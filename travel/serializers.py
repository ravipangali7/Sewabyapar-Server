"""Travel app serializers"""
import json
from django.db import transaction
from rest_framework import serializers
from travel.models import (
    TravelCommittee, TravelVehicle, TravelVehicleSeat, TravelBooking,
    TravelCommitteeStaff, TravelDealer, TravelVehicleImage
)
from shared.serializers import PlaceSerializer
from core.serializers import UserSerializer


class TravelCommitteeSerializer(serializers.ModelSerializer):
    """Travel Committee serializer"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = TravelCommittee
        fields = ['id', 'name', 'logo', 'user', 'description', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class TravelVehicleImageSerializer(serializers.ModelSerializer):
    """Travel Vehicle Image serializer"""
    class Meta:
        model = TravelVehicleImage
        fields = ['id', 'image', 'title', 'created_at']
        read_only_fields = ['id', 'created_at']


class TravelVehicleSeatSerializer(serializers.ModelSerializer):
    """Travel Vehicle Seat serializer"""
    class Meta:
        model = TravelVehicleSeat
        fields = ['id', 'side', 'number', 'status', 'floor', 'created_at']
        read_only_fields = ['id', 'created_at']


class TravelVehicleSerializer(serializers.ModelSerializer):
    """Travel Vehicle serializer"""
    from_place = PlaceSerializer(read_only=True)
    to_place = PlaceSerializer(read_only=True)
    committee = TravelCommitteeSerializer(read_only=True)
    seats = TravelVehicleSeatSerializer(many=True, read_only=True)
    images = TravelVehicleImageSerializer(many=True, read_only=True)
    seat_count = serializers.SerializerMethodField()
    
    class Meta:
        model = TravelVehicle
        fields = [
            'id', 'name', 'vehicle_no', 'committee', 'image', 'is_active',
            'from_place', 'to_place', 'departure_time', 'actual_seat_price',
            'seat_price', 'seats', 'images', 'seat_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_seat_count(self, obj):
        return obj.seats.count()


class TravelVehicleCreateUpdateSerializer(serializers.ModelSerializer):
    """Travel Vehicle create/update serializer (write-only fields)"""
    seats = TravelVehicleSeatSerializer(many=True, required=False, write_only=True)
    images = serializers.ListField(
        child=serializers.ImageField(),
        required=False,
        write_only=True,
    )
    image_titles = serializers.ListField(
        child=serializers.CharField(allow_blank=True),
        required=False,
        write_only=True,
    )
    remove_image_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        write_only=True,
    )

    class Meta:
        model = TravelVehicle
        fields = [
            'name', 'vehicle_no', 'committee', 'image', 'is_active',
            'from_place', 'to_place', 'departure_time', 'actual_seat_price',
            'seat_price', 'seats', 'images', 'image_titles', 'remove_image_ids'
        ]
    
    def validate_vehicle_no(self, value):
        qs = TravelVehicle.objects.filter(vehicle_no=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('A vehicle with this number already exists.')
        return value

    def to_internal_value(self, data):
        mutable_data = data.copy()
        for key in ('seats', 'image_titles', 'remove_image_ids'):
            raw_value = mutable_data.get(key)
            if isinstance(raw_value, str):
                try:
                    mutable_data[key] = json.loads(raw_value)
                except json.JSONDecodeError:
                    raise serializers.ValidationError({key: 'Invalid JSON format.'})
        return super().to_internal_value(mutable_data)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        seats = attrs.get('seats')
        if seats:
            seen = set()
            duplicates = []
            for seat in seats:
                key = (seat['floor'], seat['side'], seat['number'])
                if key in seen:
                    duplicates.append(f"{seat['floor']}-{seat['side']}{seat['number']}")
                seen.add(key)
            if duplicates:
                raise serializers.ValidationError({
                    'seats': f'Duplicate seats in payload: {", ".join(sorted(set(duplicates)))}'
                })
        return attrs

    def _save_vehicle_seats(self, vehicle, seats):
        if seats is None:
            return
        vehicle.seats.all().delete()
        TravelVehicleSeat.objects.bulk_create([
            TravelVehicleSeat(vehicle=vehicle, **seat) for seat in seats
        ])

    def _save_vehicle_images(self, vehicle, images, image_titles):
        if not images:
            return
        titles = image_titles or []
        TravelVehicleImage.objects.bulk_create([
            TravelVehicleImage(
                vehicle=vehicle,
                image=image,
                title=titles[index] if index < len(titles) else '',
            )
            for index, image in enumerate(images)
        ])

    @transaction.atomic
    def create(self, validated_data):
        seats = validated_data.pop('seats', None)
        images = validated_data.pop('images', [])
        image_titles = validated_data.pop('image_titles', [])
        validated_data.pop('remove_image_ids', None)
        vehicle = super().create(validated_data)
        self._save_vehicle_seats(vehicle, seats)
        self._save_vehicle_images(vehicle, images, image_titles)
        return vehicle

    @transaction.atomic
    def update(self, instance, validated_data):
        seats = validated_data.pop('seats', None)
        images = validated_data.pop('images', [])
        image_titles = validated_data.pop('image_titles', [])
        remove_image_ids = validated_data.pop('remove_image_ids', [])
        vehicle = super().update(instance, validated_data)
        if remove_image_ids:
            vehicle.images.filter(id__in=remove_image_ids).delete()
        self._save_vehicle_seats(vehicle, seats)
        self._save_vehicle_images(vehicle, images, image_titles)
        return vehicle


class SeatLayoutSerializer(serializers.Serializer):
    """Seat layout structure serializer"""
    vehicle_id = serializers.IntegerField()
    upper_floor = serializers.DictField(child=serializers.ListField(child=serializers.DictField()))
    lower_floor = serializers.DictField(child=serializers.ListField(child=serializers.DictField()))


class TravelBookingSerializer(serializers.ModelSerializer):
    """Travel Booking serializer — committee/staff (operational / payout detail)."""
    customer = UserSerializer(read_only=True)
    vehicle = TravelVehicleSerializer(read_only=True)
    vehicle_seat = TravelVehicleSeatSerializer(read_only=True)
    agent = serializers.SerializerMethodField()
    boarding_place = PlaceSerializer(read_only=True)
    
    class Meta:
        model = TravelBooking
        fields = [
            'id', 'ticket_number', 'qr_code', 'customer', 'name', 'phone', 'gender',
            'nationality', 'remarks', 'agent', 'vehicle', 'vehicle_seat', 'status',
            'booking_date', 'boarding_date', 'boarding_place', 'actual_price',
            'dealer_commission', 'agent_commission', 'system_commission',
            'commission_distributed',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'ticket_number', 'qr_code', 'created_at', 'updated_at', 'commission_distributed']
    
    def get_agent(self, obj):
        """Get agent information"""
        if obj.agent:
            return {
                'id': obj.agent.id,
                'user': {
                    'id': obj.agent.user.id,
                    'name': obj.agent.user.name,
                    'phone': obj.agent.user.phone,
                },
                'is_active': obj.agent.is_active,
            }
        return None


class TravelBookingPublicSerializer(serializers.ModelSerializer):
    """Agent, dealer, customer — no internal split fields; optional booking_revenue for this user."""
    customer = UserSerializer(read_only=True)
    vehicle = TravelVehicleSerializer(read_only=True)
    vehicle_seat = TravelVehicleSeatSerializer(read_only=True)
    agent = serializers.SerializerMethodField()
    boarding_place = PlaceSerializer(read_only=True)
    booking_revenue = serializers.SerializerMethodField()
    fare = serializers.SerializerMethodField()
    
    class Meta:
        model = TravelBooking
        fields = [
            'id', 'ticket_number', 'qr_code', 'customer', 'name', 'phone', 'gender',
            'nationality', 'remarks', 'agent', 'vehicle', 'vehicle_seat', 'status',
            'booking_date', 'boarding_date', 'boarding_place',
            'booking_revenue', 'fare',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'ticket_number', 'qr_code', 'customer', 'name', 'phone', 'gender',
            'nationality', 'remarks', 'agent', 'vehicle', 'vehicle_seat', 'status',
            'booking_date', 'boarding_date', 'boarding_place',
            'booking_revenue', 'fare',
            'created_at', 'updated_at'
        ]
    
    def get_agent(self, obj):
        if obj.agent:
            return {
                'id': obj.agent.id,
                'user': {
                    'id': obj.agent.user.id,
                    'name': obj.agent.user.name,
                    'phone': obj.agent.user.phone,
                },
                'is_active': obj.agent.is_active,
            }
        return None
    
    def get_booking_revenue(self, obj):
        """Your revenue from this booking (not commission %)."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        from travel.utils import check_user_travel_role
        roles = check_user_travel_role(request.user)
        if roles['is_agent'] and obj.agent and obj.agent.user_id == request.user.id:
            return float(obj.agent_commission)
        if roles['is_travel_dealer'] and obj.agent and obj.agent.dealer and obj.agent.dealer.user_id == request.user.id:
            return float(obj.dealer_commission)
        return None
    
    def get_fare(self, obj):
        if obj.vehicle:
            return float(obj.vehicle.seat_price)
        return None


def _use_internal_booking_serializer(request):
    from travel.utils import check_user_travel_role
    roles = check_user_travel_role(request.user)
    return roles['is_travel_committee'] or roles['is_travel_staff']


def serialize_booking(booking, request):
    if _use_internal_booking_serializer(request):
        return TravelBookingSerializer(booking, context={'request': request}).data
    return TravelBookingPublicSerializer(booking, context={'request': request}).data


def serialize_bookings(bookings, request):
    if _use_internal_booking_serializer(request):
        return TravelBookingSerializer(bookings, many=True, context={'request': request}).data
    return TravelBookingPublicSerializer(bookings, many=True, context={'request': request}).data


class TravelBookingCreateSerializer(serializers.ModelSerializer):
    """Travel Booking create serializer"""
    seat_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        help_text='List of seat IDs to book'
    )
    booking_date = serializers.DateTimeField()
    
    class Meta:
        model = TravelBooking
        fields = [
            'name', 'phone', 'gender', 'nationality', 'remarks',
            'vehicle', 'seat_ids', 'booking_date', 'customer'
        ]
    
    def validate(self, data):
        """Validate booking data"""
        from travel.utils import validate_booking_date
        
        vehicle = data.get('vehicle')
        booking_date = data.get('booking_date')
        seat_ids = data.get('seat_ids', [])
        
        if not vehicle:
            raise serializers.ValidationError("Vehicle is required")
        
        if not seat_ids:
            raise serializers.ValidationError("At least one seat must be selected")
        
        # Validate date
        is_valid, error = validate_booking_date(vehicle, booking_date)
        if not is_valid:
            raise serializers.ValidationError(error)
        
        # Validate seats belong to vehicle and are available
        seats = TravelVehicleSeat.objects.filter(
            id__in=seat_ids,
            vehicle=vehicle,
            status='available'
        )
        
        if seats.count() != len(seat_ids):
            raise serializers.ValidationError("Some selected seats are not available")
        
        return data


class TravelBookingUpdateSerializer(serializers.ModelSerializer):
    """Travel Booking update serializer - status and optional fields for committee"""
    class Meta:
        model = TravelBooking
        fields = ['status', 'name', 'phone', 'remarks']
    
    def validate_status(self, value):
        allowed = {'pending', 'booked', 'boarded', 'cancelled'}
        if value not in allowed:
            raise serializers.ValidationError(
                f'Status must be one of: {", ".join(allowed)}'
            )
        return value
    
    def update(self, instance, validated_data):
        new_status = validated_data.get('status', instance.status)
        if new_status == 'cancelled' and instance.status != 'cancelled':
            if instance.status == 'boarded':
                raise serializers.ValidationError('Cannot cancel a boarded ticket.')
            seat = instance.vehicle_seat
            if seat.status == 'booked':
                seat.status = 'available'
                seat.save()
        return super().update(instance, validated_data)


class TravelCommitteeStaffSerializer(serializers.ModelSerializer):
    """Travel Committee Staff serializer"""
    user = UserSerializer(read_only=True)
    travel_committee = TravelCommitteeSerializer(read_only=True)
    
    class Meta:
        model = TravelCommitteeStaff
        fields = [
            'id', 'user', 'travel_committee', 'booking_permission',
            'boarding_permission', 'finance_permission', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TravelCommitteeStaffWriteSerializer(serializers.ModelSerializer):
    """Travel Committee Staff create/update serializer"""
    class Meta:
        model = TravelCommitteeStaff
        fields = [
            'user', 'travel_committee', 'booking_permission',
            'boarding_permission', 'finance_permission'
        ]


class TravelDealerSerializer(serializers.ModelSerializer):
    """Travel Dealer serializer"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = TravelDealer
        fields = [
            'id', 'user', 'commission_type', 'commission_value',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

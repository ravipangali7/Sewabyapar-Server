"""Travel app serializers"""
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
    
    class Meta:
        model = TravelVehicle
        fields = [
            'id', 'name', 'vehicle_no', 'committee', 'image', 'is_active',
            'from_place', 'to_place', 'departure_time', 'actual_seat_price',
            'seat_price', 'seats', 'images', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TravelVehicleCreateUpdateSerializer(serializers.ModelSerializer):
    """Travel Vehicle create/update serializer (write-only fields)"""
    class Meta:
        model = TravelVehicle
        fields = [
            'name', 'vehicle_no', 'committee', 'image', 'is_active',
            'from_place', 'to_place', 'departure_time', 'actual_seat_price',
            'seat_price'
        ]
    
    def validate_vehicle_no(self, value):
        qs = TravelVehicle.objects.filter(vehicle_no=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('A vehicle with this number already exists.')
        return value


class SeatLayoutSerializer(serializers.Serializer):
    """Seat layout structure serializer"""
    vehicle_id = serializers.IntegerField()
    upper_floor = serializers.DictField(child=serializers.ListField(child=serializers.DictField()))
    lower_floor = serializers.DictField(child=serializers.ListField(child=serializers.DictField()))


class TravelBookingSerializer(serializers.ModelSerializer):
    """Travel Booking serializer"""
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
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'ticket_number', 'qr_code', 'created_at', 'updated_at']
    
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
        allowed = {'pending', 'booked', 'boarded'}
        if value not in allowed:
            raise serializers.ValidationError(
                f'Status must be one of: {", ".join(allowed)}'
            )
        return value


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


class RevenueHistorySerializer(serializers.Serializer):
    """Revenue history serializer based on transactions"""
    id = serializers.IntegerField()
    transaction_type = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    status = serializers.CharField()
    description = serializers.CharField()
    booking = TravelBookingSerializer(read_only=True, source='related_travel_booking')
    created_at = serializers.DateTimeField()

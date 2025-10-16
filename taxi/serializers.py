from rest_framework import serializers
from .models import Driver, Vehicle, Trip, Seater, TaxiBooking
from core.serializers import UserSerializer
from shared.serializers import PlaceSerializer


class DriverSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Driver
        fields = ['id', 'user', 'license', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class VehicleSerializer(serializers.ModelSerializer):
    driver = DriverSerializer(read_only=True)
    image = serializers.SerializerMethodField()
    
    class Meta:
        model = Vehicle
        fields = ['id', 'name', 'vehicle_no', 'image', 'driver', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def get_image(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class TripSerializer(serializers.ModelSerializer):
    from_place = PlaceSerializer(read_only=True)
    to_place = PlaceSerializer(read_only=True)
    
    class Meta:
        model = Trip
        fields = ['id', 'from_place', 'to_place']
        read_only_fields = ['id']


class SeaterSerializer(serializers.ModelSerializer):
    trip = TripSerializer(read_only=True)
    
    class Meta:
        model = Seater
        fields = ['id', 'seat', 'price', 'trip']
        read_only_fields = ['id']


class TaxiBookingSerializer(serializers.ModelSerializer):
    customer = UserSerializer(read_only=True)
    trip = TripSerializer(read_only=True)
    seater = SeaterSerializer(read_only=True)
    vehicle = VehicleSerializer(read_only=True)
    
    class Meta:
        model = TaxiBooking
        fields = ['id', 'customer', 'trip', 'seater', 'price', 'date', 'time', 
                 'payment_status', 'vehicle', 'trip_status', 'remarks', 'created_at']
        read_only_fields = ['id', 'created_at']


# Create/Update serializers
class DriverCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = ['user', 'license', 'is_active']


class VehicleCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ['name', 'vehicle_no', 'image', 'driver', 'is_active']


class TripCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trip
        fields = ['from_place', 'to_place']


class SeaterCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seater
        fields = ['seat', 'price', 'trip']


class TaxiBookingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxiBooking
        fields = ['id', 'trip', 'seater', 'date', 'time', 'payment_status', 
                 'trip_status', 'remarks']
        read_only_fields = ['id']
    
    def create(self, validated_data):
        from .models import Vehicle
        
        # Auto-set customer from request context
        request = self.context.get('request')
        if not request or not hasattr(request, 'user'):
            raise serializers.ValidationError({
                'customer': 'Authentication required'
            })
        validated_data['customer'] = request.user
        
        # Auto-calculate price from seater
        seater = validated_data.get('seater')
        if not seater:
            raise serializers.ValidationError({
                'seater': 'Seater is required'
            })
        validated_data['price'] = seater.price
        
        # Check vehicle availability for the selected date
        selected_date = validated_data.get('date')
        
        if not selected_date:
            raise serializers.ValidationError({
                'date': 'Date is required'
            })
        
        # Get all active vehicles
        all_vehicles = Vehicle.objects.filter(is_active=True)
        total_vehicles = all_vehicles.count()
        
        if total_vehicles == 0:
            raise serializers.ValidationError({
                'error': 'No vehicles available in the system'
            })
        
        # Count all bookings except cancelled ones (pending, confirmed, ongoing, completed)
        active_bookings_count = TaxiBooking.objects.filter(
            date=selected_date
        ).exclude(
            trip_status='cancelled'
        ).count()
        
        # If all vehicle slots are taken, raise validation error
        if active_bookings_count >= total_vehicles:
            raise serializers.ValidationError({
                'error': f'All vehicles are booked for {selected_date}. Please choose a different date.'
            })
        
        # Proceed with booking creation
        return super().create(validated_data)

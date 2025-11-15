from django.db import models
from django.core.validators import MinValueValidator
from core.models import User
from shared.models import Place


class Driver(models.Model):
    """Driver model for taxi drivers"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='driver_profile')
    license = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.name} - {self.license}"
    
    class Meta:
        ordering = ['-created_at']


class Vehicle(models.Model):
    """Vehicle model for taxi vehicles"""
    name = models.CharField(max_length=100)
    vehicle_no = models.CharField(max_length=20, unique=True)
    image = models.ImageField(upload_to='vehicles/', blank=True, null=True)
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='vehicles')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.vehicle_no}"
    
    class Meta:
        ordering = ['-created_at']


class Trip(models.Model):
    """Trip model for taxi routes"""
    from_place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='trips_from')
    to_place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='trips_to')
    
    def __str__(self):
        return f"{self.from_place.name} to {self.to_place.name}"
    
    class Meta:
        ordering = ['from_place__name', 'to_place__name']


class Seater(models.Model):
    """Seater model for different seat types and prices"""
    seat = models.CharField(max_length=50)  # e.g., "Front Seat", "Back Seat", "Window Seat"
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='seaters')
    
    def __str__(self):
        return f"{self.trip} - {self.seat} (₹{self.price})"
    
    class Meta:
        ordering = ['trip', 'price']


class TaxiBooking(models.Model):
    """Taxi booking model"""
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('refunded', 'Refunded'),
    ]
    
    TRIP_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='taxi_bookings')
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='bookings')
    seater = models.ForeignKey(Seater, on_delete=models.CASCADE, related_name='bookings')
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    date = models.DateField()
    time = models.TimeField()
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='bookings', null=True, blank=True)
    trip_status = models.CharField(max_length=20, choices=TRIP_STATUS_CHOICES, default='pending')
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Booking {self.id} - {self.customer.name} ({self.trip})"
    
    class Meta:
        ordering = ['-created_at']
from django.db import models
from django.core.validators import MinValueValidator
from core.models import User
from shared.models import Place


class TravelCommittee(models.Model):
    """Travel Committee model"""
    name = models.CharField(max_length=200)
    logo = models.ImageField(upload_to='travel_committees/logos/', blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='travel_committees')
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Travel Committee'
        verbose_name_plural = 'Travel Committees'


class TravelVehicle(models.Model):
    """Travel Vehicle model"""
    name = models.CharField(max_length=200)
    vehicle_no = models.CharField(max_length=50, unique=True)
    committee = models.ForeignKey(TravelCommittee, on_delete=models.CASCADE, related_name='vehicles')
    image = models.ImageField(upload_to='travel_vehicles/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    from_place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='vehicles_from')
    to_place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='vehicles_to')
    departure_time = models.TimeField()
    actual_seat_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    seat_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.vehicle_no})"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Travel Vehicle'
        verbose_name_plural = 'Travel Vehicles'


class TravelVehicleImage(models.Model):
    """Travel Vehicle Image model"""
    image = models.ImageField(upload_to='travel_vehicles/images/')
    vehicle = models.ForeignKey(TravelVehicle, on_delete=models.CASCADE, related_name='images')
    title = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.vehicle.name} - {self.title or 'Image'}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Travel Vehicle Image'
        verbose_name_plural = 'Travel Vehicle Images'


class TravelVehicleSeat(models.Model):
    """Travel Vehicle Seat model"""
    SIDE_CHOICES = [
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
    ]
    
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('booked', 'Booked'),
        ('boarded', 'Boarded'),
    ]
    
    FLOOR_CHOICES = [
        ('upper', 'Upper'),
        ('lower', 'Lower'),
    ]
    
    vehicle = models.ForeignKey(TravelVehicle, on_delete=models.CASCADE, related_name='seats')
    side = models.CharField(max_length=1, choices=SIDE_CHOICES)
    number = models.IntegerField(validators=[MinValueValidator(1)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    floor = models.CharField(max_length=10, choices=FLOOR_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.vehicle.name} - {self.side}{self.number} ({self.floor})"
    
    class Meta:
        ordering = ['vehicle', 'floor', 'side', 'number']
        unique_together = ['vehicle', 'side', 'number', 'floor']
        verbose_name = 'Travel Vehicle Seat'
        verbose_name_plural = 'Travel Vehicle Seats'


class TravelCommitteeStaff(models.Model):
    """Travel Committee Staff model"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='travel_committee_staff')
    travel_committee = models.ForeignKey(TravelCommittee, on_delete=models.CASCADE, related_name='staff')
    booking_permission = models.BooleanField(default=False)
    boarding_permission = models.BooleanField(default=False)
    finance_permission = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.name} - {self.travel_committee.name}"
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'travel_committee']
        verbose_name = 'Travel Committee Staff'
        verbose_name_plural = 'Travel Committee Staff'


class TravelDealer(models.Model):
    """Travel Dealer model"""
    COMMISSION_TYPE_CHOICES = [
        ('flat', 'Flat'),
        ('percentage', 'Percentage'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='travel_dealers')
    commission_type = models.CharField(max_length=20, choices=COMMISSION_TYPE_CHOICES, default='percentage')
    commission_value = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.name} - {self.get_commission_type_display()}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Travel Dealer'
        verbose_name_plural = 'Travel Dealers'


class TravelBooking(models.Model):
    """Travel Booking model"""
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('booked', 'Booked'),
        ('boarded', 'Boarded'),
    ]
    
    ticket_number = models.CharField(max_length=50, unique=True, blank=True, null=True)
    qr_code = models.TextField(blank=True, null=True, help_text='QR code data for ticket scanning')
    customer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='travel_bookings')
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    nationality = models.CharField(max_length=100, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    agent = models.ForeignKey('core.Agent', on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings')
    vehicle = models.ForeignKey(TravelVehicle, on_delete=models.CASCADE, related_name='bookings')
    vehicle_seat = models.ForeignKey(TravelVehicleSeat, on_delete=models.CASCADE, related_name='bookings')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    booking_date = models.DateTimeField()
    boarding_date = models.DateTimeField(blank=True, null=True)
    boarding_place = models.ForeignKey(Place, on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings')
    actual_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    dealer_commission = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    agent_commission = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    system_commission = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def generate_ticket_number(self):
        """Generate unique ticket number"""
        import uuid
        from datetime import datetime
        if not self.ticket_number:
            timestamp = datetime.now().strftime('%Y%m%d')
            unique_id = str(uuid.uuid4())[:8].upper()
            self.ticket_number = f"TRV-{timestamp}-{unique_id}"
        return self.ticket_number
    
    def generate_qr_code(self):
        """Generate QR code data for ticket"""
        if not self.ticket_number:
            self.generate_ticket_number()
        self.qr_code = self.ticket_number
        return self.qr_code
    
    def calculate_commissions(self):
        """Calculate all commission amounts"""
        from decimal import Decimal
        if not self.vehicle:
            return
        
        # System commission
        self.system_commission = Decimal(str(self.vehicle.seat_price)) - Decimal(str(self.vehicle.actual_seat_price))
        
        # Dealer commission
        if self.agent and self.agent.dealer:
            dealer = self.agent.dealer
            if dealer.commission_type == 'flat':
                self.dealer_commission = Decimal(str(dealer.commission_value))
            else:  # percentage
                self.dealer_commission = self.system_commission * (Decimal(str(dealer.commission_value)) / Decimal('100'))
        else:
            self.dealer_commission = Decimal('0')
        
        # Agent commission
        if self.agent:
            if self.agent.commission_type == 'flat':
                self.agent_commission = Decimal(str(self.agent.commission_value))
            else:  # percentage
                self.agent_commission = self.system_commission * (Decimal(str(self.agent.commission_value)) / Decimal('100'))
        else:
            self.agent_commission = Decimal('0')
    
    def __str__(self):
        return f"{self.ticket_number or 'N/A'} - {self.name}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Travel Booking'
        verbose_name_plural = 'Travel Bookings'
        indexes = [
            models.Index(fields=['ticket_number']),
            models.Index(fields=['status', '-created_at']),
        ]
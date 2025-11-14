from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.contrib import messages
from django.utils.dateparse import parse_date, parse_time
import json
from taxi.models import TaxiBooking, Trip, Seater, Vehicle
from taxi.serializers import TaxiBookingCreateSerializer
from shared.models import Place
from website.models import MySetting, CMSPages


@login_required
def new_booking_view(request):
    """New taxi booking page with POST handling for booking creation"""
    try:
        settings = MySetting.objects.first()
    except MySetting.DoesNotExist:
        settings = None
    
    menu_pages = CMSPages.objects.filter(on_menu=True)
    footer_pages = CMSPages.objects.filter(on_footer=True)
    
    # Handle POST request - create booking
    if request.method == 'POST':
        try:
            # Get form data
            from_place_id = request.POST.get('from_place')
            to_place_id = request.POST.get('to_place')
            seater_id = request.POST.get('seater')
            date_str = request.POST.get('date')
            time_str = request.POST.get('time')
            remarks = request.POST.get('remarks', '').strip()
            
            # Validate required fields
            if not all([from_place_id, to_place_id, seater_id, date_str, time_str]):
                messages.error(request, 'Please fill in all required fields.')
                return redirect('website:new_taxi_booking')
            
            # Find the trip based on from_place and to_place
            try:
                trip = Trip.objects.get(from_place_id=from_place_id, to_place_id=to_place_id)
            except Trip.DoesNotExist:
                messages.error(request, 'Invalid route selected. Please select valid From and To places.')
                return redirect('website:new_taxi_booking')
            
            # Get seater
            try:
                seater = Seater.objects.get(id=seater_id, trip=trip)
            except Seater.DoesNotExist:
                messages.error(request, 'Invalid seater selected. Please select a valid seater type.')
                return redirect('website:new_taxi_booking')
            
            # Parse date and time
            try:
                booking_date = parse_date(date_str)
                booking_time = parse_time(time_str)
                if not booking_date or not booking_time:
                    raise ValueError("Invalid date or time format")
            except (ValueError, TypeError):
                messages.error(request, 'Invalid date or time format. Please select valid date and time.')
                return redirect('website:new_taxi_booking')
            
            # Prepare data for serializer
            booking_data = {
                'trip': trip.id,
                'seater': seater.id,
                'date': booking_date,
                'time': booking_time,
                'remarks': remarks if remarks else None,
                'payment_status': 'pending',
                'trip_status': 'pending',
            }
            
            # Create booking using serializer (handles validation and vehicle availability)
            serializer = TaxiBookingCreateSerializer(data=booking_data, context={'request': request})
            
            if serializer.is_valid():
                booking = serializer.save()
                messages.success(request, f'Taxi booking created successfully! Booking ID: {booking.id}')
                return redirect('website:taxi_booking_detail', booking_id=booking.id)
            else:
                # Handle serializer validation errors
                error_messages = []
                for field, errors in serializer.errors.items():
                    if isinstance(errors, list):
                        error_messages.extend([f"{field}: {error}" for error in errors])
                    else:
                        error_messages.append(f"{field}: {errors}")
                
                if error_messages:
                    messages.error(request, ' '.join(error_messages))
                else:
                    messages.error(request, 'Failed to create booking. Please try again.')
                
                return redirect('website:new_taxi_booking')
                
        except Exception as e:
            messages.error(request, f'An error occurred while creating the booking: {str(e)}')
            return redirect('website:new_taxi_booking')
    
    # GET request - display form
    trips = Trip.objects.all()
    
    # Filter "From Place" options to only show places used in trips as from_place
    from_places = Place.objects.filter(trips_from__isnull=False).distinct().order_by('name')
    
    # Get all places for JavaScript filtering of "To Place" options
    all_places = Place.objects.all().order_by('name')
    places_data = [{'id': p.id, 'name': p.name} for p in all_places]
    
    # Get trip from URL parameter if provided
    selected_trip = None
    trip_id = request.GET.get('trip')
    if trip_id:
        try:
            selected_trip = Trip.objects.get(id=trip_id)
        except Trip.DoesNotExist:
            pass
    
    # Get all trips with their seaters for JavaScript
    trips_data = []
    for trip in trips:
        seaters = trip.seaters.all()
        trips_data.append({
            'id': trip.id,
            'from_place_id': trip.from_place.id,
            'to_place_id': trip.to_place.id,
            'from_place_name': trip.from_place.name,
            'to_place_name': trip.to_place.name,
            'seaters': [{'id': s.id, 'seat': s.seat, 'price': float(s.price)} for s in seaters]
        })
    
    # Convert to JSON string for template
    trips_data_json = json.dumps(trips_data)
    places_data_json = json.dumps(places_data)
    
    context = {
        'settings': settings,
        'menu_pages': menu_pages,
        'footer_pages': footer_pages,
        'from_places': from_places,
        'trips': trips,
        'selected_trip': selected_trip,
        'trips_data_json': trips_data_json,
        'places_data_json': places_data_json,
    }
    
    return render(request, 'website/taxi/new_booking.html', context)


@login_required
def my_bookings_view(request):
    """User's taxi bookings list"""
    try:
        settings = MySetting.objects.first()
    except MySetting.DoesNotExist:
        settings = None
    
    menu_pages = CMSPages.objects.filter(on_menu=True)
    footer_pages = CMSPages.objects.filter(on_footer=True)
    
    bookings = TaxiBooking.objects.filter(customer=request.user).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(bookings, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'settings': settings,
        'menu_pages': menu_pages,
        'footer_pages': footer_pages,
        'bookings': page_obj,
    }
    
    return render(request, 'website/taxi/my_bookings.html', context)


@login_required
def booking_detail_view(request, booking_id):
    """Taxi booking detail page"""
    try:
        settings = MySetting.objects.first()
    except MySetting.DoesNotExist:
        settings = None
    
    menu_pages = CMSPages.objects.filter(on_menu=True)
    footer_pages = CMSPages.objects.filter(on_footer=True)
    
    booking = get_object_or_404(TaxiBooking, id=booking_id, customer=request.user)
    
    context = {
        'settings': settings,
        'menu_pages': menu_pages,
        'footer_pages': footer_pages,
        'booking': booking,
    }
    
    return render(request, 'website/taxi/booking_detail.html', context)


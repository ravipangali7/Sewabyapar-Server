from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from ecommerce.models import Order, Wishlist
from taxi.models import TaxiBooking
from core.models import Address
from core.utils.role_helpers import get_user_primary_role, is_travel_role
from website.models import MySetting, CMSPages


@login_required
def profile_view(request):
    """User profile page"""
    if is_travel_role(get_user_primary_role(request.user)):
        return redirect('website:travel_profile')

    try:
        settings = MySetting.objects.first()
    except MySetting.DoesNotExist:
        settings = None
    
    menu_pages = CMSPages.objects.filter(on_menu=True)
    footer_pages = CMSPages.objects.filter(on_footer=True)
    
    # Get user stats
    orders_count = Order.objects.filter(user=request.user).count()
    wishlist_count = Wishlist.objects.filter(user=request.user).count()
    bookings_count = TaxiBooking.objects.filter(customer=request.user).count()
    addresses_count = Address.objects.filter(user=request.user).count()
    
    # Recent orders
    recent_orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    context = {
        'settings': settings,
        'menu_pages': menu_pages,
        'footer_pages': footer_pages,
        'user': request.user,
        'orders_count': orders_count,
        'wishlist_count': wishlist_count,
        'bookings_count': bookings_count,
        'addresses_count': addresses_count,
        'recent_orders': recent_orders,
    }
    
    return render(request, 'website/profile/profile.html', context)


@login_required
def travel_profile_view(request):
    """Travel user profile page."""
    if not is_travel_role(get_user_primary_role(request.user)):
        return redirect('website:profile')

    try:
        settings = MySetting.objects.first()
    except MySetting.DoesNotExist:
        settings = None
    
    menu_pages = CMSPages.objects.filter(on_menu=True)
    footer_pages = CMSPages.objects.filter(on_footer=True)
    
    # Get user stats
    orders_count = Order.objects.filter(user=request.user).count()
    wishlist_count = Wishlist.objects.filter(user=request.user).count()
    bookings_count = TaxiBooking.objects.filter(customer=request.user).count()
    addresses_count = Address.objects.filter(user=request.user).count()
    
    # Recent orders
    recent_orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    context = {
        'settings': settings,
        'menu_pages': menu_pages,
        'footer_pages': footer_pages,
        'user': request.user,
        'orders_count': orders_count,
        'wishlist_count': wishlist_count,
        'bookings_count': bookings_count,
        'addresses_count': addresses_count,
        'recent_orders': recent_orders,
    }
    
    return render(request, 'website/profile/profile.html', context)


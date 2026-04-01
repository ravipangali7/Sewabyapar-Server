from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from ..models import MySetting, Services, CMSPages
from ecommerce.models import Product, Category, Store, Order, OrderItem
from taxi.models import TaxiBooking
from website.decorators import travel_role_required
from core.utils.role_helpers import get_user_primary_role, get_dashboard_path_for_user


def home_view(request):
    """Homepage view - single page website"""
    # If user is authenticated, redirect to dashboard
    if request.user.is_authenticated:
        return redirect(get_dashboard_path_for_user(request.user))
    
    try:
        settings = MySetting.objects.first()
    except MySetting.DoesNotExist:
        settings = None
    
    services = Services.objects.all()
    menu_pages = CMSPages.objects.filter(on_menu=True)
    footer_pages = CMSPages.objects.filter(on_footer=True)
    
    context = {
        'settings': settings,
        'services': services,
        'menu_pages': menu_pages,
        'footer_pages': footer_pages,
    }
    
    return render(request, 'website/home.html', context)


def cms_page_view(request, slug):
    """Dynamic CMS page view"""
    page = get_object_or_404(CMSPages, slug=slug)
    
    try:
        settings = MySetting.objects.first()
    except MySetting.DoesNotExist:
        settings = None
    
    menu_pages = CMSPages.objects.filter(on_menu=True)
    footer_pages = CMSPages.objects.filter(on_footer=True)
    
    context = {
        'page': page,
        'settings': settings,
        'menu_pages': menu_pages,
        'footer_pages': footer_pages,
    }
    
    return render(request, 'website/cms_page.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def contact_form_view(request):
    """Handle contact form submission"""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()
        
        # Basic validation
        if not all([name, email, subject, message]):
            return JsonResponse({
                'success': False,
                'message': 'All fields are required.'
            })
        
        # Here you could save to database, send email, etc.
        # For now, just return success
        return JsonResponse({
            'success': True,
            'message': 'Thank you for your message. We will get back to you soon!'
        })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method.'
    })


@login_required
def dashboard_view(request):
    """Dashboard view for logged-in users"""
    if get_user_primary_role(request.user) != 'customer':
        return redirect(get_dashboard_path_for_user(request.user))

    try:
        settings = MySetting.objects.first()
    except MySetting.DoesNotExist:
        settings = None
    
    menu_pages = CMSPages.objects.filter(on_menu=True)
    footer_pages = CMSPages.objects.filter(on_footer=True)
    
    # Featured products
    featured_products = Product.objects.filter(is_active=True, is_featured=True).select_related('store', 'category').prefetch_related('images')[:8]
    
    # Pending orders
    pending_orders = Order.objects.filter(
        user=request.user,
        status__in=['pending', 'confirmed', 'processing']
    ).order_by('-created_at')[:5]
    
    # Top selling products (aggregate from OrderItem)
    top_selling_products = Product.objects.filter(
        is_active=True
    ).annotate(
        total_sold=Sum('orderitem__quantity', filter=Q(orderitem__order__status__in=['confirmed', 'processing', 'shipped', 'delivered']))
    ).filter(
        total_sold__gt=0
    ).order_by('-total_sold')[:8]
    
    # Categories with products
    categories = Category.objects.filter(is_active=True, parent=None)[:6]
    category_data = []
    for category in categories:
        products = Product.objects.filter(
            category=category,
            is_active=True
        ).select_related('store').prefetch_related('images')[:4]
        if products.exists():
            category_data.append({
                'category': category,
                'products': products
            })
    
    # Active stores
    stores = Store.objects.filter(is_active=True)[:6]
    
    # Pending taxi booking
    pending_taxi_booking = TaxiBooking.objects.filter(
        customer=request.user,
        trip_status__in=['pending', 'confirmed', 'ongoing']
    ).select_related('trip', 'trip__from_place', 'trip__to_place').first()
    
    context = {
        'settings': settings,
        'menu_pages': menu_pages,
        'footer_pages': footer_pages,
        'featured_products': featured_products,
        'pending_orders': pending_orders,
        'top_selling_products': top_selling_products,
        'category_data': category_data,
        'stores': stores,
        'pending_taxi_booking': pending_taxi_booking,
    }
    
    return render(request, 'website/dashboard.html', context)


def _base_website_context():
    settings = MySetting.objects.first()
    return {
        "settings": settings,
        "menu_pages": CMSPages.objects.filter(on_menu=True),
        "footer_pages": CMSPages.objects.filter(on_footer=True),
    }


@travel_role_required("travel_committee")
def travel_committee_view(request):
    context = _base_website_context()
    context.update(
        {
            "travel_role": "travel_committee",
            "travel_title": "Travel Committee Dashboard",
            "api_base": "/api/travel",
        }
    )
    return render(request, "website/travel/dashboard.html", context)


@travel_role_required("travel_staff")
def travel_committee_staff_view(request):
    context = _base_website_context()
    context.update(
        {
            "travel_role": "travel_staff",
            "travel_title": "Travel Committee Staff Dashboard",
            "api_base": "/api/travel",
        }
    )
    return render(request, "website/travel/dashboard.html", context)


@travel_role_required("travel_dealer")
def travel_dealer_view(request):
    context = _base_website_context()
    context.update(
        {
            "travel_role": "travel_dealer",
            "travel_title": "Travel Dealer Dashboard",
            "api_base": "/api/travel",
        }
    )
    return render(request, "website/travel/dashboard.html", context)


@travel_role_required("agent")
def travel_agent_view(request):
    context = _base_website_context()
    context.update(
        {
            "travel_role": "agent",
            "travel_title": "Agent Dashboard",
            "api_base": "/api/travel",
        }
    )
    return render(request, "website/travel/dashboard.html", context)


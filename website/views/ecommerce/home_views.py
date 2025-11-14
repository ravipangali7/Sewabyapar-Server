from django.shortcuts import render
from django.db.models import Q
from ecommerce.models import Product, Category, Store
from website.models import MySetting, CMSPages


def shop_view(request):
    """Shop/Home page with featured products"""
    try:
        settings = MySetting.objects.first()
    except MySetting.DoesNotExist:
        settings = None
    
    menu_pages = CMSPages.objects.filter(on_menu=True)
    footer_pages = CMSPages.objects.filter(on_footer=True)
    
    # Get featured products
    featured_products = Product.objects.filter(is_active=True, is_featured=True)[:8]
    
    # Get categories
    categories = Category.objects.filter(is_active=True, parent=None)[:6]
    
    # Get recent products
    recent_products = Product.objects.filter(is_active=True)[:8]
    
    context = {
        'settings': settings,
        'menu_pages': menu_pages,
        'footer_pages': footer_pages,
        'featured_products': featured_products,
        'categories': categories,
        'recent_products': recent_products,
    }
    
    return render(request, 'website/ecommerce/shop.html', context)


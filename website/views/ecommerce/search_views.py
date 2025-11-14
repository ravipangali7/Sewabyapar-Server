from django.shortcuts import render
from django.db.models import Q
from django.core.paginator import Paginator
from ecommerce.models import Product
from website.models import MySetting, CMSPages


def search_view(request):
    """Product search page"""
    try:
        settings = MySetting.objects.first()
    except MySetting.DoesNotExist:
        settings = None
    
    menu_pages = CMSPages.objects.filter(on_menu=True)
    footer_pages = CMSPages.objects.filter(on_footer=True)
    
    query = request.GET.get('q', '').strip()
    products = Product.objects.filter(is_active=True)
    
    if query:
        products = products.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) |
            Q(category__name__icontains=query) |
            Q(store__name__icontains=query)
        )
    else:
        products = products.none()
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'settings': settings,
        'menu_pages': menu_pages,
        'footer_pages': footer_pages,
        'products': page_obj,
        'query': query,
    }
    
    return render(request, 'website/ecommerce/search.html', context)


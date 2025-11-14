from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from ecommerce.models import Order
from website.models import MySetting, CMSPages


@login_required
def orders_view(request):
    """Orders list page"""
    try:
        settings = MySetting.objects.first()
    except MySetting.DoesNotExist:
        settings = None
    
    menu_pages = CMSPages.objects.filter(on_menu=True)
    footer_pages = CMSPages.objects.filter(on_footer=True)
    
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'settings': settings,
        'menu_pages': menu_pages,
        'footer_pages': footer_pages,
        'orders': page_obj,
    }
    
    return render(request, 'website/ecommerce/orders.html', context)


@login_required
def order_detail_view(request, order_id):
    """Order detail page"""
    try:
        settings = MySetting.objects.first()
    except MySetting.DoesNotExist:
        settings = None
    
    menu_pages = CMSPages.objects.filter(on_menu=True)
    footer_pages = CMSPages.objects.filter(on_footer=True)
    
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = order.items.all().select_related('product', 'store')
    
    context = {
        'settings': settings,
        'menu_pages': menu_pages,
        'footer_pages': footer_pages,
        'order': order,
        'order_items': order_items,
    }
    
    return render(request, 'website/ecommerce/order_detail.html', context)


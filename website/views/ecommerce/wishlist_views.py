from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from ecommerce.models import Wishlist, Product
from website.models import MySetting, CMSPages


@login_required
def wishlist_view(request):
    """Wishlist page with POST handling for add/remove"""
    try:
        settings = MySetting.objects.first()
    except MySetting.DoesNotExist:
        settings = None
    
    menu_pages = CMSPages.objects.filter(on_menu=True)
    footer_pages = CMSPages.objects.filter(on_footer=True)
    
    # Handle POST requests
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        action = request.POST.get('action', 'toggle')
        
        if product_id:
            try:
                product = Product.objects.get(id=product_id, is_active=True)
                wishlist_item = Wishlist.objects.filter(user=request.user, product=product).first()
                
                if action == 'remove' or wishlist_item:
                    # Remove from wishlist
                    if wishlist_item:
                        wishlist_item.delete()
                        messages.success(request, f'{product.name} removed from wishlist')
                else:
                    # Add to wishlist
                    Wishlist.objects.create(user=request.user, product=product)
                    messages.success(request, f'{product.name} added to wishlist')
                
                # Redirect back to product page if coming from there
                referer = request.META.get('HTTP_REFERER', '')
                if 'product' in referer:
                    return redirect('website:product_detail', product_id=product_id)
                return redirect('website:wishlist')
            except Product.DoesNotExist:
                messages.error(request, 'Product not found')
                return redirect('website:wishlist')
    
    # GET request - display wishlist
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')
    
    # Pagination
    paginator = Paginator(wishlist_items, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'settings': settings,
        'menu_pages': menu_pages,
        'footer_pages': footer_pages,
        'wishlist_items': page_obj,
    }
    
    return render(request, 'website/ecommerce/wishlist.html', context)


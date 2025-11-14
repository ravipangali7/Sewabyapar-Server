from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from ecommerce.models import Cart, Product
from website.models import MySetting, CMSPages


@login_required
def cart_view(request):
    """Shopping cart page with POST handling for add/update/remove"""
    try:
        settings = MySetting.objects.first()
    except MySetting.DoesNotExist:
        settings = None
    
    menu_pages = CMSPages.objects.filter(on_menu=True)
    footer_pages = CMSPages.objects.filter(on_footer=True)
    
    # Handle POST requests
    if request.method == 'POST':
        # Add product to cart (from product detail page)
        if 'product_id' in request.POST:
            product_id = request.POST.get('product_id')
            quantity = int(request.POST.get('quantity', 1))
            
            try:
                product = Product.objects.get(id=product_id, is_active=True)
                cart_item, created = Cart.objects.get_or_create(
                    user=request.user,
                    product=product,
                    defaults={'quantity': quantity}
                )
                if not created:
                    cart_item.quantity += quantity
                    if cart_item.quantity > product.stock_quantity:
                        cart_item.quantity = product.stock_quantity
                    cart_item.save()
                    messages.success(request, f'Updated quantity for {product.name}')
                else:
                    messages.success(request, f'{product.name} added to cart')
                
                # Redirect back to product page if coming from there
                referer = request.META.get('HTTP_REFERER', '')
                if 'product' in referer:
                    return redirect('website:product_detail', product_id=product_id)
                return redirect('website:cart')
            except Product.DoesNotExist:
                messages.error(request, 'Product not found')
                return redirect('website:cart')
        
        # Update or remove cart item
        item_id = request.POST.get('item_id')
        action = request.POST.get('action')
        
        if item_id and action:
            try:
                cart_item = Cart.objects.get(id=item_id, user=request.user)
                
                if action == 'update':
                    quantity = int(request.POST.get('quantity', 1))
                    if quantity > 0 and quantity <= cart_item.product.stock_quantity:
                        cart_item.quantity = quantity
                        cart_item.save()
                        messages.success(request, 'Cart updated successfully')
                    else:
                        messages.error(request, f'Invalid quantity. Max available: {cart_item.product.stock_quantity}')
                elif action == 'remove':
                    product_name = cart_item.product.name
                    cart_item.delete()
                    messages.success(request, f'{product_name} removed from cart')
                
                return redirect('website:cart')
            except Cart.DoesNotExist:
                messages.error(request, 'Cart item not found')
                return redirect('website:cart')
    
    # GET request - display cart
    cart_items = Cart.objects.filter(user=request.user).select_related('product')
    
    # Calculate totals for each item and overall
    cart_items_with_totals = []
    for item in cart_items:
        item_total = item.product.price * item.quantity
        cart_items_with_totals.append({
            'item': item,
            'item_total': item_total,
        })
    
    subtotal = sum(item_total['item_total'] for item_total in cart_items_with_totals)
    total = subtotal  # Add shipping, tax, etc. here if needed
    
    context = {
        'settings': settings,
        'menu_pages': menu_pages,
        'footer_pages': footer_pages,
        'cart_items_with_totals': cart_items_with_totals,
        'subtotal': subtotal,
        'total': total,
    }
    
    return render(request, 'website/ecommerce/cart.html', context)


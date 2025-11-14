from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from ecommerce.models import Cart, Order, OrderItem, Coupon
from core.models import Address
from website.models import MySetting, CMSPages
import random
import string


def process_checkout(request):
    """Process checkout and create order"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Please login first'})
    
    cart_items = Cart.objects.filter(user=request.user)
    
    if not cart_items.exists():
        return JsonResponse({'success': False, 'message': 'Cart is empty'})
    
    # Get address
    address_id = request.POST.get('address_id')
    try:
        address = Address.objects.get(id=address_id, user=request.user)
    except Address.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Invalid address'})
    
    # Generate order number
    order_number = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    
    # Calculate total
    subtotal = sum(item.product.price * item.quantity for item in cart_items)
    
    # Create order
    order = Order.objects.create(
        user=request.user,
        order_number=order_number,
        total_amount=subtotal,
        shipping_address=f"{address.full_name}, {address.address}, {address.city}, {address.state} {address.zip_code}",
        billing_address=f"{address.full_name}, {address.address}, {address.city}, {address.state} {address.zip_code}",
        phone=address.phone,
        email=request.user.email or '',
        status='pending',
    )
    
    # Create order items
    for cart_item in cart_items:
        OrderItem.objects.create(
            order=order,
            product=cart_item.product,
            store=cart_item.product.store,
            quantity=cart_item.quantity,
            price=cart_item.product.price,
            total=cart_item.product.price * cart_item.quantity,
        )
    
    # Clear cart
    cart_items.delete()
    
    return JsonResponse({
        'success': True,
        'message': 'Order placed successfully',
        'order_id': order.id,
        'order_number': order.order_number,
    })


@login_required
def checkout_view(request):
    """Checkout page"""
    try:
        settings = MySetting.objects.first()
    except MySetting.DoesNotExist:
        settings = None
    
    menu_pages = CMSPages.objects.filter(on_menu=True)
    footer_pages = CMSPages.objects.filter(on_footer=True)
    
    cart_items = Cart.objects.filter(user=request.user).select_related('product')
    
    if not cart_items.exists():
        return redirect('website:cart')
    
    addresses = Address.objects.filter(user=request.user)
    default_address = addresses.filter(is_default=True).first()
    
    # Calculate totals for each item and overall
    cart_items_with_totals = []
    for item in cart_items:
        item_total = item.product.price * item.quantity
        cart_items_with_totals.append({
            'item': item,
            'item_total': item_total,
        })
    
    subtotal = sum(item_total['item_total'] for item_total in cart_items_with_totals)
    shipping = 0  # Add shipping calculation here
    total = subtotal + shipping
    
    # Coupon handling
    coupon_code = request.GET.get('coupon', '')
    coupon = None
    discount = 0
    if coupon_code:
        try:
            coupon = Coupon.objects.get(code=coupon_code.upper(), is_active=True)
            if coupon.is_valid():
                if coupon.discount_type == 'percentage':
                    discount = (subtotal * coupon.discount_value) / 100
                else:
                    discount = coupon.discount_value
                total = max(0, total - discount)
        except Coupon.DoesNotExist:
            pass
    
    context = {
        'settings': settings,
        'menu_pages': menu_pages,
        'footer_pages': footer_pages,
        'cart_items': cart_items,
        'cart_items_with_totals': cart_items_with_totals,
        'addresses': addresses,
        'default_address': default_address,
        'subtotal': subtotal,
        'shipping': shipping,
        'discount': discount,
        'total': total,
        'coupon': coupon,
    }
    
    return render(request, 'website/ecommerce/checkout.html', context)


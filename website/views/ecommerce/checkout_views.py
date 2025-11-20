from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.conf import settings
from ecommerce.models import Cart, Order, OrderItem, Coupon
from core.models import Address
from website.models import MySetting, CMSPages
from ecommerce.services.phonepe_service import (
    get_authorization_token,
    initiate_payment,
    generate_merchant_order_id,
    check_payment_status_by_order_id,
    check_payment_status_by_transaction_id
)
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
    
    # Get payment method
    payment_method = request.POST.get('payment_method', 'cod')
    
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
        payment_method=payment_method,
        status='pending',
    )
    
    # Set payment status based on payment method
    if payment_method == 'cod':
        # For COD, payment is considered successful immediately
        order.payment_status = 'success'
        order.status = 'confirmed'
        order.save()
    else:
        # For online payment, payment status is pending until payment is completed
        order.payment_status = 'pending'
        order.save()
    
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
    
    # For online payment, initiate PhonePe payment
    if payment_method == 'online':
        try:
            # Get authorization token
            auth_response = get_authorization_token()
            if 'error' in auth_response:
                return JsonResponse({
                    'success': False,
                    'message': f'Payment initiation failed: {auth_response["error"]}'
                })
            
            access_token = auth_response.get('access_token')
            if not access_token:
                return JsonResponse({
                    'success': False,
                    'message': 'Failed to get access token from PhonePe'
                })
            
            # Generate merchant order ID
            merchant_order_id = generate_merchant_order_id()
            order.phonepe_merchant_order_id = merchant_order_id
            order.save()
            
            # Build redirect URL
            redirect_url = f"{settings.PHONEPE_BASE_URL}/payment/result/?merchant_order_id={merchant_order_id}"
            
            # Initiate payment
            payment_response = initiate_payment(
                amount=float(order.total_amount),
                merchant_order_id=merchant_order_id,
                redirect_url=redirect_url,
                auth_token=access_token
            )
            
            if 'error' in payment_response:
                return JsonResponse({
                    'success': False,
                    'message': f'Payment initiation failed: {payment_response["error"]}'
                })
            
            # Extract redirect URL from response
            redirect_url_from_response = payment_response.get('data', {}).get('redirectUrl') or payment_response.get('redirectUrl')
            
            if not redirect_url_from_response:
                return JsonResponse({
                    'success': False,
                    'message': 'No redirect URL received from PhonePe'
                })
            
            return JsonResponse({
                'success': True,
                'message': 'Payment initiated successfully',
                'order_id': order.id,
                'order_number': order.order_number,
                'redirectUrl': redirect_url_from_response,
                'merchantOrderId': merchant_order_id
            })
        
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error initiating payment: {str(e)}'
            })
    
    # For COD, return success response
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


@login_required
def payment_result_view(request):
    """Payment result page - handles PhonePe callback"""
    try:
        site_settings = MySetting.objects.first()
    except MySetting.DoesNotExist:
        site_settings = None
    
    menu_pages = CMSPages.objects.filter(on_menu=True)
    footer_pages = CMSPages.objects.filter(on_footer=True)
    
    merchant_order_id = request.GET.get('merchant_order_id')
    transaction_id = request.GET.get('transaction_id')
    
    order = None
    payment_status_data = None
    
    # Try to find order
    if merchant_order_id:
        try:
            order = Order.objects.get(phonepe_merchant_order_id=merchant_order_id, user=request.user)
        except Order.DoesNotExist:
            pass
    elif transaction_id:
        try:
            order = Order.objects.get(phonepe_transaction_id=transaction_id, user=request.user)
        except Order.DoesNotExist:
            pass
    
    # Check payment status if order found
    if order:
        try:
            # Get authorization token
            auth_response = get_authorization_token()
            if 'error' not in auth_response:
                access_token = auth_response.get('access_token')
                if access_token:
                    # Check payment status
                    if merchant_order_id:
                        status_response = check_payment_status_by_order_id(merchant_order_id, access_token)
                    elif transaction_id:
                        status_response = check_payment_status_by_transaction_id(transaction_id, access_token)
                    else:
                        status_response = {}
                    
                    if 'error' not in status_response:
                        payment_status_data = status_response.get('data', {})
                        payment_details = payment_status_data.get('paymentDetails', {}) or payment_status_data
                        payment_status_value = payment_details.get('status', '').upper()
                        
                        # Update order payment status
                        if payment_status_value in ['SUCCESS', 'PAYMENT_SUCCESS', 'COMPLETED']:
                            order.payment_status = 'success'
                            order.status = 'confirmed'
                            if payment_details.get('transactionId'):
                                order.phonepe_transaction_id = payment_details.get('transactionId')
                        elif payment_status_value in ['FAILED', 'PAYMENT_FAILED', 'FAILURE']:
                            order.payment_status = 'failed'
                        elif payment_status_value in ['PENDING', 'INITIATED']:
                            order.payment_status = 'pending'
                        
                        order.save()
        except Exception as e:
            print(f"Error checking payment status: {str(e)}")
    
    context = {
        'settings': site_settings,
        'menu_pages': menu_pages,
        'footer_pages': footer_pages,
        'order': order,
        'payment_status_data': payment_status_data,
        'merchant_order_id': merchant_order_id,
        'transaction_id': transaction_id,
    }
    
    return render(request, 'website/ecommerce/payment_result.html', context)


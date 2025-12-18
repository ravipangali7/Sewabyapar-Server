from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.conf import settings
from ecommerce.models import Cart, Order, OrderItem, Coupon
from core.models import Address, SuperSetting
from website.models import MySetting, CMSPages
from collections import defaultdict
from ecommerce.services.phonepe_service import (
    initiate_payment,
    generate_merchant_order_id,
    check_payment_status_by_order_id,
    check_payment_status_by_transaction_id
)
import random
import string
import logging

logger = logging.getLogger(__name__)


def split_order_by_vendor(temp_order):
    """Split a temporary order into separate orders by vendor after payment success"""
    from ecommerce.models import Store, Product
    
    try:
        # Check if this is a temporary order with CART_DATA
        if not temp_order.notes or not temp_order.notes.startswith('CART_DATA:'):
            logger.warning(f"Order {temp_order.id} does not have CART_DATA, skipping split")
            return None
        
        # Parse cart data from notes
        cart_data_str = temp_order.notes.replace('CART_DATA:', '')
        cart_items_data = cart_data_str.split('|')
        
        # Group items by vendor
        vendor_items = defaultdict(list)
        for item_str in cart_items_data:
            if not item_str:
                continue
            try:
                store_id, product_id, quantity, price = item_str.split(':')
                store_id = int(store_id)
                product_id = int(product_id)
                quantity = int(quantity)
                price = float(price)
                
                try:
                    store = Store.objects.get(id=store_id)
                    product = Product.objects.get(id=product_id)
                    vendor_items[store].append({
                        'product': product,
                        'quantity': quantity,
                        'price': price,
                    })
                except (Store.DoesNotExist, Product.DoesNotExist) as e:
                    logger.error(f"Store or Product not found: {str(e)}")
                    continue
            except ValueError as e:
                logger.error(f"Error parsing cart item data: {item_str}, error: {str(e)}")
                continue
        
        if not vendor_items:
            logger.warning(f"No valid vendor items found in order {temp_order.id}")
            return None
        
        # Get SuperSetting
        try:
            super_setting = SuperSetting.objects.first()
            if not super_setting:
                super_setting = SuperSetting.objects.create()
            basic_shipping_charge = super_setting.basic_shipping_charge
        except Exception as e:
            logger.error(f"Error getting SuperSetting: {str(e)}")
            basic_shipping_charge = 0
        
        # Create separate order for each vendor
        created_orders = []
        for store, items in vendor_items.items():
            # Calculate subtotal for this vendor
            vendor_subtotal = sum(item['price'] * item['quantity'] for item in items)
            vendor_total = vendor_subtotal + basic_shipping_charge
            
            # Generate order number
            order_number = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
            
            # Create order for this vendor
            order = Order.objects.create(
                user=temp_order.user,
                merchant=store,
                order_number=order_number,
                subtotal=vendor_subtotal,
                shipping_cost=basic_shipping_charge,
                total_amount=vendor_total,
                shipping_address=temp_order.shipping_address,
                billing_address=temp_order.billing_address,
                phone=temp_order.phone,
                email=temp_order.email,
                payment_method=temp_order.payment_method,
                payment_status='success',  # Payment already succeeded
                status='pending',  # Waiting for merchant acceptance
                phonepe_transaction_id=temp_order.phonepe_transaction_id,
                phonepe_order_id=temp_order.phonepe_order_id,
                phonepe_merchant_order_id=temp_order.phonepe_merchant_order_id,
                phonepe_transaction_date=temp_order.phonepe_transaction_date,
            )
            
            # Create order items for this vendor
            for item in items:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    store=store,
                    quantity=item['quantity'],
                    price=item['price'],
                    total=item['price'] * item['quantity'],
                )
            
            created_orders.append(order)
        
        # Update SuperSetting balance
        super_setting.balance += temp_order.total_amount
        super_setting.save()
        
        # Delete temporary order
        temp_order.delete()
        
        logger.info(f"Successfully split order into {len(created_orders)} vendor orders")
        return created_orders
    
    except Exception as e:
        logger.error(f"Error splitting order by vendor: {str(e)}", exc_info=True)
        return None


def process_checkout(request):
    """Process checkout and create orders split by vendor"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Please login first'})
    
    cart_items = Cart.objects.filter(user=request.user).select_related('product', 'product__store')
    
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
    
    # Get SuperSetting
    try:
        super_setting = SuperSetting.objects.first()
        if not super_setting:
            super_setting = SuperSetting.objects.create()
        basic_shipping_charge = super_setting.basic_shipping_charge
    except Exception as e:
        logger.error(f"Error getting SuperSetting: {str(e)}")
        basic_shipping_charge = 0
    
    # Group cart items by vendor (store)
    vendor_items = defaultdict(list)
    for item in cart_items:
        vendor_items[item.product.store].append(item)
    
    # Calculate total amount (for payment)
    total_subtotal = sum(item.product.price * item.quantity for item in cart_items)
    vendor_count = len(vendor_items)
    total_shipping = basic_shipping_charge * vendor_count
    total_amount = total_subtotal + total_shipping
    
    # Prepare shipping address string
    shipping_address_str = f"{address.full_name}, {address.address}, {address.city}, {address.state} {address.zip_code}"
    billing_address_str = f"{address.full_name}, {address.address}, {address.city}, {address.state} {address.zip_code}"
    
    # For online payment, we'll create a temporary order to initiate payment
    # Then split into vendor orders after payment success
    if payment_method == 'online':
        try:
            # Generate merchant order ID
            merchant_order_id = generate_merchant_order_id()
            
            # Create a temporary order to track the payment
            # This will be split into vendor orders after payment success
            temp_order = Order.objects.create(
                user=request.user,
                order_number=''.join(random.choices(string.ascii_uppercase + string.digits, k=10)),
                subtotal=total_subtotal,
                shipping_cost=total_shipping,
                total_amount=total_amount,
                shipping_address=shipping_address_str,
                billing_address=billing_address_str,
                phone=address.phone,
                email=request.user.email or '',
                payment_method=payment_method,
                payment_status='pending',
                status='pending',
                phonepe_merchant_order_id=merchant_order_id,
            )
            
            # Store cart items temporarily (we'll create order items after payment success)
            # For now, just store the cart item IDs in notes or create a temporary mapping
            # We'll handle this in the payment callback
            
            # Build redirect URL
            redirect_url = f"{settings.PHONEPE_BASE_URL}/payment/result/?merchant_order_id={merchant_order_id}"
            
            # Initiate payment using SDK
            payment_response = initiate_payment(
                amount=float(total_amount),
                merchant_order_id=merchant_order_id,
                redirect_url=redirect_url
            )
            
            if 'error' in payment_response:
                temp_order.delete()
                return JsonResponse({
                    'success': False,
                    'message': f'Payment initiation failed: {payment_response["error"]}'
                })
            
            # Extract redirect URL from response
            redirect_url_from_response = payment_response.get('data', {}).get('redirectUrl') or payment_response.get('redirectUrl')
            
            if not redirect_url_from_response:
                temp_order.delete()
                return JsonResponse({
                    'success': False,
                    'message': 'No redirect URL received from PhonePe'
                })
            
            # Store cart item data in order notes temporarily (we'll parse it in callback)
            # Format: "CART_ITEMS:store_id:product_id:quantity:price|store_id:product_id:quantity:price|..."
            cart_data = []
            for store, items in vendor_items.items():
                for item in items:
                    cart_data.append(f"{store.id}:{item.product.id}:{item.quantity}:{item.product.price}")
            temp_order.notes = f"CART_DATA:{'|'.join(cart_data)}"
            temp_order.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Payment initiated successfully',
                'order_id': temp_order.id,
                'order_number': temp_order.order_number,
                'redirectUrl': redirect_url_from_response,
                'merchantOrderId': merchant_order_id
            })
        
        except Exception as e:
            logger.error(f"Error initiating payment: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'message': f'Error initiating payment: {str(e)}'
            })
    
    # For COD, create orders immediately
    else:
        try:
            # Get or create SuperSetting
            try:
                super_setting = SuperSetting.objects.first()
                if not super_setting:
                    super_setting = SuperSetting.objects.create()
            except:
                super_setting = SuperSetting.objects.create()
            
            created_orders = []
            
            # Create separate order for each vendor
            for store, items in vendor_items.items():
                # Calculate subtotal for this vendor
                vendor_subtotal = sum(item.product.price * item.quantity for item in items)
                vendor_total = vendor_subtotal + basic_shipping_charge
                
                # Generate order number
                order_number = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
                
                # Create order for this vendor
                order = Order.objects.create(
                    user=request.user,
                    merchant=store,
                    order_number=order_number,
                    subtotal=vendor_subtotal,
                    shipping_cost=basic_shipping_charge,
                    total_amount=vendor_total,
                    shipping_address=shipping_address_str,
                    billing_address=billing_address_str,
                    phone=address.phone,
                    email=request.user.email or '',
                    payment_method=payment_method,
                    payment_status='success',  # COD is considered paid
                    status='pending',  # Waiting for merchant acceptance
                )
                
                # Create order items for this vendor
                for item in items:
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        store=store,
                        quantity=item.quantity,
                        price=item.product.price,
                        total=item.product.price * item.quantity,
                    )
                
                created_orders.append(order)
            
            # Update SuperSetting balance
            super_setting.balance += total_amount
            super_setting.save()
            
            # Clear cart
            cart_items.delete()
            
            return JsonResponse({
                'success': True,
                'message': 'Order placed successfully',
                'order_ids': [order.id for order in created_orders],
                'order_numbers': [order.order_number for order in created_orders],
            })
        
        except Exception as e:
            logger.error(f"Error creating COD orders: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'message': f'Error creating order: {str(e)}'
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
    
    # Get SuperSetting for shipping calculation
    try:
        super_setting = SuperSetting.objects.first()
        if not super_setting:
            super_setting = SuperSetting.objects.create()
        basic_shipping_charge = super_setting.basic_shipping_charge
    except:
        basic_shipping_charge = 0
    
    # Group cart items by vendor (store)
    vendor_items = defaultdict(list)
    for item in cart_items:
        vendor_items[item.product.store].append(item)
    
    # Calculate totals for each item and overall
    cart_items_with_totals = []
    for item in cart_items:
        item_total = item.product.price * item.quantity
        cart_items_with_totals.append({
            'item': item,
            'item_total': item_total,
        })
    
    subtotal = sum(item_total['item_total'] for item_total in cart_items_with_totals)
    
    # Calculate shipping: basic_shipping_charge * number of vendors
    vendor_count = len(vendor_items)
    shipping = basic_shipping_charge * vendor_count
    total = subtotal + shipping
    
    # Prepare vendor breakdown for display
    vendor_breakdown = []
    for store, items in vendor_items.items():
        vendor_subtotal = sum(item.product.price * item.quantity for item in items)
        vendor_breakdown.append({
            'store': store,
            'items': items,
            'subtotal': vendor_subtotal,
            'shipping': basic_shipping_charge,
            'total': vendor_subtotal + basic_shipping_charge,
        })
    
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
        'vendor_breakdown': vendor_breakdown,
        'vendor_count': vendor_count,
        'basic_shipping_charge': basic_shipping_charge,
    }
    
    return render(request, 'website/ecommerce/checkout.html', context)


@login_required
def payment_result_view(request):
    """Payment result page - handles PhonePe callback and verifies transaction status via PhonePe API"""
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
    api_error = None
    
    # Try to find order in database
    if merchant_order_id:
        try:
            order = Order.objects.get(phonepe_merchant_order_id=merchant_order_id, user=request.user)
            logger.info(f"Order found for merchant_order_id: {merchant_order_id}, Order ID: {order.id}")
        except Order.DoesNotExist:
            logger.warning(f"Order not found for merchant_order_id: {merchant_order_id}, user: {request.user.id}")
    elif transaction_id:
        try:
            order = Order.objects.get(phonepe_transaction_id=transaction_id, user=request.user)
            logger.info(f"Order found for transaction_id: {transaction_id}, Order ID: {order.id}")
        except Order.DoesNotExist:
            logger.warning(f"Order not found for transaction_id: {transaction_id}, user: {request.user.id}")
    
    # Always call PhonePe API to verify transaction status when merchant_order_id is present
    # This ensures we get the latest status from PhonePe, even if order exists in DB
    if merchant_order_id:
        try:
            logger.info(f"Calling PhonePe API to check payment status for merchant_order_id: {merchant_order_id}")
            status_response = check_payment_status_by_order_id(merchant_order_id)
            
            if 'error' not in status_response:
                payment_status_data = status_response.get('data', {})
                logger.info(f"PhonePe API response received: {payment_status_data}")
                
                # Extract payment status from PhonePe response
                # PhonePe SDK returns 'state' as primary field (COMPLETED, FAILED, PENDING)
                # and also provides status in paymentDetails
                payment_state = payment_status_data.get('state', '').upper()
                payment_details = payment_status_data.get('paymentDetails', {}) or payment_status_data
                payment_status_value = payment_details.get('status', '').upper()
                
                # Use state as primary source (PhonePe's main status field)
                # State values: COMPLETED, FAILED, PENDING
                if payment_state:
                    payment_status_value = payment_state
                elif payment_status_value:
                    # Fallback to status if state not available
                    pass
                else:
                    payment_status_value = ''
                
                logger.info(f"Payment status from PhonePe - state: {payment_state}, status: {payment_status_value}")
                
                # Update order if found
                if order:
                    # Ensure payment_method is 'online' for PhonePe orders
                    if order.payment_method != 'online':
                        order.payment_method = 'online'
                        logger.info(f"Updated payment_method to 'online' for order {order.id}")
                    
                    # Map PhonePe state/status values to our payment_status field
                    # PhonePe SDK state values: COMPLETED, FAILED, PENDING (primary)
                    # Also handles: PAYMENT_SUCCESS, PAYMENT_PENDING, PAYMENT_ERROR, etc.
                    if payment_status_value in ['COMPLETED', 'PAYMENT_SUCCESS', 'SUCCESS', 'PAID']:
                        order.payment_status = 'success'
                        order.status = 'confirmed'
                        logger.info(f"Order {order.id} marked as payment success (status: {payment_status_value})")
                        
                        # If this is a temporary order with CART_DATA, split it by vendor
                        if order.notes and order.notes.startswith('CART_DATA:'):
                            logger.info(f"Splitting temporary order {order.id} by vendor")
                            created_orders = split_order_by_vendor(order)
                            if created_orders:
                                # Update order to the first created order for display
                                order = created_orders[0]
                                logger.info(f"Order split into {len(created_orders)} vendor orders")
                            else:
                                logger.error(f"Failed to split order {order.id} by vendor")
                    elif payment_status_value in ['FAILED', 'PAYMENT_ERROR', 'PAYMENT_FAILED', 'FAILURE', 'ERROR']:
                        order.payment_status = 'failed'
                        logger.info(f"Order {order.id} marked as payment failed (status: {payment_status_value})")
                    elif payment_status_value in ['PENDING', 'PAYMENT_PENDING', 'INITIATED', 'AUTHORIZED']:
                        order.payment_status = 'pending'
                        logger.info(f"Order {order.id} marked as payment pending (status: {payment_status_value})")
                    else:
                        # Unknown status - keep as pending but log it
                        order.payment_status = 'pending'
                        logger.warning(f"Unknown payment status '{payment_status_value}' for order {order.id}, set to pending")
                    
                    # Update transaction ID if available
                    transaction_id_from_api = payment_details.get('transactionId') or payment_status_data.get('transactionId')
                    if transaction_id_from_api and not order.phonepe_transaction_id:
                        order.phonepe_transaction_id = transaction_id_from_api
                        logger.info(f"Updated transaction_id for order {order.id}: {transaction_id_from_api}")
                    
                    # Save all PhonePe transaction details
                    order_id_from_api = payment_status_data.get('orderId')
                    if order_id_from_api and not order.phonepe_order_id:
                        order.phonepe_order_id = order_id_from_api
                        logger.info(f"Updated order_id for order {order.id}: {order_id_from_api}")
                    
                    # Save UTR and VPA from payment details
                    utr_from_api = payment_details.get('utr') or payment_status_data.get('utr')
                    if utr_from_api and not order.phonepe_utr:
                        order.phonepe_utr = utr_from_api
                        logger.info(f"Updated UTR for order {order.id}: {utr_from_api}")
                    
                    vpa_from_api = payment_details.get('vpa') or payment_status_data.get('vpa')
                    if vpa_from_api and not order.phonepe_vpa:
                        order.phonepe_vpa = vpa_from_api
                        logger.info(f"Updated VPA for order {order.id}: {vpa_from_api}")
                    
                    # Save transaction date
                    transaction_date_str = payment_details.get('transactionDate') or payment_status_data.get('transactionDate')
                    if transaction_date_str and not order.phonepe_transaction_date:
                        try:
                            from datetime import datetime
                            transaction_date = datetime.fromisoformat(transaction_date_str)
                            order.phonepe_transaction_date = transaction_date
                            logger.info(f"Updated transaction_date for order {order.id}: {transaction_date}")
                        except (ValueError, TypeError) as e:
                            logger.warning(f"Could not parse transaction_date for order {order.id}: {e}")
                    
                    # Save processing mechanism
                    processing_mechanism = payment_details.get('processingMechanism') or payment_status_data.get('processingMechanism')
                    if processing_mechanism and not order.phonepe_processing_mechanism:
                        order.phonepe_processing_mechanism = processing_mechanism
                        logger.info(f"Updated processing_mechanism for order {order.id}: {processing_mechanism}")
                    
                    # Save product type
                    product_type = payment_details.get('productType') or payment_status_data.get('productType')
                    if product_type and not order.phonepe_product_type:
                        order.phonepe_product_type = product_type
                        logger.info(f"Updated product_type for order {order.id}: {product_type}")
                    
                    # Save instrument type
                    instrument_type = payment_details.get('instrumentType') or payment_status_data.get('instrumentType')
                    if instrument_type and not order.phonepe_instrument_type:
                        order.phonepe_instrument_type = instrument_type
                        logger.info(f"Updated instrument_type for order {order.id}: {instrument_type}")
                    
                    # Save payment mode
                    payment_mode = payment_details.get('paymentMode') or payment_status_data.get('paymentMode')
                    if payment_mode and not order.phonepe_payment_mode:
                        order.phonepe_payment_mode = payment_mode
                        logger.info(f"Updated payment_mode for order {order.id}: {payment_mode}")
                    
                    # Save bank ID
                    bank_id = payment_details.get('bankId') or payment_status_data.get('bankId')
                    if bank_id and not order.phonepe_bank_id:
                        order.phonepe_bank_id = bank_id
                        logger.info(f"Updated bank_id for order {order.id}: {bank_id}")
                    
                    # Save card network
                    card_network = payment_details.get('cardNetwork') or payment_status_data.get('cardNetwork')
                    if card_network and not order.phonepe_card_network:
                        order.phonepe_card_network = card_network
                        logger.info(f"Updated card_network for order {order.id}: {card_network}")
                    
                    # Save transaction note
                    transaction_note = payment_details.get('transactionNote') or payment_status_data.get('transactionNote')
                    if transaction_note and not order.phonepe_transaction_note:
                        order.phonepe_transaction_note = transaction_note
                        logger.info(f"Updated transaction_note for order {order.id}: {transaction_note}")
                    
                    order.save()
                    logger.info(f"Order {order.id} saved with payment_status: {order.payment_status}")
                else:
                    # Order not found in DB but PhonePe has record - log this case
                    logger.warning(f"PhonePe API returned status but order not found in DB for merchant_order_id: {merchant_order_id}")
            else:
                # PhonePe API returned an error
                api_error = status_response.get('error', 'Unknown error')
                logger.error(f"PhonePe API error for merchant_order_id {merchant_order_id}: {api_error}")
                
                # If order exists but API call failed, we still show the order
                # but payment status might be outdated
                if order:
                    logger.warning(f"PhonePe API call failed for existing order {order.id}, using current DB status")
        
        except Exception as e:
            api_error = str(e)
            logger.error(f"Exception while calling PhonePe API for merchant_order_id {merchant_order_id}: {str(e)}", exc_info=True)
            
            # If order exists but API call failed, we still show the order
            if order:
                logger.warning(f"PhonePe API call exception for existing order {order.id}, using current DB status")
    
    elif transaction_id:
        # Try to check by transaction_id (though PhonePe SDK primarily uses merchant_order_id)
        try:
            logger.info(f"Calling PhonePe API to check payment status for transaction_id: {transaction_id}")
            status_response = check_payment_status_by_transaction_id(transaction_id)
            
            if 'error' not in status_response:
                payment_status_data = status_response.get('data', {})
                payment_details = payment_status_data.get('paymentDetails', {}) or payment_status_data
                payment_status_value = payment_details.get('status', '').upper()
                
                if order:
                    if order.payment_method != 'online':
                        order.payment_method = 'online'
                    
                    if payment_status_value in ['PAYMENT_SUCCESS', 'SUCCESS', 'COMPLETED', 'PAID']:
                        order.payment_status = 'success'
                        order.status = 'confirmed'
                    elif payment_status_value in ['PAYMENT_ERROR', 'PAYMENT_FAILED', 'FAILED', 'FAILURE']:
                        order.payment_status = 'failed'
                    elif payment_status_value in ['PAYMENT_PENDING', 'PENDING', 'INITIATED']:
                        order.payment_status = 'pending'
                    
                    order.save()
            else:
                api_error = status_response.get('error', 'Unknown error')
                logger.error(f"PhonePe API error for transaction_id {transaction_id}: {api_error}")
        except Exception as e:
            api_error = str(e)
            logger.error(f"Exception while calling PhonePe API for transaction_id {transaction_id}: {str(e)}", exc_info=True)
    
    context = {
        'settings': site_settings,
        'menu_pages': menu_pages,
        'footer_pages': footer_pages,
        'order': order,
        'payment_status_data': payment_status_data,
        'merchant_order_id': merchant_order_id,
        'transaction_id': transaction_id,
        'api_error': api_error,
    }
    
    return render(request, 'website/ecommerce/payment_result.html', context)


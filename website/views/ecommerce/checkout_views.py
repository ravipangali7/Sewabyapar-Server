from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.conf import settings
from ecommerce.models import Cart, Order, OrderItem, Coupon
from core.models import Transaction
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
import sys
import traceback


def split_order_by_vendor(temp_order):
    """Split a temporary order into separate orders by vendor after payment success"""
    from ecommerce.models import Store, Product
    
    try:
        # Check if this is a temporary order with CART_DATA
        if not temp_order.notes or not temp_order.notes.startswith('CART_DATA:'):
            print(f"[WARNING] Order {temp_order.id} does not have CART_DATA, skipping split")
            sys.stdout.flush()
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
                    print(f"[ERROR] Store or Product not found: {str(e)}")
                    sys.stdout.flush()
                    continue
            except ValueError as e:
                print(f"[ERROR] Error parsing cart item data: {item_str}, error: {str(e)}")
                sys.stdout.flush()
                continue
        
        if not vendor_items:
            print(f"[WARNING] No valid vendor items found in order {temp_order.id}")
            sys.stdout.flush()
            return None
        
        # Get SuperSetting
        try:
            super_setting = SuperSetting.objects.first()
            if not super_setting:
                super_setting = SuperSetting.objects.create()
            basic_shipping_charge = super_setting.basic_shipping_charge
        except Exception as e:
            print(f"[ERROR] Error getting SuperSetting: {str(e)}")
            sys.stdout.flush()
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
        
        # Delete temporary order
        temp_order.delete()
        
        print(f"[INFO] Successfully split order into {len(created_orders)} vendor orders")
        sys.stdout.flush()
        return created_orders
    
    except Exception as e:
        print(f"[ERROR] Error splitting order by vendor: {str(e)}")
        traceback.print_exc()
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
        print(f"[ERROR] Error getting SuperSetting: {str(e)}")
        sys.stdout.flush()
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
            # Create a temporary order to track the payment
            # This will be split into vendor orders after payment success
            # Note: clientTxnId will be generated and stored by SabPaisa service
            temp_order = Order.objects.create(
                user=request.user,
                order_number=''.join(random.choices(string.ascii_uppercase + string.digits, k=10)),
                subtotal=total_subtotal,
                shipping_cost=total_shipping,
                total_amount=total_amount,
                shipping_address=address,  # Store address object, not string
                billing_address=address,  # Store address object, not string
                phone=address.phone,
                email=request.user.email or '',
                payment_method=payment_method,
                payment_status='pending',
                status='pending',
            )
            
            # Store cart items temporarily (we'll create order items after payment success)
            # For now, just store the cart item IDs in notes or create a temporary mapping
            # We'll handle this in the payment callback
            
            # Initiate SabPaisa payment
            from ecommerce.services.sabpaisa_service import initiate_sabpaisa_payment
            
            payer_name = address.full_name if address.full_name else request.user.name
            payer_email = request.user.email or ''
            payer_mobile = address.phone
            payer_address = f"{address.address}, {address.city}, {address.state} {address.zip_code}"
            
            payment_response = initiate_sabpaisa_payment(
                order=temp_order,
                payer_name=payer_name,
                payer_email=payer_email,
                payer_mobile=payer_mobile,
                payer_address=payer_address
            )
            
            if 'error' in payment_response:
                temp_order.delete()
                return JsonResponse({
                    'success': False,
                    'message': f'Payment initiation failed: {payment_response["error"]}'
                })
            
            # Extract encData and clientCode from response
            enc_data = payment_response.get('encData')
            client_code = payment_response.get('clientCode')
            client_txn_id = payment_response.get('clientTxnId')
            
            if not enc_data or not client_code:
                temp_order.delete()
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid payment response from SabPaisa'
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
                'encData': enc_data,
                'clientCode': client_code,
                'clientTxnId': client_txn_id,
                'sabpaisaUrl': getattr(settings, 'SABPAISA_URL', 'https://stage-securepay.sabpaisa.in/SabPaisa/sabPaisaInit?v=1')
            })
        
        except Exception as e:
            print(f"[ERROR] Error initiating payment: {str(e)}")
            traceback.print_exc()
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
                    payment_status='pending',  # COD payment is pending until delivery
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
            
            # Clear cart
            cart_items.delete()
            
            return JsonResponse({
                'success': True,
                'message': 'Order placed successfully',
                'order_ids': [order.id for order in created_orders],
                'order_numbers': [order.order_number for order in created_orders],
            })
        
        except Exception as e:
            print(f"[ERROR] Error creating COD orders: {str(e)}")
            traceback.print_exc()
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
    
    # Try to find Transaction and Order in database
    transaction = None
    order = None
    if merchant_order_id:
        try:
            transaction = Transaction.objects.get(merchant_order_id=merchant_order_id, user=request.user)
            order = transaction.related_order
            print(f"[INFO] Transaction found for merchant_order_id: {merchant_order_id}, Order ID: {order.id if order else 'None'}")
            sys.stdout.flush()
        except Transaction.DoesNotExist:
            print(f"[WARNING] Transaction not found for merchant_order_id: {merchant_order_id}, user: {request.user.id}")
            sys.stdout.flush()
    elif transaction_id:
        # For transaction_id, we can't directly look up - need merchant_order_id
        print(f"[WARNING] transaction_id lookup not supported, need merchant_order_id")
        sys.stdout.flush()
    
    # Always call PhonePe API to verify transaction status when merchant_order_id is present
    # This ensures we get the latest status from PhonePe, even if order exists in DB
    if merchant_order_id:
        try:
            print(f"[INFO] Calling PhonePe API to check payment status for merchant_order_id: {merchant_order_id}")
            sys.stdout.flush()
            status_response = check_payment_status_by_order_id(merchant_order_id)
            
            if 'error' not in status_response:
                payment_status_data = status_response.get('data', {})
                print(f"[INFO] PhonePe API response received: {payment_status_data}")
                sys.stdout.flush()
                
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
                
                print(f"[INFO] Payment status from PhonePe - state: {payment_state}, status: {payment_status_value}")
                sys.stdout.flush()
                
                # Update order if found
                if order:
                    # Ensure payment_method is 'online' for PhonePe orders
                    if order.payment_method != 'online':
                        order.payment_method = 'online'
                        print(f"[INFO] Updated payment_method to 'online' for order {order.id}")
                        sys.stdout.flush()
                    
                    # Map PhonePe state/status values to our payment_status field
                    # PhonePe SDK state values: COMPLETED, FAILED, PENDING (primary)
                    # Also handles: PAYMENT_SUCCESS, PAYMENT_PENDING, PAYMENT_ERROR, etc.
                    if payment_status_value in ['COMPLETED', 'PAYMENT_SUCCESS', 'SUCCESS', 'PAID']:
                        if transaction:
                            transaction.status = 'completed'
                            transaction.utr = payment_details.get('utr') or transaction.utr
                            transaction.vpa = payment_details.get('vpa') or transaction.vpa
                            transaction.bank_id = payment_details.get('bankId') or transaction.bank_id
                            transaction.save()
                        
                        order.payment_status = 'success'
                        order.status = 'confirmed'
                        print(f"[INFO] Order {order.id} marked as payment success (status: {payment_status_value})")
                        sys.stdout.flush()
                        
                        # If this is a temporary order with CART_DATA, split it by vendor
                        if order.notes and order.notes.startswith('CART_DATA:'):
                            print(f"[INFO] Splitting temporary order {order.id} by vendor")
                            sys.stdout.flush()
                            created_orders = split_order_by_vendor(order)
                            if created_orders:
                                # Update transaction to point to first created order
                                if transaction:
                                    transaction.related_order = created_orders[0]
                                    transaction.save()
                                # Update order to the first created order for display
                                order = created_orders[0]
                                print(f"[INFO] Order split into {len(created_orders)} vendor orders")
                                sys.stdout.flush()
                            else:
                                print(f"[ERROR] Failed to split order {order.id} by vendor")
                                sys.stdout.flush()
                        else:
                            order.save()
                    elif payment_status_value in ['FAILED', 'PAYMENT_ERROR', 'PAYMENT_FAILED', 'FAILURE', 'ERROR']:
                        if transaction:
                            transaction.status = 'failed'
                            transaction.save()
                        
                        # Delete temporary order if payment failed (only if it's a temporary order with CART_DATA)
                        if order.notes and order.notes.startswith('CART_DATA:'):
                            order_id = order.id
                            order_number = order.order_number
                            order.delete()
                            print(f"[INFO] Temporary order {order_id} (order_number: {order_number}) deleted due to payment failure (status: {payment_status_value})")
                            sys.stdout.flush()
                            # Set order to None so it won't be displayed
                            order = None
                        else:
                            # For non-temporary orders, just mark as failed
                            order.payment_status = 'failed'
                            order.save()
                            print(f"[INFO] Order {order.id} marked as payment failed (status: {payment_status_value})")
                            sys.stdout.flush()
                    elif payment_status_value in ['PENDING', 'PAYMENT_PENDING', 'INITIATED', 'AUTHORIZED']:
                        if transaction:
                            transaction.status = 'pending'
                            transaction.save()
                        order.payment_status = 'pending'
                        order.save()
                        print(f"[INFO] Order {order.id} marked as payment pending (status: {payment_status_value})")
                        sys.stdout.flush()
                    else:
                        # Unknown status - keep as pending but log it
                        if transaction:
                            transaction.status = 'pending'
                            transaction.save()
                        order.payment_status = 'pending'
                        order.save()
                        print(f"[WARNING] Unknown payment status '{payment_status_value}' for order {order.id}, set to pending")
                        sys.stdout.flush()
                    
                    # Note: Transaction details (UTR, VPA) are now stored in Transaction model, not Order
                    
                    # Save transaction date
                    transaction_date_str = payment_details.get('transactionDate') or payment_status_data.get('transactionDate')
                    if transaction_date_str and not order.phonepe_transaction_date:
                        try:
                            from datetime import datetime
                            transaction_date = datetime.fromisoformat(transaction_date_str)
                            order.phonepe_transaction_date = transaction_date
                            print(f"[INFO] Updated transaction_date for order {order.id}: {transaction_date}")
                            sys.stdout.flush()
                        except (ValueError, TypeError) as e:
                            print(f"[WARNING] Could not parse transaction_date for order {order.id}: {e}")
                            sys.stdout.flush()
                    
                    # Save processing mechanism
                    processing_mechanism = payment_details.get('processingMechanism') or payment_status_data.get('processingMechanism')
                    if processing_mechanism and not order.phonepe_processing_mechanism:
                        order.phonepe_processing_mechanism = processing_mechanism
                        print(f"[INFO] Updated processing_mechanism for order {order.id}: {processing_mechanism}")
                        sys.stdout.flush()
                    
                    # Save product type
                    product_type = payment_details.get('productType') or payment_status_data.get('productType')
                    if product_type and not order.phonepe_product_type:
                        order.phonepe_product_type = product_type
                        print(f"[INFO] Updated product_type for order {order.id}: {product_type}")
                        sys.stdout.flush()
                    
                    # Save instrument type
                    instrument_type = payment_details.get('instrumentType') or payment_status_data.get('instrumentType')
                    if instrument_type and not order.phonepe_instrument_type:
                        order.phonepe_instrument_type = instrument_type
                        print(f"[INFO] Updated instrument_type for order {order.id}: {instrument_type}")
                        sys.stdout.flush()
                    
                    # Save payment mode
                    payment_mode = payment_details.get('paymentMode') or payment_status_data.get('paymentMode')
                    if payment_mode and not order.phonepe_payment_mode:
                        order.phonepe_payment_mode = payment_mode
                        print(f"[INFO] Updated payment_mode for order {order.id}: {payment_mode}")
                        sys.stdout.flush()
                    
                    # Save bank ID
                    bank_id = payment_details.get('bankId') or payment_status_data.get('bankId')
                    if bank_id and not order.phonepe_bank_id:
                        order.phonepe_bank_id = bank_id
                        print(f"[INFO] Updated bank_id for order {order.id}: {bank_id}")
                        sys.stdout.flush()
                    
                    # Save card network
                    card_network = payment_details.get('cardNetwork') or payment_status_data.get('cardNetwork')
                    if card_network and not order.phonepe_card_network:
                        order.phonepe_card_network = card_network
                        print(f"[INFO] Updated card_network for order {order.id}: {card_network}")
                        sys.stdout.flush()
                    
                    # Save transaction note
                    transaction_note = payment_details.get('transactionNote') or payment_status_data.get('transactionNote')
                    if transaction_note and not order.phonepe_transaction_note:
                        order.phonepe_transaction_note = transaction_note
                        print(f"[INFO] Updated transaction_note for order {order.id}: {transaction_note}")
                        sys.stdout.flush()
                    
                    order.save()
                    print(f"[INFO] Order {order.id} saved with payment_status: {order.payment_status}")
                    sys.stdout.flush()
                else:
                    # Order not found in DB but PhonePe has record - log this case
                    print(f"[WARNING] PhonePe API returned status but order not found in DB for merchant_order_id: {merchant_order_id}")
                    sys.stdout.flush()
            else:
                # PhonePe API returned an error
                api_error = status_response.get('error', 'Unknown error')
                print(f"[ERROR] PhonePe API error for merchant_order_id {merchant_order_id}: {api_error}")
                sys.stdout.flush()
                
                # If order exists but API call failed, we still show the order
                # but payment status might be outdated
                if order:
                    print(f"[WARNING] PhonePe API call failed for existing order {order.id}, using current DB status")
                    sys.stdout.flush()
        
        except Exception as e:
            api_error = str(e)
            print(f"[ERROR] Exception while calling PhonePe API for merchant_order_id {merchant_order_id}: {str(e)}")
            traceback.print_exc()
            
            # If order exists but API call failed, we still show the order
            if order:
                print(f"[WARNING] PhonePe API call exception for existing order {order.id}, using current DB status")
                sys.stdout.flush()
    
    elif transaction_id:
        # Try to check by transaction_id (though PhonePe SDK primarily uses merchant_order_id)
        try:
            print(f"[INFO] Calling PhonePe API to check payment status for transaction_id: {transaction_id}")
            sys.stdout.flush()
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
                        order.save()
                    elif payment_status_value in ['PAYMENT_ERROR', 'PAYMENT_FAILED', 'FAILED', 'FAILURE']:
                        # Delete temporary order if payment failed (only if it's a temporary order with CART_DATA)
                        if order.notes and order.notes.startswith('CART_DATA:'):
                            order_id = order.id
                            order_number = order.order_number
                            order.delete()
                            print(f"[INFO] Temporary order {order_id} (order_number: {order_number}) deleted due to payment failure (status: {payment_status_value})")
                            sys.stdout.flush()
                            order = None
                        else:
                            order.payment_status = 'failed'
                            order.save()
                    elif payment_status_value in ['PAYMENT_PENDING', 'PENDING', 'INITIATED']:
                        order.payment_status = 'pending'
                        order.save()
            else:
                api_error = status_response.get('error', 'Unknown error')
                print(f"[ERROR] PhonePe API error for transaction_id {transaction_id}: {api_error}")
                sys.stdout.flush()
        except Exception as e:
            api_error = str(e)
            print(f"[ERROR] Exception while calling PhonePe API for transaction_id {transaction_id}: {str(e)}")
            traceback.print_exc()
    
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


from django.db.models.signals import post_save, pre_save
from django.db import transaction as db_transaction
from django.dispatch import receiver
from decimal import Decimal, ROUND_HALF_UP
from .models import Order
from core.models import Transaction
from core.models import SuperSetting
import sys
import traceback


@receiver(post_save, sender=Order)
def handle_order_delivery(sender, instance, created, **kwargs):
    """Handle order delivery and calculate commission"""
    # Only process if order is delivered and payment is successful
    if instance.status == 'delivered' and instance.payment_status == 'success':
        # Check if commission has already been processed (to avoid double processing)
        if instance.commission_processed:
            print(f"[INFO] Order {instance.id} commission already processed, skipping")
            sys.stdout.flush()
            return
        
        if not instance.merchant:
            print(f"[WARNING] Order {instance.id} is delivered but has no merchant assigned")
            sys.stdout.flush()
            return
        
        try:
            # Use database transaction to ensure atomicity
            with db_transaction.atomic():
                # Get SuperSetting
                super_setting = SuperSetting.objects.select_for_update().first()
                if not super_setting:
                    print("[WARNING] SuperSetting not found, creating default")
                    sys.stdout.flush()
                    super_setting = SuperSetting.objects.create()
                
                # Calculate total price and total actual_price from order items
                sales_commission_percentage = Decimal(str(super_setting.sales_commission))
                total_price = Decimal('0')
                total_actual_price = Decimal('0')
                
                for order_item in instance.items.all():
                    item_price = Decimal(str(order_item.price)) * Decimal(str(order_item.quantity))
                    total_price += item_price
                    
                    # Get actual_price from order item (or fallback to price if not set)
                    if order_item.actual_price:
                        item_actual_price = Decimal(str(order_item.actual_price)) * Decimal(str(order_item.quantity))
                    else:
                        # Backward compatibility: if actual_price not set, calculate from price
                        # This assumes price includes commission, so reverse calculate
                        item_actual_price = item_price / (Decimal('1') + (sales_commission_percentage / Decimal('100')))
                    total_actual_price += item_actual_price
                
                # Commission = what customer paid (price) - what merchant should get (actual_price)
                commission = total_price - total_actual_price
                commission = commission.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                
                # Get shipping charge from ShippingChargeHistory
                from .models import ShippingChargeHistory
                shipping_charge_history = ShippingChargeHistory.objects.filter(
                    order=instance,
                    merchant=instance.merchant
                ).first()
                
                shipping_charge = Decimal('0')
                if shipping_charge_history:
                    shipping_charge = Decimal(str(shipping_charge_history.shipping_charge))
                    shipping_charge = shipping_charge.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                
                # Merchant payout: actual_price - shipping_charge
                vendor_payout = total_actual_price - shipping_charge
                vendor_payout = vendor_payout.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                
                # Update SuperSetting balance with commission
                super_setting.balance = Decimal(str(super_setting.balance)) + commission
                # Round SuperSetting balance to 2 decimal places
                super_setting.balance = super_setting.balance.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                super_setting.save()
                
                # Get vendor and initial wallet balance
                vendor = instance.merchant.owner
                current_wallet = Decimal(str(vendor.balance))
                current_wallet = current_wallet.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                
                # Get payment transaction details from Transaction model if available
                # Check for both PhonePe and SabPaisa transactions
                payment_transaction = Transaction.objects.filter(
                    related_order=instance,
                    transaction_type__in=['phonepe_payment', 'sabpaisa_payment']
                ).first()
                
                # Transaction 1: Add actual_price to merchant wallet
                wallet_before_actual_price = current_wallet
                current_wallet = current_wallet + total_actual_price
                current_wallet = current_wallet.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                wallet_after_actual_price = current_wallet
                
                Transaction.objects.create(
                    user=vendor,
                    transaction_type='payout',
                    amount=total_actual_price,  # Positive amount - actual_price goes to merchant
                    status='completed',
                    description=f'Actual price from order {instance.order_number} (₹{total_actual_price})',
                    related_order=instance,
                    payer_name=vendor.name if vendor.name else None,
                    wallet_before=wallet_before_actual_price,
                    wallet_after=wallet_after_actual_price,
                )
                
                # Transaction 2: Shipping Charge Deduction (negative amount)
                wallet_before_shipping = current_wallet
                if shipping_charge > 0:
                    current_wallet = current_wallet - shipping_charge
                    current_wallet = current_wallet.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                    wallet_after_shipping = current_wallet
                    
                    Transaction.objects.create(
                        user=vendor,
                        transaction_type='shipping_charge_deduction',
                        amount=-shipping_charge,  # Negative amount for deduction
                        status='completed',
                        description=f'Shipping charge deducted from order {instance.order_number} (₹{shipping_charge})',
                        related_order=instance,
                        payer_name=vendor.name if vendor.name else None,
                        wallet_before=wallet_before_shipping,
                        wallet_after=wallet_after_shipping,
                    )
                
                # Update vendor balance to final amount
                vendor.balance = current_wallet
                vendor.save()
                
                # Mark commission as processed (use update to avoid triggering signal again)
                Order.objects.filter(pk=instance.pk).update(commission_processed=True)
                
                print(f"[INFO] Order {instance.id} delivered: Total Price={total_price}, Total Actual Price={total_actual_price}, Commission={commission} (added to SuperSetting), Shipping Charge={shipping_charge}, Payout={vendor_payout} (added to vendor), SuperSetting balance={super_setting.balance}, Vendor balance={vendor.balance}")
                sys.stdout.flush()
            
        except Exception as e:
            print(f"[ERROR] Error processing commission for order {instance.id}: {str(e)}")
            traceback.print_exc()

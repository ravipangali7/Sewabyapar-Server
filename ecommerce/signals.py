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
                
                # Calculate commission and round to 2 decimal places
                # Ensure we're working with Decimal types
                subtotal = Decimal(str(instance.subtotal))
                sales_commission_percentage = Decimal(str(super_setting.sales_commission))
                
                # Calculate commission on subtotal only (shipping is handled separately)
                commission = (subtotal * sales_commission_percentage) / Decimal('100')
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
                
                # Calculate vendor payout: (subtotal - commission) - shipping_charge
                vendor_payout_before_shipping = subtotal - commission
                vendor_payout = vendor_payout_before_shipping - shipping_charge
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
                
                # Transaction 1: Commission Deduction (negative amount)
                wallet_before_commission = current_wallet
                current_wallet = current_wallet - commission
                current_wallet = current_wallet.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                wallet_after_commission = current_wallet
                
                Transaction.objects.create(
                    user=vendor,
                    transaction_type='commission_deduction',
                    amount=-commission,  # Negative amount for deduction
                    status='completed',
                    description=f'Sales commission deducted from order {instance.order_number} ({sales_commission_percentage}% of ₹{subtotal})',
                    related_order=instance,
                    payer_name=vendor.name if vendor.name else None,
                    wallet_before=wallet_before_commission,
                    wallet_after=wallet_after_commission,
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
                        description=f'Shipping charge deducted from order {instance.order_number}',
                        related_order=instance,
                        payer_name=vendor.name if vendor.name else None,
                        wallet_before=wallet_before_shipping,
                        wallet_after=wallet_after_shipping,
                    )
                
                # Transaction 3: Payout (positive amount)
                wallet_before_payout = current_wallet
                current_wallet = current_wallet + vendor_payout
                current_wallet = current_wallet.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                wallet_after_payout = current_wallet
                
                Transaction.objects.create(
                    user=vendor,
                    transaction_type='payout',
                    amount=vendor_payout,  # Positive amount for payout
                    status='completed',
                    description=f'Payout from order {instance.order_number}',
                    related_order=instance,
                    utr=payment_transaction.utr if payment_transaction and payment_transaction.utr else None,
                    bank_id=payment_transaction.bank_id if payment_transaction and payment_transaction.bank_id else None,
                    vpa=payment_transaction.vpa if payment_transaction and payment_transaction.vpa else None,
                    payer_name=vendor.name if vendor.name else None,
                    wallet_before=wallet_before_payout,
                    wallet_after=wallet_after_payout,
                )
                
                # Update vendor balance to final amount
                vendor.balance = current_wallet
                vendor.save()
                
                # Mark commission as processed (use update to avoid triggering signal again)
                Order.objects.filter(pk=instance.pk).update(commission_processed=True)
                
                print(f"[INFO] Order {instance.id} delivered: Commission={commission} (added to SuperSetting), Payout={vendor_payout} (added to vendor), SuperSetting balance={super_setting.balance}, Vendor balance={vendor.balance}")
                sys.stdout.flush()
            
        except Exception as e:
            print(f"[ERROR] Error processing commission for order {instance.id}: {str(e)}")
            traceback.print_exc()

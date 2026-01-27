"""Travel app signals"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from decimal import Decimal, ROUND_HALF_UP
from travel.models import TravelBooking
from core.models import Transaction, SuperSetting


@receiver(post_save, sender=TravelBooking)
def handle_booking_status_change(sender, instance, created, **kwargs):
    """Handle booking status change to 'boarded' - distribute commissions"""
    if instance.status == 'boarded' and not created:
        # Check if commissions already distributed (by checking if transactions exist)
        existing_transactions = Transaction.objects.filter(
            related_travel_booking=instance,
            status='completed'
        ).exists()
        
        if not existing_transactions:
            distribute_travel_commissions(instance)


def distribute_travel_commissions(booking):
    """Distribute commissions on boarding status"""
    from django.db import transaction as db_transaction
    
    if booking.status != 'boarded':
        return
    
    with db_transaction.atomic():
        # Get all parties
        committee_user = booking.vehicle.committee.user
        dealer_user = None
        agent_user = None
        
        if booking.agent:
            agent_user = booking.agent.user
            if booking.agent.dealer:
                dealer_user = booking.agent.dealer.user
        
        # Get current balances
        committee_balance_before = Decimal(str(committee_user.balance))
        dealer_balance_before = Decimal(str(dealer_user.balance)) if dealer_user else Decimal('0')
        agent_balance_before = Decimal(str(agent_user.balance)) if agent_user else Decimal('0')
        
        # Get SuperSetting for system balance
        super_setting = SuperSetting.objects.first()
        if not super_setting:
            super_setting = SuperSetting.objects.create()
        system_balance_before = Decimal(str(super_setting.balance))
        
        # Update balances
        actual_price = Decimal(str(booking.actual_price))
        dealer_commission = Decimal(str(booking.dealer_commission))
        agent_commission = Decimal(str(booking.agent_commission))
        system_commission = Decimal(str(booking.system_commission))
        
        # Committee gets actual_price
        committee_user.balance = committee_balance_before + actual_price
        committee_user.balance = committee_user.balance.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        committee_user.save()
        
        # Dealer gets dealer_commission
        if dealer_user:
            dealer_user.balance = dealer_balance_before + dealer_commission
            dealer_user.balance = dealer_user.balance.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            dealer_user.save()
        
        # Agent gets agent_commission
        if agent_user:
            agent_user.balance = agent_balance_before + agent_commission
            agent_user.balance = agent_user.balance.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            agent_user.save()
        
        # System gets system_commission
        super_setting.balance = system_balance_before + system_commission
        super_setting.balance = super_setting.balance.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        super_setting.save()
        
        # Create transactions
        # Committee transaction
        Transaction.objects.create(
            user=committee_user,
            transaction_type='travel_booking_revenue',
            amount=actual_price,
            status='completed',
            description=f'Travel booking revenue for ticket {booking.ticket_number}',
            related_travel_booking=booking,
            wallet_before=committee_balance_before,
            wallet_after=committee_user.balance
        )
        
        # Dealer transaction
        if dealer_user:
            Transaction.objects.create(
                user=dealer_user,
                transaction_type='travel_booking_revenue',
                amount=dealer_commission,
                status='completed',
                description=f'Travel booking revenue for ticket {booking.ticket_number}',
                related_travel_booking=booking,
                wallet_before=dealer_balance_before,
                wallet_after=dealer_user.balance
            )
        
        # Agent transaction
        if agent_user:
            Transaction.objects.create(
                user=agent_user,
                transaction_type='travel_booking_revenue',
                amount=agent_commission,
                status='completed',
                description=f'Travel booking revenue for ticket {booking.ticket_number}',
                related_travel_booking=booking,
                wallet_before=agent_balance_before,
                wallet_after=agent_user.balance
            )
        
        # System transaction (using a system user or SuperSetting)
        # For system transactions, we'll use the committee user as a placeholder
        # but mark it clearly in description
        Transaction.objects.create(
            user=committee_user,  # Placeholder - system transactions
            transaction_type='travel_booking_commission',
            amount=system_commission,
            status='completed',
            description=f'System commission for travel booking ticket {booking.ticket_number}',
            related_travel_booking=booking,
            wallet_before=system_balance_before,
            wallet_after=super_setting.balance
        )

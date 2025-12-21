"""
Django management command to update order tracking from Shipdaak
Run this periodically (e.g., every 30 minutes via cron or Celery)
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
from ecommerce.models import Order
from ecommerce.services.shipdaak_service import ShipdaakService
import traceback


class Command(BaseCommand):
    help = 'Update order tracking status from Shipdaak API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Maximum number of orders to process (default: 100)',
        )

    def handle(self, *args, **options):
        limit = options['limit']
        
        # Get orders with AWB numbers that are not yet delivered
        orders = Order.objects.filter(
            shipdaak_awb_number__isnull=False
        ).exclude(
            Q(status='delivered') | Q(status='cancelled') | Q(status='refunded')
        ).select_related('merchant')[:limit]
        
        if not orders.exists():
            self.stdout.write(self.style.SUCCESS('No orders to track'))
            return
        
        self.stdout.write(f'Processing {orders.count()} orders...')
        
        shipdaak = ShipdaakService()
        updated_count = 0
        error_count = 0
        
        for order in orders:
            try:
                tracking_data = shipdaak.track_shipment(order.shipdaak_awb_number)
                
                if not tracking_data:
                    error_count += 1
                    continue
                
                # Update Shipdaak status
                shipdaak_status = tracking_data.get('status', '').lower()
                order.shipdaak_status = tracking_data.get('status')
                
                # Map Shipdaak status to order status
                status_mapping = {
                    'pending pickup': 'accepted',
                    'picked up': 'shipped',
                    'in transit': 'shipped',
                    'out for delivery': 'shipped',
                    'delivered': 'delivered',
                    'rto': 'cancelled',  # Handle RTO as cancelled
                    'cancelled': 'cancelled',
                }
                
                # Update order status based on Shipdaak status
                new_status = None
                for shipdaak_key, order_status in status_mapping.items():
                    if shipdaak_key in shipdaak_status:
                        new_status = order_status
                        break
                
                if new_status and new_status != order.status:
                    order.status = new_status
                    self.stdout.write(
                        f'Order {order.order_number}: Status updated to {new_status}'
                    )
                
                # Update dates from tracking data
                if tracking_data.get('pickupDate'):
                    try:
                        from datetime import datetime
                        pickup_date = datetime.fromisoformat(
                            tracking_data['pickupDate'].replace('Z', '+00:00')
                        )
                        if timezone.is_naive(pickup_date):
                            pickup_date = timezone.make_aware(pickup_date)
                        if not order.pickup_date:
                            order.pickup_date = pickup_date
                    except (ValueError, TypeError):
                        pass
                
                if tracking_data.get('deliveredDate'):
                    try:
                        from datetime import datetime
                        delivered_date = datetime.fromisoformat(
                            tracking_data['deliveredDate'].replace('Z', '+00:00')
                        )
                        if timezone.is_naive(delivered_date):
                            delivered_date = timezone.make_aware(delivered_date)
                        if not order.delivered_date:
                            order.delivered_date = delivered_date
                    except (ValueError, TypeError):
                        pass
                
                # Save order
                order.save()
                updated_count += 1
                
            except Exception as e:
                error_count += 1
                print(
                    f"[ERROR] Error updating tracking for order {order.order_number} "
                    f"(AWB: {order.shipdaak_awb_number}): {str(e)}"
                )
                traceback.print_exc()
                self.stdout.write(
                    self.style.ERROR(
                        f'Error processing order {order.order_number}: {str(e)}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully updated {updated_count} orders. '
                f'Errors: {error_count}'
            )
        )


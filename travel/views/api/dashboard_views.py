"""Travel dashboard API views"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from travel.models import (
    TravelCommittee, TravelCommitteeStaff, TravelDealer,
    TravelVehicle, TravelBooking, TravelVehicleSeat
)
from core.models import Agent, Transaction
from travel.utils import check_user_travel_role


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def travel_committee_dashboard(request):
    """Travel Committee dashboard with stats"""
    roles = check_user_travel_role(request.user)
    
    if not roles['is_travel_committee']:
        return Response({
            'error': 'User is not a Travel Committee member'
        }, status=status.HTTP_403_FORBIDDEN)
    
    committee = roles['committee']
    
    # Get date ranges
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Vehicle stats
    total_vehicles = TravelVehicle.objects.filter(committee=committee).count()
    active_vehicles = TravelVehicle.objects.filter(committee=committee, is_active=True).count()
    
    # Booking stats
    bookings = TravelBooking.objects.filter(vehicle__committee=committee)
    total_bookings = bookings.count()
    today_bookings = bookings.filter(created_at__date=today).count()
    week_bookings = bookings.filter(created_at__date__gte=week_ago).count()
    month_bookings = bookings.filter(created_at__date__gte=month_ago).count()
    pending_bookings = bookings.filter(status='pending').count()
    
    # Revenue stats (from transactions)
    revenue_transactions = Transaction.objects.filter(
        user=request.user,
        transaction_type='travel_booking_revenue',
        status='completed'
    )
    today_revenue = revenue_transactions.filter(created_at__date=today).aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0')
    week_revenue = revenue_transactions.filter(created_at__date__gte=week_ago).aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0')
    month_revenue = revenue_transactions.filter(created_at__date__gte=month_ago).aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0')
    
    # Staff stats
    active_staff = TravelCommitteeStaff.objects.filter(travel_committee=committee).count()
    
    # Occupancy rate (booked seats / total seats)
    total_seats = TravelVehicleSeat.objects.filter(vehicle__committee=committee).count()
    booked_seats = TravelVehicleSeat.objects.filter(
        vehicle__committee=committee,
        status__in=['booked', 'boarded']
    ).count()
    occupancy_rate = (booked_seats / total_seats * 100) if total_seats > 0 else 0
    
    # Wallet balance
    balance = Decimal(str(request.user.balance))
    
    return Response({
        'committee': {
            'id': committee.id,
            'name': committee.name,
            'logo': request.build_absolute_uri(committee.logo.url) if committee.logo else None,
        },
        'stats': {
            'vehicles': {
                'total': total_vehicles,
                'active': active_vehicles,
                'inactive': total_vehicles - active_vehicles,
            },
            'bookings': {
                'total': total_bookings,
                'today': today_bookings,
                'week': week_bookings,
                'month': month_bookings,
                'pending': pending_bookings,
            },
            'revenue': {
                'today': float(today_revenue),
                'week': float(week_revenue),
                'month': float(month_revenue),
            },
            'staff': {
                'active': active_staff,
            },
            'occupancy_rate': round(occupancy_rate, 2),
            'balance': float(balance),
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def travel_staff_dashboard(request):
    """Travel Committee Staff dashboard with permission-based stats"""
    roles = check_user_travel_role(request.user)
    
    if not roles['is_travel_staff']:
        return Response({
            'error': 'User is not a Travel Committee Staff member'
        }, status=status.HTTP_403_FORBIDDEN)
    
    staff = roles['staff']
    committee = staff.travel_committee
    
    today = timezone.now().date()
    
    # Permission-based widgets
    widgets = {}
    
    # Booking permission
    if staff.booking_permission:
        today_bookings = TravelBooking.objects.filter(
            vehicle__committee=committee,
            created_at__date=today
        ).count()
        pending_count = TravelBooking.objects.filter(
            vehicle__committee=committee,
            status='pending'
        ).count()
        widgets['booking'] = {
            'today_bookings': today_bookings,
            'pending_count': pending_count,
        }
    
    # Boarding permission
    if staff.boarding_permission:
        boarding_queue = TravelBooking.objects.filter(
            vehicle__committee=committee,
            status='booked'
        ).count()
        widgets['boarding'] = {
            'queue_count': boarding_queue,
        }
    
    # Finance permission
    if staff.finance_permission:
        today_revenue = Transaction.objects.filter(
            user=request.user,
            transaction_type='travel_booking_revenue',
            status='completed',
            created_at__date=today
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        widgets['finance'] = {
            'today_revenue': float(today_revenue),
        }
    
    return Response({
        'staff': {
            'id': staff.id,
            'permissions': {
                'booking': staff.booking_permission,
                'boarding': staff.boarding_permission,
                'finance': staff.finance_permission,
            }
        },
        'committee': {
            'id': committee.id,
            'name': committee.name,
        },
        'widgets': widgets,
        'balance': float(Decimal(str(request.user.balance))),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def travel_dealer_dashboard(request):
    """Travel Dealer dashboard with stats"""
    roles = check_user_travel_role(request.user)
    
    if not roles['is_travel_dealer']:
        return Response({
            'error': 'User is not a Travel Dealer'
        }, status=status.HTTP_403_FORBIDDEN)
    
    dealer = roles['dealer']
    
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Agent stats
    agents = Agent.objects.filter(dealer=dealer)
    total_agents = agents.count()
    active_agents = agents.filter(is_active=True).count()
    
    # Booking stats (from agents)
    bookings = TravelBooking.objects.filter(agent__dealer=dealer)
    total_bookings = bookings.count()
    today_bookings = bookings.filter(created_at__date=today).count()
    week_bookings = bookings.filter(created_at__date__gte=week_ago).count()
    month_bookings = bookings.filter(created_at__date__gte=month_ago).count()
    
    # Revenue stats
    revenue_transactions = Transaction.objects.filter(
        user=request.user,
        transaction_type='travel_booking_revenue',
        status='completed'
    )
    total_revenue = revenue_transactions.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    today_revenue = revenue_transactions.filter(created_at__date=today).aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0')
    month_revenue = revenue_transactions.filter(created_at__date__gte=month_ago).aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0')
    
    # Top performing agents
    top_agents = agents.annotate(
        booking_count=Count('bookings')
    ).order_by('-booking_count')[:5]
    
    return Response({
        'dealer': {
            'id': dealer.id,
            'commission_type': dealer.commission_type,
        },
        'stats': {
            'agents': {
                'total': total_agents,
                'active': active_agents,
                'inactive': total_agents - active_agents,
            },
            'bookings': {
                'total': total_bookings,
                'today': today_bookings,
                'week': week_bookings,
                'month': month_bookings,
            },
            'revenue': {
                'total': float(total_revenue),
                'today': float(today_revenue),
                'month': float(month_revenue),
            },
            'top_agents': [
                {
                    'id': agent.id,
                    'name': agent.user.name,
                    'booking_count': agent.booking_count,
                }
                for agent in top_agents
            ],
        },
        'balance': float(Decimal(str(request.user.balance))),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def agent_dashboard(request):
    """Agent dashboard with stats"""
    roles = check_user_travel_role(request.user)
    
    if not roles['is_agent']:
        return Response({
            'error': 'User is not an Agent'
        }, status=status.HTTP_403_FORBIDDEN)
    
    agent = roles['agent']
    
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Booking stats
    bookings = TravelBooking.objects.filter(agent=agent)
    total_bookings = bookings.count()
    today_bookings = bookings.filter(created_at__date=today).count()
    week_bookings = bookings.filter(created_at__date__gte=week_ago).count()
    month_bookings = bookings.filter(created_at__date__gte=month_ago).count()
    pending_bookings = bookings.filter(status='pending').count()
    
    # Revenue stats
    revenue_transactions = Transaction.objects.filter(
        user=request.user,
        transaction_type='travel_booking_revenue',
        status='completed'
    )
    total_revenue = revenue_transactions.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    # Available committees
    committees = agent.committees.filter(is_active=True)
    
    return Response({
        'agent': {
            'id': agent.id,
            'dealer': {
                'id': agent.dealer.id,
                'name': agent.dealer.user.name,
            } if agent.dealer else None,
        },
        'stats': {
            'bookings': {
                'total': total_bookings,
                'today': today_bookings,
                'week': week_bookings,
                'month': month_bookings,
                'pending': pending_bookings,
            },
            'revenue': {
                'total': float(total_revenue),
            },
            'committees': [
                {
                    'id': committee.id,
                    'name': committee.name,
                }
                for committee in committees
            ],
        },
        'balance': float(Decimal(str(request.user.balance))),
    })

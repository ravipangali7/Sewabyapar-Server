"""Travel API and domain tests."""
from decimal import Decimal
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

from core.models import User, Agent, SuperSetting, Transaction
from core.utils.role_helpers import can_use_merchant_wallet_services
from shared.models import Place
from travel.models import (
    TravelCommittee,
    TravelCommitteeStaff,
    TravelDealer,
    TravelVehicle,
    TravelVehicleSeat,
    TravelBooking,
)


class TravelSetupMixin:
    """Shared fixtures for travel tests."""

    @classmethod
    def _create_user(cls, phone_suffix, name):
        return User.objects.create_user(
            phone=f'980000{phone_suffix}',
            name=name,
            password='testpass123',
        )

    @classmethod
    def setUpTestData(cls):
        cls.place_a = Place.objects.create(name='PlaceA')
        cls.place_b = Place.objects.create(name='PlaceB')
        cls.committee_user = cls._create_user('0001', 'Committee Owner')
        cls.committee = TravelCommittee.objects.create(
            user=cls.committee_user,
            name='Test Committee',
        )
        cls.vehicle = TravelVehicle.objects.create(
            name='Bus 1',
            vehicle_no='TEST-BUS-001',
            committee=cls.committee,
            from_place=cls.place_a,
            to_place=cls.place_b,
            departure_time='09:00:00',
            actual_seat_price=Decimal('80.00'),
            seat_price=Decimal('100.00'),
        )
        cls.seat1 = TravelVehicleSeat.objects.create(
            vehicle=cls.vehicle, side='A', number=1, floor='lower', status='available',
        )
        cls.seat2 = TravelVehicleSeat.objects.create(
            vehicle=cls.vehicle, side='A', number=2, floor='lower', status='available',
        )
        cls.staff_user = cls._create_user('0002', 'Staff User')
        TravelCommitteeStaff.objects.create(
            user=cls.staff_user,
            travel_committee=cls.committee,
            booking_permission=True,
            boarding_permission=True,
        )
        cls.dealer_user = cls._create_user('0003', 'Dealer')
        cls.dealer = TravelDealer.objects.create(
            user=cls.dealer_user,
            commission_type='percentage',
            commission_value=Decimal('10'),
        )
        cls.agent_user = cls._create_user('0004', 'Agent User')
        cls.agent = Agent.objects.create(
            user=cls.agent_user,
            dealer=cls.dealer,
            commission_type='percentage',
            commission_value=Decimal('10'),
        )
        cls.agent.committees.add(cls.committee)
        if not SuperSetting.objects.exists():
            SuperSetting.objects.create()


class TravelBookingApiTests(TravelSetupMixin, TestCase):
    def setUp(self):
        self.client = APIClient()
        self.tomorrow = (timezone.now() + timedelta(days=1)).replace(
            hour=10, minute=0, second=0, microsecond=0,
        )

    def _auth(self, user):
        token, _ = Token.objects.get_or_create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

    def test_multi_seat_create_distinct_tickets_and_ticket_price(self):
        self._auth(self.staff_user)
        payload = {
            'name': 'Passenger',
            'phone': '111',
            'gender': 'male',
            'vehicle': self.vehicle.id,
            'seat_ids': [self.seat1.id, self.seat2.id],
            'booking_date': self.tomorrow.isoformat(),
        }
        r = self.client.post('/api/travel/bookings/create/', payload, format='json')
        self.assertEqual(r.status_code, 201, r.content)
        data = r.json()
        self.assertEqual(len(data), 2)
        self.assertNotEqual(data[0]['ticket_number'], data[1]['ticket_number'])
        self.assertEqual(Decimal(str(data[0]['ticket_price'])), Decimal('100.00'))

    def test_reset_requires_confirm(self):
        self._auth(self.committee_user)
        r = self.client.post(
            f'/api/travel/vehicles/{self.vehicle.id}/reset-seats/',
            {},
            format='json',
        )
        self.assertEqual(r.status_code, 400)

    def test_reset_clears_boarded_seat_for_date(self):
        self._auth(self.staff_user)
        booking_date = timezone.now().replace(hour=8, minute=0, second=0, microsecond=0)
        r = self.client.post(
            '/api/travel/bookings/create/',
            {
                'name': 'P',
                'phone': '222',
                'gender': 'male',
                'vehicle': self.vehicle.id,
                'seat_ids': [self.seat1.id],
                'booking_date': booking_date.isoformat(),
            },
            format='json',
        )
        self.assertEqual(r.status_code, 201, r.content)
        booking_id = r.json()[0]['id']
        self._auth(self.staff_user)
        r2 = self.client.post(
            f'/api/travel/boarding/{booking_id}/confirm/',
            {},
            format='json',
        )
        self.assertEqual(r2.status_code, 200, r2.content)
        self.seat1.refresh_from_db()
        self.assertEqual(self.seat1.status, 'boarded')

        self._auth(self.committee_user)
        r3 = self.client.post(
            f'/api/travel/vehicles/{self.vehicle.id}/reset-seats/',
            {
                'confirm': True,
                'booking_date': booking_date.date().isoformat(),
            },
            format='json',
        )
        self.assertEqual(r3.status_code, 200, r3.content)
        self.seat1.refresh_from_db()
        self.assertEqual(self.seat1.status, 'available')

    def test_available_seats_ignores_stale_seat_row_without_booking(self):
        self.seat1.status = 'booked'
        self.seat1.save(update_fields=['status'])
        self._auth(self.agent_user)
        url = f'/api/travel/vehicles/{self.vehicle.id}/available-seats/'
        r = self.client.get(url, {'date': self.tomorrow.isoformat()})
        self.assertEqual(r.status_code, 200, r.content)
        rows = {s['id']: s for s in r.json()}
        self.assertEqual(rows[self.seat1.id]['status'], 'available')

    def test_patch_boarded_forbidden(self):
        self._auth(self.staff_user)
        booking_date = self.tomorrow
        r = self.client.post(
            '/api/travel/bookings/create/',
            {
                'name': 'P',
                'phone': '333',
                'gender': 'male',
                'vehicle': self.vehicle.id,
                'seat_ids': [self.seat1.id],
                'booking_date': booking_date.isoformat(),
            },
            format='json',
        )
        booking_id = r.json()[0]['id']
        self._auth(self.committee_user)
        pr = self.client.patch(
            f'/api/travel/bookings/{booking_id}/',
            {'status': 'boarded'},
            format='json',
        )
        self.assertEqual(pr.status_code, 400)

    def test_agent_vehicle_list_hides_actual_seat_price(self):
        self._auth(self.agent_user)
        r = self.client.get('/api/travel/vehicles/')
        self.assertEqual(r.status_code, 200)
        row = next(x for x in r.json() if x['id'] == self.vehicle.id)
        self.assertNotIn('actual_seat_price', row)
        self.assertEqual(Decimal(str(row['seat_price'])), Decimal('100.00'))

    def test_confirm_boarding_creates_revenue_transaction(self):
        self._auth(self.agent_user)
        booking_date = timezone.now().replace(hour=8, minute=0, second=0, microsecond=0)
        r = self.client.post(
            '/api/travel/bookings/create/',
            {
                'name': 'P',
                'phone': '444',
                'gender': 'male',
                'vehicle': self.vehicle.id,
                'seat_ids': [self.seat1.id],
                'booking_date': booking_date.isoformat(),
            },
            format='json',
        )
        self.assertEqual(r.status_code, 201, r.content)
        booking_id = r.json()[0]['id']

        self._auth(self.staff_user)
        r2 = self.client.post(f'/api/travel/boarding/{booking_id}/confirm/', {}, format='json')
        self.assertEqual(r2.status_code, 200, r2.content)

        booking = TravelBooking.objects.get(pk=booking_id)
        self.assertTrue(booking.commission_distributed)
        self.assertTrue(
            Transaction.objects.filter(
                related_travel_booking=booking,
                transaction_type='travel_booking_revenue',
                user=self.committee_user,
            ).exists()
        )

    def test_boarding_screen_defaults_to_today(self):
        self._auth(self.staff_user)
        booking_date = timezone.now().replace(hour=8, minute=0, second=0, microsecond=0)
        self.client.post(
            '/api/travel/bookings/create/',
            {
                'name': 'P',
                'phone': '555',
                'gender': 'male',
                'vehicle': self.vehicle.id,
                'seat_ids': [self.seat2.id],
                'booking_date': booking_date.isoformat(),
            },
            format='json',
        )
        r = self.client.get('/api/travel/boarding/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()), 1)

    def test_staff_wallet_services_allowed(self):
        self.assertTrue(can_use_merchant_wallet_services(self.staff_user))


class TravelCommissionPoolTests(TravelSetupMixin, TestCase):
    def test_calculate_commissions_raises_when_pool_exceeded(self):
        self.dealer.commission_type = 'percentage'
        self.dealer.commission_value = Decimal('90')
        self.dealer.save()
        self.agent.commission_type = 'percentage'
        self.agent.commission_value = Decimal('90')
        self.agent.save()

        booking = TravelBooking(
            name='X',
            phone='1',
            gender='male',
            vehicle=self.vehicle,
            vehicle_seat=self.seat1,
            booking_date=timezone.now(),
            status='booked',
            actual_price=self.vehicle.actual_seat_price,
            agent=self.agent,
        )
        from travel.utils import calculate_travel_commissions

        with self.assertRaises(ValueError):
            calculate_travel_commissions(booking)

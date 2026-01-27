"""Travel app utility functions"""
from django.utils import timezone
from datetime import datetime, date
from decimal import Decimal
from travel.models import TravelCommittee, TravelCommitteeStaff, TravelDealer, TravelBooking, TravelVehicle
from core.models import Agent


def check_user_travel_role(user):
    """Check user's travel roles and return role dictionary"""
    roles = {
        'is_travel_committee': False,
        'is_travel_staff': False,
        'is_travel_dealer': False,
        'is_agent': False,
        'committee': None,
        'staff': None,
        'dealer': None,
        'agent': None,
    }
    
    # Check Travel Committee
    committee = TravelCommittee.objects.filter(user=user, is_active=True).first()
    if committee:
        roles['is_travel_committee'] = True
        roles['committee'] = committee
    
    # Check Travel Committee Staff
    staff = TravelCommitteeStaff.objects.filter(user=user).first()
    if staff:
        roles['is_travel_staff'] = True
        roles['staff'] = staff
    
    # Check Travel Dealer
    dealer = TravelDealer.objects.filter(user=user, is_active=True).first()
    if dealer:
        roles['is_travel_dealer'] = True
        roles['dealer'] = dealer
    
    # Check Agent
    agent = Agent.objects.filter(user=user, is_active=True).first()
    if agent:
        roles['is_agent'] = True
        roles['agent'] = agent
    
    return roles


def calculate_travel_commissions(booking):
    """Calculate dealer/agent/system commissions for a booking"""
    from decimal import Decimal, ROUND_HALF_UP
    
    if not booking.vehicle:
        return
    
    # System commission
    system_commission = Decimal(str(booking.vehicle.seat_price)) - Decimal(str(booking.vehicle.actual_seat_price))
    system_commission = system_commission.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    booking.system_commission = system_commission
    
    # Dealer commission
    dealer_commission = Decimal('0')
    if booking.agent and booking.agent.dealer:
        dealer = booking.agent.dealer
        if dealer.commission_type == 'flat':
            dealer_commission = Decimal(str(dealer.commission_value))
        else:  # percentage
            dealer_commission = system_commission * (Decimal(str(dealer.commission_value)) / Decimal('100'))
        dealer_commission = dealer_commission.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    booking.dealer_commission = dealer_commission
    
    # Agent commission
    agent_commission = Decimal('0')
    if booking.agent:
        if booking.agent.commission_type == 'flat':
            agent_commission = Decimal(str(booking.agent.commission_value))
        else:  # percentage
            agent_commission = system_commission * (Decimal(str(booking.agent.commission_value)) / Decimal('100'))
        agent_commission = agent_commission.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    booking.agent_commission = agent_commission
    
    return {
        'system_commission': system_commission,
        'dealer_commission': dealer_commission,
        'agent_commission': agent_commission,
    }


def validate_booking_date(vehicle, booking_date):
    """Validate booking date - must be today or future"""
    if isinstance(booking_date, str):
        booking_date = datetime.fromisoformat(booking_date.replace('Z', '+00:00'))
    
    if isinstance(booking_date, datetime):
        booking_date = booking_date.date()
    
    today = timezone.now().date()
    
    if booking_date < today:
        return False, "Booking date cannot be in the past"
    
    return True, None


def generate_ticket_pdf(booking):
    """Generate PDF ticket with QR code"""
    # Import here to avoid dependency issues if packages aren't installed
    import io
    import qrcode
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader
    from PIL import Image
    
    # Create PDF buffer
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Get committee info
    committee = booking.vehicle.committee
    
    # Header with logo and committee name
    if committee.logo:
        try:
            logo_path = committee.logo.path
            logo_img = Image.open(logo_path)
            logo_img.thumbnail((100, 100), Image.Resampling.LANCZOS)
            logo_reader = ImageReader(logo_img)
            c.drawImage(logo_reader, width - 120, height - 100, width=100, height=100)
        except:
            pass
    
    # Committee name
    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, height - 50, committee.name)
    
    # Ticket number (prominent)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(50, height - 100, f"Ticket Number: {booking.ticket_number}")
    
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(booking.qr_code or booking.ticket_number)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert QR to ImageReader
    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)
    qr_reader = ImageReader(qr_buffer)
    
    # Draw QR code (right side)
    qr_size = 150
    c.drawImage(qr_reader, width - 200, height - 280, width=qr_size, height=qr_size)
    
    # Customer details
    y_pos = height - 200
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y_pos, "Passenger Details:")
    y_pos -= 25
    
    c.setFont("Helvetica", 12)
    c.drawString(50, y_pos, f"Name: {booking.name}")
    y_pos -= 20
    c.drawString(50, y_pos, f"Phone: {booking.phone}")
    y_pos -= 20
    c.drawString(50, y_pos, f"Gender: {booking.get_gender_display()}")
    if booking.nationality:
        y_pos -= 20
        c.drawString(50, y_pos, f"Nationality: {booking.nationality}")
    
    # Vehicle and seat info
    y_pos -= 40
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y_pos, "Journey Details:")
    y_pos -= 25
    
    c.setFont("Helvetica", 12)
    c.drawString(50, y_pos, f"Vehicle: {booking.vehicle.name} ({booking.vehicle.vehicle_no})")
    y_pos -= 20
    c.drawString(50, y_pos, f"Route: {booking.vehicle.from_place.name} → {booking.vehicle.to_place.name}")
    y_pos -= 20
    c.drawString(50, y_pos, f"Seat: {booking.vehicle_seat.side}{booking.vehicle_seat.number} ({booking.vehicle_seat.get_floor_display()})")
    y_pos -= 20
    c.drawString(50, y_pos, f"Departure Time: {booking.vehicle.departure_time.strftime('%I:%M %p')}")
    y_pos -= 20
    c.drawString(50, y_pos, f"Booking Date: {booking.booking_date.strftime('%Y-%m-%d %I:%M %p')}")
    
    # Price
    y_pos -= 40
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y_pos, f"Amount Paid: ₹{booking.vehicle.seat_price}")
    
    # Footer
    c.setFont("Helvetica", 10)
    c.drawString(50, 50, "Thank you for choosing our service!")
    c.drawString(50, 35, "Please arrive 15 minutes before departure time.")
    
    # Save PDF
    c.save()
    buffer.seek(0)
    return buffer.getvalue()

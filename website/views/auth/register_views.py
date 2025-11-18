from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.conf import settings as django_settings
import random
from core.models import User, Otp
from core.utils.sms_service import sms_service
from website.models import MySetting, CMSPages


def generate_otp():
    """Generate 6-digit OTP"""
    return str(random.randint(100000, 999999))


def send_otp_view(request):
    """Send OTP for registration"""
    if request.user.is_authenticated:
        return redirect('website:dashboard')
    
    if request.method == 'POST':
        phone = request.POST.get('phone', '').strip()
        country_code = request.POST.get('country_code', '+91')
        country = request.POST.get('country', 'India')
        
        # Validation
        if not phone or len(phone) < 10:
            messages.error(request, 'Please enter a valid phone number.')
            return redirect('website:register')
        
        # Check if user already exists
        if User.objects.filter(phone=phone).exists():
            messages.error(request, 'Phone number already registered.')
            return redirect('website:register')
        
        # Validate country and country_code match
        if country_code == '+977' and country != 'Nepal':
            messages.error(request, 'Country must be Nepal when country code is +977')
            return redirect('website:register')
        if country_code == '+91' and country != 'India':
            messages.error(request, 'Country must be India when country code is +91')
            return redirect('website:register')
        
        # Generate OTP
        otp = generate_otp()
        
        # Delete any existing OTP for this phone
        Otp.objects.filter(phone=phone, country_code=country_code).delete()
        
        # Create new OTP with expiration
        expires_at = timezone.now() + timedelta(minutes=getattr(django_settings, 'OTP_EXPIRY_MINUTES', 10))
        Otp.objects.create(
            phone=phone,
            otp=otp,
            country_code=country_code,
            expires_at=expires_at
        )
        
        # Send SMS based on country code
        if country_code == '+91':
            # India: Send SMS via Fast2SMS
            sms_result = sms_service.send_otp(phone, otp, country_code)
            if sms_result['success']:
                # Store in session for next step
                request.session['reg_phone'] = phone
                request.session['reg_country_code'] = country_code
                request.session['reg_country'] = country
                messages.success(request, 'OTP sent successfully to your phone number')
            else:
                messages.error(request, f"Failed to send SMS: {sms_result.get('message', 'Unknown error')}")
                return redirect('website:register')
        elif country_code == '+977':
            # Nepal: Send SMS via Kaicho Group API
            sms_result = sms_service.send_otp(phone, otp, country_code)
            if sms_result['success']:
                # Store in session for next step
                request.session['reg_phone'] = phone
                request.session['reg_country_code'] = country_code
                request.session['reg_country'] = country
                messages.success(request, 'OTP sent successfully to your phone number')
            else:
                messages.error(request, f"Failed to send SMS: {sms_result.get('message', 'Unknown error')}")
                return redirect('website:register')
        else:
            messages.error(request, 'Invalid country code')
            return redirect('website:register')
        
        return redirect('website:register')
    
    return redirect('website:register')


def register_view(request):
    """User registration page with OTP verification"""
    if request.user.is_authenticated:
        return redirect('website:dashboard')
    
    try:
        settings = MySetting.objects.first()
    except MySetting.DoesNotExist:
        settings = None
    
    menu_pages = CMSPages.objects.filter(on_menu=True)
    footer_pages = CMSPages.objects.filter(on_footer=True)
    
    # Handle reset - clear session and go back to step 1
    if request.GET.get('reset') == '1':
        request.session.pop('reg_phone', None)
        request.session.pop('reg_country_code', None)
        request.session.pop('reg_country', None)
        messages.info(request, 'Please enter your phone number again.')
        return redirect('website:register')
    
    # Check if OTP has been sent (step 2)
    otp_sent = 'reg_phone' in request.session
    
    if request.method == 'POST':
        # Check if this is OTP verification step
        if 'otp' in request.POST:
            # Step 2: Verify OTP and create account
            otp = request.POST.get('otp', '').strip()
            name = request.POST.get('name', '').strip()
            email = request.POST.get('email', '').strip() or None
            password = request.POST.get('password', '')
            confirm_password = request.POST.get('confirm_password', '')
            
            # Get phone, country_code, country from session
            phone = request.session.get('reg_phone', '')
            country_code = request.session.get('reg_country_code', '+91')
            country = request.session.get('reg_country', 'India')
            
            # Validation
            if not all([phone, name, password, otp]):
                messages.error(request, 'All fields are required.')
            elif password != confirm_password:
                messages.error(request, 'Passwords do not match.')
            elif len(otp) != 6 or not otp.isdigit():
                messages.error(request, 'OTP must be a 6-digit number.')
            else:
                # Verify OTP
                try:
                    otp_record = Otp.objects.get(phone=phone, otp=otp, country_code=country_code)
                    if otp_record.is_expired():
                        messages.error(request, 'OTP has expired. Please request a new one.')
                        # Clear session
                        request.session.pop('reg_phone', None)
                        request.session.pop('reg_country_code', None)
                        request.session.pop('reg_country', None)
                    else:
                        # OTP is valid, create user
                        try:
                            user = User.objects.create_user(
                                phone=phone,
                                name=name,
                                email=email,
                                password=password,
                                country_code=country_code,
                                country=country,
                            )
                            # Delete OTP after successful registration
                            otp_record.delete()
                            
                            # Clear session
                            request.session.pop('reg_phone', None)
                            request.session.pop('reg_country_code', None)
                            request.session.pop('reg_country', None)
                            
                            login(request, user)
                            messages.success(request, 'Registration successful!')
                            return redirect('website:dashboard')
                        except Exception as e:
                            messages.error(request, f'Registration failed: {str(e)}')
                except Otp.DoesNotExist:
                    messages.error(request, 'Invalid OTP code.')
        else:
            # This should not happen, redirect to step 1
            return redirect('website:register')
    
    context = {
        'settings': settings,
        'menu_pages': menu_pages,
        'footer_pages': footer_pages,
        'otp_sent': otp_sent,
        'phone': request.session.get('reg_phone', ''),
        'country_code': request.session.get('reg_country_code', '+91'),
        'country': request.session.get('reg_country', 'India'),
    }
    
    return render(request, 'website/auth/register.html', context)


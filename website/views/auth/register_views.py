from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from core.models import User
from website.models import MySetting, CMSPages


def register_view(request):
    """User registration page"""
    if request.user.is_authenticated:
        return redirect('website:shop')
    
    try:
        settings = MySetting.objects.first()
    except MySetting.DoesNotExist:
        settings = None
    
    menu_pages = CMSPages.objects.filter(on_menu=True)
    footer_pages = CMSPages.objects.filter(on_footer=True)
    
    if request.method == 'POST':
        phone = request.POST.get('phone', '').strip()
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip() or None
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        country_code = request.POST.get('country_code', '+977')
        country = request.POST.get('country', 'Nepal')
        
        # Validation
        if not all([phone, name, password]):
            messages.error(request, 'Phone, name, and password are required.')
        elif password != confirm_password:
            messages.error(request, 'Passwords do not match.')
        elif User.objects.filter(phone=phone).exists():
            messages.error(request, 'Phone number already registered.')
        else:
            try:
                user = User.objects.create_user(
                    phone=phone,
                    name=name,
                    email=email,
                    password=password,
                    country_code=country_code,
                    country=country,
                )
                login(request, user)
                messages.success(request, 'Registration successful!')
                return redirect('website:shop')
            except Exception as e:
                messages.error(request, f'Registration failed: {str(e)}')
    
    context = {
        'settings': settings,
        'menu_pages': menu_pages,
        'footer_pages': footer_pages,
    }
    
    return render(request, 'website/auth/register.html', context)


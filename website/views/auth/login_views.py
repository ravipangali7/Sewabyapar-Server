from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from core.models import User
from website.models import MySetting, CMSPages


def login_view(request):
    """User login page"""
    if request.user.is_authenticated:
        return redirect('website:dashboard')
    
    try:
        settings = MySetting.objects.first()
    except MySetting.DoesNotExist:
        settings = None
    
    menu_pages = CMSPages.objects.filter(on_menu=True)
    footer_pages = CMSPages.objects.filter(on_footer=True)
    
    if request.method == 'POST':
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '')
        country_code = request.POST.get('country_code', '+91')
        
        if phone and password and country_code:
            # First, check if user exists with the given phone number
            try:
                user = User.objects.get(phone=phone)
            except User.DoesNotExist:
                messages.error(request, 'Invalid phone number or password.')
                context = {
                    'settings': settings,
                    'menu_pages': menu_pages,
                    'footer_pages': footer_pages,
                }
                return render(request, 'website/auth/login.html', context)
            
            # Check if the provided country_code matches the user's registered country_code
            if user.country_code != country_code:
                messages.error(request, 'This phone number is not registered with the selected country code.')
                context = {
                    'settings': settings,
                    'menu_pages': menu_pages,
                    'footer_pages': footer_pages,
                }
                return render(request, 'website/auth/login.html', context)
            
            # If country code matches, authenticate with password
            user = authenticate(request, username=phone, password=password)
            if user is not None:
                login(request, user)
                next_url = request.GET.get('next', 'website:dashboard')
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid phone number or password.')
        else:
            messages.error(request, 'Please provide phone number, country code, and password.')
    
    context = {
        'settings': settings,
        'menu_pages': menu_pages,
        'footer_pages': footer_pages,
    }
    
    return render(request, 'website/auth/login.html', context)


@login_required
def logout_view(request):
    """User logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('website:home')


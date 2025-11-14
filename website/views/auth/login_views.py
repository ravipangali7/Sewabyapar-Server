from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from website.models import MySetting, CMSPages


def login_view(request):
    """User login page"""
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
        password = request.POST.get('password', '')
        
        if phone and password:
            user = authenticate(request, username=phone, password=password)
            if user is not None:
                login(request, user)
                next_url = request.GET.get('next', 'website:shop')
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid phone number or password.')
        else:
            messages.error(request, 'Please provide both phone number and password.')
    
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


from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from core.models import User
from website.models import MySetting, CMSPages


def reset_password_view(request):
    """Reset password page"""
    if request.user.is_authenticated:
        return redirect('website:shop')
    
    try:
        settings = MySetting.objects.first()
    except MySetting.DoesNotExist:
        settings = None
    
    menu_pages = CMSPages.objects.filter(on_menu=True)
    footer_pages = CMSPages.objects.filter(on_footer=True)
    
    phone = request.GET.get('phone', '')
    otp = request.GET.get('otp', '')
    
    if request.method == 'POST':
        phone = request.POST.get('phone', '').strip()
        otp = request.POST.get('otp', '').strip()
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')
        
        # Validation
        if not all([phone, otp, new_password, confirm_password]):
            messages.error(request, 'All fields are required.')
        elif new_password != confirm_password:
            messages.error(request, 'Passwords do not match.')
        else:
            # Here you would verify OTP
            # For now, just update password if user exists
            try:
                user = User.objects.get(phone=phone)
                user.set_password(new_password)
                user.save()
                login(request, user)
                messages.success(request, 'Password reset successful!')
                return redirect('website:shop')
            except User.DoesNotExist:
                messages.error(request, 'Invalid phone number.')
    
    context = {
        'settings': settings,
        'menu_pages': menu_pages,
        'footer_pages': footer_pages,
        'phone': phone,
        'otp': otp,
    }
    
    return render(request, 'website/auth/reset_password.html', context)


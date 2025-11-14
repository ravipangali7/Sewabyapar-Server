from django.shortcuts import render, redirect
from django.contrib import messages
from website.models import MySetting, CMSPages


def forgot_password_view(request):
    """Forgot password page"""
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
        # Here you would typically send OTP via SMS
        # For now, just show a message
        if phone:
            messages.info(request, 'If this phone number is registered, you will receive an OTP shortly.')
        else:
            messages.error(request, 'Please provide your phone number.')
    
    context = {
        'settings': settings,
        'menu_pages': menu_pages,
        'footer_pages': footer_pages,
    }
    
    return render(request, 'website/auth/forgot_password.html', context)


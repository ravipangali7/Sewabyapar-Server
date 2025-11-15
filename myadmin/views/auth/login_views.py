"""
Admin login views
"""
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache


@never_cache
@require_http_methods(["GET", "POST"])
def admin_login(request):
    """Admin login view"""
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('myadmin:dashboard')
    
    if request.method == 'POST':
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        
        if phone and password:
            user = authenticate(request, username=phone, password=password)
            if user is not None:
                if user.is_staff:
                    login(request, user)
                    messages.success(request, f'Welcome back, {user.name}!')
                    next_url = request.GET.get('next')
                    if next_url:
                        return redirect(next_url)
                    return redirect('myadmin:dashboard')
                else:
                    messages.error(request, 'You do not have permission to access the admin panel.')
            else:
                messages.error(request, 'Invalid phone number or password.')
        else:
            messages.error(request, 'Please provide both phone number and password.')
    
    return render(request, 'admin/auth/login.html', {'next': request.GET.get('next', 'myadmin:dashboard')})


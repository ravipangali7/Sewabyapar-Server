from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from core.models import Address
from website.models import MySetting, CMSPages


@login_required
def addresses_view(request):
    """Address management page"""
    try:
        settings = MySetting.objects.first()
    except MySetting.DoesNotExist:
        settings = None
    
    menu_pages = CMSPages.objects.filter(on_menu=True)
    footer_pages = CMSPages.objects.filter(on_footer=True)
    
    addresses = Address.objects.filter(user=request.user).order_by('-is_default', '-created_at')
    
    if request.method == 'POST':
        # Add new address
        title = request.POST.get('title', '').strip()
        full_name = request.POST.get('full_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        zip_code = request.POST.get('zip_code', '').strip()
        is_default = request.POST.get('is_default') == 'on'
        
        if not all([title, full_name, phone, address, city, state, zip_code]):
            messages.error(request, 'All fields are required.')
        else:
            # If setting as default, unset other defaults
            if is_default:
                Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
            
            Address.objects.create(
                user=request.user,
                title=title,
                full_name=full_name,
                phone=phone,
                address=address,
                city=city,
                state=state,
                zip_code=zip_code,
                is_default=is_default,
            )
            messages.success(request, 'Address added successfully!')
            return redirect('website:addresses')
    
    context = {
        'settings': settings,
        'menu_pages': menu_pages,
        'footer_pages': footer_pages,
        'addresses': addresses,
    }
    
    return render(request, 'website/profile/addresses.html', context)


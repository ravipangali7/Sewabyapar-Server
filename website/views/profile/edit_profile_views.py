from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from website.models import MySetting, CMSPages


@login_required
def edit_profile_view(request):
    """Edit profile page"""
    try:
        settings = MySetting.objects.first()
    except MySetting.DoesNotExist:
        settings = None
    
    menu_pages = CMSPages.objects.filter(on_menu=True)
    footer_pages = CMSPages.objects.filter(on_footer=True)
    
    if request.method == 'POST':
        user = request.user
        user.name = request.POST.get('name', user.name)
        user.email = request.POST.get('email', user.email) or None
        user.country_code = request.POST.get('country_code', user.country_code)
        user.country = request.POST.get('country', user.country)
        
        # Handle profile picture
        if 'profile_picture' in request.FILES:
            user.profile_picture = request.FILES['profile_picture']
        
        try:
            user.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('website:profile')
        except Exception as e:
            messages.error(request, f'Error updating profile: {str(e)}')
    
    context = {
        'settings': settings,
        'menu_pages': menu_pages,
        'footer_pages': footer_pages,
        'user': request.user,
    }
    
    return render(request, 'website/profile/edit_profile.html', context)


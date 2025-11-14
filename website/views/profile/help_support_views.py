from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from website.models import MySetting, CMSPages


@login_required
def help_support_view(request):
    """Help and support page"""
    try:
        settings = MySetting.objects.first()
    except MySetting.DoesNotExist:
        settings = None
    
    menu_pages = CMSPages.objects.filter(on_menu=True)
    footer_pages = CMSPages.objects.filter(on_footer=True)
    
    context = {
        'settings': settings,
        'menu_pages': menu_pages,
        'footer_pages': footer_pages,
    }
    
    return render(request, 'website/profile/help_support.html', context)


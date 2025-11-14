from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from core.models import Notification
from website.models import MySetting, CMSPages


@login_required
def notifications_view(request):
    """Notifications list page"""
    try:
        settings = MySetting.objects.first()
    except MySetting.DoesNotExist:
        settings = None
    
    menu_pages = CMSPages.objects.filter(on_menu=True)
    footer_pages = CMSPages.objects.filter(on_footer=True)
    
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Mark as read if viewing
    if request.method == 'GET':
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    
    # Pagination
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'settings': settings,
        'menu_pages': menu_pages,
        'footer_pages': footer_pages,
        'notifications': page_obj,
    }
    
    return render(request, 'website/profile/notifications.html', context)


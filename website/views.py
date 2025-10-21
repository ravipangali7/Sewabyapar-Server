from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import MySetting, Services, CMSPages


def home_view(request):
    """Homepage view - single page website"""
    try:
        settings = MySetting.objects.first()
    except MySetting.DoesNotExist:
        settings = None
    
    services = Services.objects.all()
    menu_pages = CMSPages.objects.filter(on_menu=True)
    footer_pages = CMSPages.objects.filter(on_footer=True)
    
    context = {
        'settings': settings,
        'services': services,
        'menu_pages': menu_pages,
        'footer_pages': footer_pages,
    }
    
    return render(request, 'website/home.html', context)


def cms_page_view(request, slug):
    """Dynamic CMS page view"""
    page = get_object_or_404(CMSPages, slug=slug)
    
    try:
        settings = MySetting.objects.first()
    except MySetting.DoesNotExist:
        settings = None
    
    menu_pages = CMSPages.objects.filter(on_menu=True)
    footer_pages = CMSPages.objects.filter(on_footer=True)
    
    context = {
        'page': page,
        'settings': settings,
        'menu_pages': menu_pages,
        'footer_pages': footer_pages,
    }
    
    return render(request, 'website/cms_page.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def contact_form_view(request):
    """Handle contact form submission"""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()
        
        # Basic validation
        if not all([name, email, subject, message]):
            return JsonResponse({
                'success': False,
                'message': 'All fields are required.'
            })
        
        # Here you could save to database, send email, etc.
        # For now, just return success
        return JsonResponse({
            'success': True,
            'message': 'Thank you for your message. We will get back to you soon!'
        })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method.'
    })
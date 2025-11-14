from django.shortcuts import render
from ecommerce.models import Category
from website.models import MySetting, CMSPages


def categories_view(request):
    """Categories listing page"""
    try:
        settings = MySetting.objects.first()
    except MySetting.DoesNotExist:
        settings = None
    
    menu_pages = CMSPages.objects.filter(on_menu=True)
    footer_pages = CMSPages.objects.filter(on_footer=True)
    
    categories = Category.objects.filter(is_active=True, parent=None)
    
    context = {
        'settings': settings,
        'menu_pages': menu_pages,
        'footer_pages': footer_pages,
        'categories': categories,
    }
    
    return render(request, 'website/ecommerce/categories.html', context)


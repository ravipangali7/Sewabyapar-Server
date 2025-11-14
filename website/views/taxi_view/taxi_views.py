from django.shortcuts import render
from taxi.models import Trip, Vehicle
from shared.models import Place
from website.models import MySetting, CMSPages


def taxi_view(request):
    """Main taxi page"""
    try:
        settings = MySetting.objects.first()
    except MySetting.DoesNotExist:
        settings = None
    
    menu_pages = CMSPages.objects.filter(on_menu=True)
    footer_pages = CMSPages.objects.filter(on_footer=True)
    
    # Get available trips
    trips = Trip.objects.all()[:10]
    
    # Get places for dropdowns
    places = Place.objects.all().order_by('name')
    
    context = {
        'settings': settings,
        'menu_pages': menu_pages,
        'footer_pages': footer_pages,
        'trips': trips,
        'places': places,
    }
    
    return render(request, 'website/taxi/taxi.html', context)


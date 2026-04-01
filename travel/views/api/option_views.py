"""Travel form option API views."""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from shared.models import Place
from travel.models import TravelVehicle
from travel.utils import check_user_travel_role


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def vehicle_options(request):
    """Dropdown options for vehicles visible to current travel role."""
    roles = check_user_travel_role(request.user)
    if roles["is_travel_committee"]:
        queryset = TravelVehicle.objects.filter(committee=roles["committee"])
    elif roles["is_travel_staff"]:
        queryset = TravelVehicle.objects.filter(committee=roles["staff"].travel_committee)
    elif roles["is_agent"]:
        queryset = TravelVehicle.objects.filter(committee__in=roles["agent"].committees.filter(is_active=True), is_active=True)
    else:
        queryset = TravelVehicle.objects.filter(is_active=True)

    search = request.query_params.get("search")
    if search:
        queryset = queryset.filter(name__icontains=search)

    queryset = queryset.select_related("from_place", "to_place").order_by("name")[:200]
    data = [
        {
            "value": vehicle.id,
            "label": f"{vehicle.name} ({vehicle.vehicle_no})",
            "name": vehicle.name,
            "vehicle_no": vehicle.vehicle_no,
            "from_place": vehicle.from_place.name if vehicle.from_place else "",
            "to_place": vehicle.to_place.name if vehicle.to_place else "",
        }
        for vehicle in queryset
    ]
    return Response(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def place_options(request):
    """Dropdown options for places."""
    queryset = Place.objects.all()
    search = request.query_params.get("search")
    if search:
        queryset = queryset.filter(name__icontains=search)

    queryset = queryset.order_by("name")[:300]
    return Response([{"value": place.id, "label": place.name, "name": place.name} for place in queryset])


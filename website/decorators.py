from functools import wraps
from urllib.parse import urlencode

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse

from core.utils.role_helpers import get_user_primary_role, get_dashboard_path_for_user
from travel.utils import check_user_travel_role


def travel_role_required(expected_role):
    """Guard website travel pages by expected primary role."""

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            user = request.user
            if not user.is_authenticated:
                query = urlencode({"next": request.get_full_path()})
                return redirect(f"{reverse('website:login')}?{query}")

            roles = check_user_travel_role(user)
            allowed = {
                "travel_committee": roles["is_travel_committee"],
                "travel_staff": roles["is_travel_staff"],
                "travel_dealer": roles["is_travel_dealer"],
                "agent": roles["is_agent"],
            }
            primary = get_user_primary_role(user)
            # Hard route gating: only allow the dashboard that matches
            # the user's current primary role.
            if allowed.get(expected_role) and primary == expected_role:
                return view_func(request, *args, **kwargs)

            messages.warning(request, "Access restricted for this travel role page.")
            return redirect(get_dashboard_path_for_user(user))

        return _wrapped

    return decorator


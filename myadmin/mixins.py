"""
Common mixins for admin views
"""
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to require staff status for admin views"""
    
    def test_func(self):
        return self.request.user.is_staff
    
    def handle_no_permission(self):
        from django.shortcuts import redirect
        from django.contrib import messages
        if not self.request.user.is_authenticated:
            messages.error(self.request, 'Please login to access this page.')
            return redirect('myadmin:login')
        else:
            messages.error(self.request, 'You must be a staff member to access this page.')
            return redirect('myadmin:login')


def staff_required(view_func):
    """Decorator to require staff status"""
    decorated_view = login_required(
        user_passes_test(
            lambda u: u.is_staff,
            login_url='myadmin:login'
        )(view_func)
    )
    return decorated_view


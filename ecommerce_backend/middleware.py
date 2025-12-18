"""
Custom middleware for API CSRF exemption
"""
import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class ApiCsrfExemptMiddleware(MiddlewareMixin):
    """
    Middleware to exempt all /api/ routes from CSRF checks.
    This is necessary for token-based authentication used by mobile apps.
    """
    
    def process_request(self, request):
        # Exempt all API routes from CSRF
        if request.path.startswith('/api/'):
            setattr(request, '_dont_enforce_csrf_checks', True)
            # Also set CSRF_COOKIE_NEEDED to False for API routes
            setattr(request, 'csrf_cookie_needed', False)
        return None
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        # Additional check to ensure API routes are exempted
        if request.path.startswith('/api/'):
            setattr(request, '_dont_enforce_csrf_checks', True)
        return None

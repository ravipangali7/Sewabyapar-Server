"""
Custom middleware for API CSRF exemption
"""
from django.utils.deprecation import MiddlewareMixin


class ApiCsrfExemptMiddleware(MiddlewareMixin):
    """
    Middleware to exempt all /api/ routes from CSRF checks.
    This is necessary for token-based authentication used by mobile apps.
    """
    
    def process_request(self, request):
        # Exempt all API routes from CSRF
        if request.path.startswith('/api/'):
            setattr(request, '_dont_enforce_csrf_checks', True)
        return None

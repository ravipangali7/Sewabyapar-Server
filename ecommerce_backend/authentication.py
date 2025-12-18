"""
Custom authentication classes for Django REST Framework
"""
from rest_framework.authentication import TokenAuthentication
from rest_framework import exceptions


class CsrfExemptTokenAuthentication(TokenAuthentication):
    """
    Custom TokenAuthentication that explicitly exempts CSRF checks.
    This is necessary for mobile app API requests using token authentication.
    """
    
    def authenticate(self, request):
        """
        Authenticate the request and exempt from CSRF.
        """
        # Call parent authentication
        auth_result = super().authenticate(request)
        
        # If authentication succeeded, exempt from CSRF
        if auth_result is not None:
            # Mark request as CSRF exempt
            setattr(request, '_dont_enforce_csrf_checks', True)
            setattr(request, 'csrf_cookie_needed', False)
        
        return auth_result
    
    def enforce_csrf(self, request):
        """
        Override to disable CSRF enforcement for token authentication.
        """
        return  # Do not enforce CSRF for token-authenticated requests

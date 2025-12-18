"""
Custom authentication classes for Django REST Framework
"""
from rest_framework.authentication import TokenAuthentication


class CsrfExemptTokenAuthentication(TokenAuthentication):
    """
    Custom TokenAuthentication that explicitly exempts CSRF checks.
    This is necessary for mobile app API requests using token authentication.
    
    The parent TokenAuthentication class already handles:
    - No token provided: Returns None (allows IsAuthenticatedOrReadOnly to permit GET)
    - Invalid token: Raises AuthenticationFailed (proper 401 error)
    - Valid token: Returns (user, token) tuple
    
    This class only adds CSRF exemption for authenticated requests.
    """
    
    def authenticate(self, request):
        """
        Authenticate the request using parent class and exempt from CSRF when token is valid.
        """
        # Call parent authentication to validate token
        # This will return None if no token, raise AuthenticationFailed if invalid, 
        # or return (user, token) if valid
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

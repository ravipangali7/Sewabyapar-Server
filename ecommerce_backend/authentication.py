"""
Custom authentication classes for Django REST Framework
"""
from rest_framework.authentication import TokenAuthentication
from rest_framework import exceptions


class CsrfExemptTokenAuthentication(TokenAuthentication):
    """
    Custom TokenAuthentication that explicitly exempts CSRF checks.
    This is necessary for mobile app API requests using token authentication.
    
    This class properly handles:
    - No token provided: Returns None (allows IsAuthenticatedOrReadOnly to permit GET)
    - Invalid token: Returns None (allows permission class to handle)
    - Valid token: Authenticates and exempts CSRF
    """
    
    def authenticate(self, request):
        """
        Authenticate the request and exempt from CSRF when token is valid.
        Returns None when no token is provided, allowing unauthenticated read requests.
        """
        # Check if Authorization header exists
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header:
            # No token provided - return None to allow unauthenticated requests
            return None
        
        # Check if it's a token authentication header
        auth_header_parts = auth_header.split()
        if len(auth_header_parts) != 2 or auth_header_parts[0].lower() != 'token':
            # Not a token auth header - return None
            return None
        
        try:
            # Call parent authentication to validate token
            auth_result = super().authenticate(request)
            
            # If authentication succeeded, exempt from CSRF
            if auth_result is not None:
                # Mark request as CSRF exempt
                setattr(request, '_dont_enforce_csrf_checks', True)
                setattr(request, 'csrf_cookie_needed', False)
            
            return auth_result
        except exceptions.AuthenticationFailed:
            # Invalid token - return None to let permission class handle it
            # This allows IsAuthenticatedOrReadOnly to work correctly
            return None
        except Exception:
            # Any other exception - return None
            return None
    
    def enforce_csrf(self, request):
        """
        Override to disable CSRF enforcement for token authentication.
        """
        return  # Do not enforce CSRF for token-authenticated requests

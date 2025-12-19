"""
Custom authentication classes for Django REST Framework
"""
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed


class CsrfExemptTokenAuthentication(TokenAuthentication):
    """
    Custom TokenAuthentication that explicitly exempts CSRF checks.
    This is necessary for mobile app API requests using token authentication.
    
    For safe HTTP methods (GET, HEAD, OPTIONS), invalid tokens are treated as
    no authentication (returns None) to allow IsAuthenticatedOrReadOnly to work.
    For unsafe methods (POST, PUT, PATCH, DELETE), invalid tokens raise
    AuthenticationFailed to enforce authentication.
    """
    
    def authenticate(self, request):
        """
        Authenticate the request using parent class and exempt from CSRF when token is valid.
        For safe methods, invalid tokens are ignored to allow public read access.
        """
        # Check if this is a safe method (read-only)
        is_safe_method = request.method in ('GET', 'HEAD', 'OPTIONS')
        
        try:
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
            
        except AuthenticationFailed:
            # For safe methods, treat invalid token as no authentication
            # This allows IsAuthenticatedOrReadOnly to permit the request
            if is_safe_method:
                return None
            # For unsafe methods, re-raise to enforce authentication
            raise
    
    def enforce_csrf(self, request):
        """
        Override to disable CSRF enforcement for token authentication.
        """
        return  # Do not enforce CSRF for token-authenticated requests

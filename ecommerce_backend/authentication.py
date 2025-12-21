"""
Custom authentication classes for Django REST Framework
"""
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed


class CsrfExemptTokenAuthentication(TokenAuthentication):
    """
    Custom TokenAuthentication that explicitly exempts CSRF checks.
    This is necessary for mobile app API requests using token authentication.
    
    When an Authorization header with a token is provided, it must be valid.
    Only returns None when no Authorization header is present, allowing public endpoints.
    """
    
    def authenticate(self, request):
        """
        Authenticate the request using parent class and exempt from CSRF when token is valid.
        If Authorization header is present, token must be valid (raises exception if invalid).
        Only returns None when no Authorization header is provided.
        """
        # Check if Authorization header is present
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header.startswith('Token '):
            # No token provided - return None (allows unauthenticated access for public endpoints)
            return None
        
        # Token is provided in Authorization header - must validate it strictly
        try:
            # Call parent authentication to validate token
            # This will raise AuthenticationFailed if invalid, or return (user, token) if valid
            auth_result = super().authenticate(request)
            
            # If authentication succeeded, exempt from CSRF
            if auth_result is not None:
                # Mark request as CSRF exempt
                setattr(request, '_dont_enforce_csrf_checks', True)
                setattr(request, 'csrf_cookie_needed', False)
            
            return auth_result
            
        except AuthenticationFailed:
            # Invalid token - always raise exception regardless of HTTP method
            # This ensures IsAuthenticated permission checks work correctly
            raise
    
    def enforce_csrf(self, request):
        """
        Override to disable CSRF enforcement for token authentication.
        """
        return  # Do not enforce CSRF for token-authenticated requests

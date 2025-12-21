from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from website.models import CMSPages, MySetting
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])  # Allow public access for CMS pages
def cms_page_by_slug(request, slug):
    """Get CMS page by slug"""
    try:
        page = get_object_or_404(CMSPages, slug=slug)
        
        # Build image URL if image exists
        image_url = None
        if page.image:
            image_url = request.build_absolute_uri(page.image.url)
        
        return Response({
            'success': True,
            'data': {
                'id': page.id,
                'title': page.title,
                'slug': page.slug,
                'description': page.description,  # HTML content from CKEditor
                'image': image_url,
                'created_at': page.created_at.isoformat(),
                'updated_at': page.updated_at.isoformat(),
            }
        }, status=status.HTTP_200_OK)
    except CMSPages.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Page not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error getting CMS page by slug '{slug}': {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to get page'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])  # Allow public access for contact form
def contact_form_submit(request):
    """Handle contact form submission"""
    try:
        name = request.data.get('name', '').strip()
        email = request.data.get('email', '').strip()
        subject = request.data.get('subject', '').strip()
        message = request.data.get('message', '').strip()
        
        # Basic validation
        if not all([name, email, subject, message]):
            return Response({
                'success': False,
                'error': 'All fields are required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Basic email validation
        if '@' not in email or '.' not in email.split('@')[-1]:
            return Response({
                'success': False,
                'error': 'Please enter a valid email address.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Here you could save to database, send email, etc.
        # For now, just return success (matching website behavior)
        logger.info(f"Contact form submission from {name} ({email}): {subject}")
        
        return Response({
            'success': True,
            'message': 'Thank you for your message. We will get back to you soon!'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error processing contact form: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to submit contact form. Please try again later.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])  # Allow public access for website settings
def website_settings(request):
    """Get website settings, specifically about section data"""
    try:
        setting = MySetting.objects.first()
        
        if not setting:
            return Response({
                'success': True,
                'data': {
                    'about_title': None,
                    'about_tag': None,
                    'about_image': None,
                    'about_description': None,
                }
            }, status=status.HTTP_200_OK)
        
        # Build image URL if image exists
        about_image_url = None
        if setting.about_image:
            about_image_url = request.build_absolute_uri(setting.about_image.url)
        
        return Response({
            'success': True,
            'data': {
                'about_title': setting.about_title,
                'about_tag': setting.about_tag,
                'about_image': about_image_url,
                'about_description': setting.about_description,  # HTML content from CKEditor
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting website settings: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to get website settings'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from website.models import CMSPages
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


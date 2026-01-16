"""
Variant image upload views
"""
import os
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from myadmin.mixins import StaffRequiredMixin
from django.utils.decorators import method_decorator
from django.views import View
import uuid


@method_decorator(csrf_exempt, name='dispatch')
class VariantImageUploadView(StaffRequiredMixin, View):
    """Handle variant combination image uploads"""
    
    def post(self, request):
        if 'image' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'No image file provided'}, status=400)
        
        image_file = request.FILES['image']
        
        # Validate file type
        if not image_file.content_type.startswith('image/'):
            return JsonResponse({'success': False, 'error': 'File must be an image'}, status=400)
        
        # Validate file size (max 5MB)
        if image_file.size > 5 * 1024 * 1024:
            return JsonResponse({'success': False, 'error': 'Image size must be less than 5MB'}, status=400)
        
        try:
            # Generate unique filename
            file_ext = os.path.splitext(image_file.name)[1]
            unique_filename = f"variant_images/{uuid.uuid4()}{file_ext}"
            
            # Save file
            file_path = default_storage.save(unique_filename, ContentFile(image_file.read()))
            
            # Get URL
            if hasattr(default_storage, 'url'):
                file_url = default_storage.url(file_path)
            else:
                # Fallback for local storage
                file_url = f"/media/{file_path}"
            
            return JsonResponse({
                'success': True,
                'url': file_url,
                'filename': file_path
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error uploading image: {str(e)}'
            }, status=500)


# Function-based view for easier URL routing
@require_http_methods(["POST"])
def upload_variant_image(request):
    """Function-based view for variant image upload"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentication required'}, status=401)
    
    if 'image' not in request.FILES:
        return JsonResponse({'success': False, 'error': 'No image file provided'}, status=400)
    
    image_file = request.FILES['image']
    
    # Validate file type
    if not image_file.content_type.startswith('image/'):
        return JsonResponse({'success': False, 'error': 'File must be an image'}, status=400)
    
    # Validate file size (max 5MB)
    if image_file.size > 5 * 1024 * 1024:
        return JsonResponse({'success': False, 'error': 'Image size must be less than 5MB'}, status=400)
    
    try:
        # Generate unique filename
        file_ext = os.path.splitext(image_file.name)[1]
        unique_filename = f"variant_images/{uuid.uuid4()}{file_ext}"
        
        # Save file
        file_path = default_storage.save(unique_filename, ContentFile(image_file.read()))
        
        # Get URL
        if hasattr(default_storage, 'url'):
            file_url = default_storage.url(file_path)
        else:
            # Fallback for local storage
            file_url = f"/media/{file_path}"
        
        return JsonResponse({
            'success': True,
            'url': file_url,
            'filename': file_path
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error uploading image: {str(e)}'
        }, status=500)

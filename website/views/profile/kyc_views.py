from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from website.models import MySetting, CMSPages


@login_required
def kyc_submit_view(request):
    """KYC submission page"""
    try:
        settings = MySetting.objects.first()
    except MySetting.DoesNotExist:
        settings = None
    
    menu_pages = CMSPages.objects.filter(on_menu=True)
    footer_pages = CMSPages.objects.filter(on_footer=True)
    
    user = request.user
    
    # If already verified, redirect to status page
    if user.is_kyc_verified:
        messages.info(request, 'Your KYC is already verified.')
        return redirect('website:kyc_status')
    
    if request.method == 'POST':
        national_id = request.POST.get('national_id', '').strip()
        national_id_document = request.FILES.get('national_id_document')
        pan_no = request.POST.get('pan_no', '').strip()
        pan_document = request.FILES.get('pan_document')
        
        # Validation - at least one document (National ID or PAN) should be provided
        has_national_id = national_id and national_id_document
        has_pan = pan_no and pan_document
        
        if not has_national_id and not has_pan:
            messages.error(request, 'Please provide at least one document: either National ID or PAN.')
        else:
            errors = []
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'application/pdf']
            
            # Validate National ID if provided
            if national_id or national_id_document:
                if national_id and not national_id_document:
                    errors.append('National ID document is required when National ID number is provided.')
                elif national_id_document:
                    if national_id_document.size > 5 * 1024 * 1024:
                        errors.append('National ID document size should not exceed 5MB.')
                    elif national_id_document.content_type not in allowed_types:
                        errors.append('Invalid National ID document type. Please upload an image (JPEG, PNG, GIF) or PDF.')
            
            # Validate PAN if provided
            if pan_no or pan_document:
                if pan_no and not pan_document:
                    errors.append('PAN document is required when PAN number is provided.')
                elif pan_document:
                    if pan_document.size > 5 * 1024 * 1024:
                        errors.append('PAN document size should not exceed 5MB.')
                    elif pan_document.content_type not in allowed_types:
                        errors.append('Invalid PAN document type. Please upload an image (JPEG, PNG, GIF) or PDF.')
            
            if errors:
                for error in errors:
                    messages.error(request, error)
            else:
                try:
                    # Update user KYC information
                    if national_id:
                        user.national_id = national_id
                    if national_id_document:
                        user.national_id_document = national_id_document
                    if pan_no:
                        user.pan_no = pan_no
                    if pan_document:
                        user.pan_document = pan_document
                    
                    # Only update kyc_submitted_at if at least one document is being submitted
                    if has_national_id or has_pan:
                        user.kyc_submitted_at = timezone.now()
                        user.is_kyc_verified = False  # Reset verification status if resubmitting
                        user.kyc_verified_at = None
                    
                    user.save()
                    
                    messages.success(request, 'KYC information submitted successfully! It will be reviewed by our team.')
                    return redirect('website:kyc_status')
                except Exception as e:
                    messages.error(request, f'Error submitting KYC: {str(e)}')
    
    context = {
        'settings': settings,
        'menu_pages': menu_pages,
        'footer_pages': footer_pages,
        'user': user,
    }
    
    return render(request, 'website/profile/kyc_submit.html', context)


@login_required
def kyc_status_view(request):
    """KYC status display page"""
    try:
        settings = MySetting.objects.first()
    except MySetting.DoesNotExist:
        settings = None
    
    menu_pages = CMSPages.objects.filter(on_menu=True)
    footer_pages = CMSPages.objects.filter(on_footer=True)
    
    user = request.user
    
    context = {
        'settings': settings,
        'menu_pages': menu_pages,
        'footer_pages': footer_pages,
        'user': user,
    }
    
    return render(request, 'website/profile/kyc_status.html', context)


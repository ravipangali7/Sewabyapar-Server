from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from shared.models import FeedbackComplain
from website.models import MySetting, CMSPages


@login_required
def feedback_complain_view(request):
    """Feedback/Complain form page"""
    try:
        settings = MySetting.objects.first()
    except MySetting.DoesNotExist:
        settings = None
    
    menu_pages = CMSPages.objects.filter(on_menu=True)
    footer_pages = CMSPages.objects.filter(on_footer=True)
    
    feedback_type = request.GET.get('type', 'feedback')
    
    if request.method == 'POST':
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()
        feedback_type = request.POST.get('type', 'feedback')
        
        if not all([subject, message]):
            messages.error(request, 'Subject and message are required.')
        else:
            FeedbackComplain.objects.create(
                user=request.user,
                subject=subject,
                message=message,
                type=feedback_type,
            )
            messages.success(request, f'Your {feedback_type} has been submitted successfully!')
            return redirect('website:feedback_complain')
    
    # Get user's feedback/complains
    user_feedbacks = FeedbackComplain.objects.filter(user=request.user).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(user_feedbacks, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'settings': settings,
        'menu_pages': menu_pages,
        'footer_pages': footer_pages,
        'feedback_type': feedback_type,
        'user_feedbacks': page_obj,
    }
    
    return render(request, 'website/profile/feedback_complain.html', context)


@login_required
def feedback_detail_view(request, feedback_id):
    """Feedback/Complain detail page"""
    try:
        settings = MySetting.objects.first()
    except MySetting.DoesNotExist:
        settings = None
    
    menu_pages = CMSPages.objects.filter(on_menu=True)
    footer_pages = CMSPages.objects.filter(on_footer=True)
    
    feedback = get_object_or_404(FeedbackComplain, id=feedback_id, user=request.user)
    replies = feedback.replies.all().order_by('created_at')
    
    if request.method == 'POST':
        # Add reply
        message = request.POST.get('message', '').strip()
        if message:
            feedback.replies.create(
                user=request.user,
                message=message,
                is_admin_reply=False,
            )
            messages.success(request, 'Your reply has been added.')
            return redirect('website:feedback_detail', feedback_id=feedback_id)
        else:
            messages.error(request, 'Message is required.')
    
    context = {
        'settings': settings,
        'menu_pages': menu_pages,
        'footer_pages': footer_pages,
        'feedback': feedback,
        'replies': replies,
    }
    
    return render(request, 'website/profile/feedback_detail.html', context)


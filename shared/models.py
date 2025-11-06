from django.db import models
from core.models import User


class Place(models.Model):
    """Place model for trip locations"""
    name = models.CharField(max_length=200)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']


class FeedbackComplain(models.Model):
    """Feedback and Complain model"""
    TYPE_CHOICES = [
        ('feedback', 'Feedback'),
        ('complain', 'Complain'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedback_complains')
    subject = models.CharField(max_length=200)
    message = models.TextField()
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='feedback')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.get_type_display()} - {self.subject} ({self.user.name})"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Feedback/Complain'
        verbose_name_plural = 'Feedbacks/Complains'


class FeedbackComplainReply(models.Model):
    """Reply model for Feedback and Complain"""
    feedback_complain = models.ForeignKey(
        FeedbackComplain, 
        on_delete=models.CASCADE, 
        related_name='replies'
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedback_replies')
    is_admin_reply = models.BooleanField(default=False)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        reply_type = "Admin" if self.is_admin_reply else "Customer"
        return f"{reply_type} Reply to: {self.feedback_complain.subject}"
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Feedback/Complain Reply'
        verbose_name_plural = 'Feedback/Complain Replies'
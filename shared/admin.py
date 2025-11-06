from django.contrib import admin
from .models import Place, FeedbackComplain, FeedbackComplainReply


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


class FeedbackComplainReplyInline(admin.TabularInline):
    """Inline admin for replies"""
    model = FeedbackComplainReply
    extra = 0
    readonly_fields = ['created_at']
    fields = ['is_admin_reply', 'message', 'created_at']
    exclude = ['user']  # Hide user field, will be auto-set


@admin.register(FeedbackComplain)
class FeedbackComplainAdmin(admin.ModelAdmin):
    list_display = ['subject', 'user', 'type', 'status', 'created_at']
    list_filter = ['type', 'status', 'created_at']
    search_fields = ['subject', 'message', 'user__name', 'user__phone']
    readonly_fields = ['user', 'created_at', 'updated_at']
    inlines = [FeedbackComplainReplyInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'subject', 'message', 'type', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_formset(self, request, form, formset, change):
        """Override to auto-set user and is_admin_reply for inline replies"""
        instances = formset.save(commit=False)
        for instance in instances:
            # If this is a new reply (no pk) or user is not set, set it to admin user
            if not instance.pk or not instance.user_id:
                instance.user = request.user
                instance.is_admin_reply = True
            instance.save()
        # Delete any marked for deletion
        for obj in formset.deleted_objects:
            obj.delete()


@admin.register(FeedbackComplainReply)
class FeedbackComplainReplyAdmin(admin.ModelAdmin):
    list_display = ['feedback_complain', 'user', 'is_admin_reply', 'created_at']
    list_filter = ['is_admin_reply', 'created_at']
    search_fields = ['message', 'feedback_complain__subject', 'user__name']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Reply Information', {
            'fields': ('feedback_complain', 'user', 'is_admin_reply', 'message')
        }),
        ('Timestamp', {
            'fields': ('created_at',),
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Override to auto-set user and is_admin_reply for admin replies"""
        if not change or not obj.user_id:  # New reply or user not set
            obj.user = request.user
            obj.is_admin_reply = True
        super().save_model(request, obj, form, change)
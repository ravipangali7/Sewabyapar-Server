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
    readonly_fields = ['user', 'created_at']
    fields = ['user', 'is_admin_reply', 'message', 'created_at']


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
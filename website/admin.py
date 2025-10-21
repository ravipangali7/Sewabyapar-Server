from django.contrib import admin
from django.utils.html import format_html
from .models import MySetting, Services, CMSPages


@admin.register(MySetting)
class MySettingAdmin(admin.ModelAdmin):
    """Admin for website settings - singleton pattern"""
    list_display = ['name', 'phone', 'email', 'total_customers', 'updated_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'phone', 'email', 'logo', 'tagline')
        }),
        ('Hero Section', {
            'fields': ('hero_title', 'hero_image', 'hero_description')
        }),
        ('About Section', {
            'fields': ('about_title', 'about_tag', 'about_image', 'about_description')
        }),
        ('Statistics', {
            'fields': ('total_customers', 'total_daily_signup', 'total_txn_everyday')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Prevent adding multiple instances"""
        return not MySetting.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deleting the only instance"""
        return False


@admin.register(Services)
class ServicesAdmin(admin.ModelAdmin):
    """Admin for services"""
    list_display = ['title', 'slug', 'created_at']
    list_filter = ['created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['slug', 'created_at', 'updated_at']
    prepopulated_fields = {'slug': ('title',)}
    
    fieldsets = (
        ('Service Information', {
            'fields': ('title', 'slug', 'image', 'description')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CMSPages)
class CMSPagesAdmin(admin.ModelAdmin):
    """Admin for CMS pages"""
    list_display = ['title', 'slug', 'on_menu', 'on_footer', 'created_at']
    list_filter = ['on_menu', 'on_footer', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['slug', 'created_at', 'updated_at']
    prepopulated_fields = {'slug': ('title',)}
    
    fieldsets = (
        ('Page Information', {
            'fields': ('title', 'slug', 'image', 'description')
        }),
        ('Display Options', {
            'fields': ('on_menu', 'on_footer')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
from django.db import models
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django_ckeditor_5.fields import CKEditor5Field


class MySetting(models.Model):
    """Website settings model - singleton pattern"""
    name = models.CharField(max_length=200, help_text="Company/Website name")
    phone = models.CharField(max_length=20, help_text="Contact phone number")
    email = models.EmailField(help_text="Contact email address")
    address = models.TextField(blank=True, help_text="Company address")
    website = models.URLField(blank=True, help_text="Company website URL")
    logo = models.ImageField(upload_to='website/logos/', blank=True, null=True, help_text="Company logo")
    tagline = models.CharField(max_length=300, blank=True, help_text="Website tagline")
    
    # Hero Section
    hero_title = models.CharField(max_length=200, help_text="Hero section main title")
    hero_image = models.ImageField(upload_to='website/hero/', blank=True, null=True, help_text="Hero section background image")
    hero_description = CKEditor5Field('Hero section description', config_name='default')
    
    # About Section
    about_title = models.CharField(max_length=200, help_text="About section title")
    about_tag = models.CharField(max_length=200, blank=True, help_text="About section tagline")
    about_image = models.ImageField(upload_to='website/about/', blank=True, null=True, help_text="About section image")
    about_description = CKEditor5Field('About section description', config_name='default')
    
    # Statistics
    total_customers = models.IntegerField(default=0, help_text="Total number of customers")
    total_daily_signup = models.IntegerField(default=0, help_text="Daily signup count")
    total_txn_everyday = models.IntegerField(default=0, help_text="Daily transaction count")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def clean(self):
        """Ensure only one instance exists"""
        if MySetting.objects.exists() and not self.pk:
            raise ValidationError("Only one MySetting instance is allowed")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Website Settings - {self.name}"
    
    class Meta:
        verbose_name = "Website Settings"
        verbose_name_plural = "Website Settings"


class Services(models.Model):
    """Services offered by the website"""
    title = models.CharField(max_length=200, help_text="Service title")
    slug = models.SlugField(max_length=200, unique=True, blank=True, help_text="URL-friendly version of title")
    image = models.ImageField(upload_to='website/services/', blank=True, null=True, help_text="Service image")
    description = models.TextField(help_text="Service description")
    url = models.URLField(blank=True, null=True, help_text="Service URL for redirect")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = "Service"
        verbose_name_plural = "Services"
        ordering = ['created_at']


class CMSPages(models.Model):
    """Content Management System pages"""
    title = models.CharField(max_length=200, help_text="Page title")
    slug = models.SlugField(max_length=200, unique=True, blank=True, help_text="URL-friendly version of title")
    image = models.ImageField(upload_to='website/cms/', blank=True, null=True, help_text="Page image")
    description = CKEditor5Field('Page content', config_name='extends')
    on_footer = models.BooleanField(default=False, help_text="Show in footer links")
    on_menu = models.BooleanField(default=False, help_text="Show in main navigation menu")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = "CMS Page"
        verbose_name_plural = "CMS Pages"
        ordering = ['created_at']
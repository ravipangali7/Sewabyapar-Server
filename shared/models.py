from django.db import models


class Place(models.Model):
    """Place model for trip locations"""
    name = models.CharField(max_length=200)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']
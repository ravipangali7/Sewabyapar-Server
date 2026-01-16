"""
Hierarchical Category Widget
Shows parent-child relationships in category dropdown
"""
from django import forms
from ecommerce.models import Category


class HierarchicalCategoryWidget(forms.Select):
    """Widget that displays categories in a hierarchical format"""
    
    def __init__(self, attrs=None):
        super().__init__(attrs)
        self.choices = []
    
    def build_choices(self, value, categories=None):
        """Build hierarchical choices from categories"""
        if categories is None:
            categories = Category.objects.filter(is_active=True).order_by('name')
        
        choices = [('', '---------')]  # Empty choice
        
        # Build a tree structure
        def build_tree(parent=None, level=0):
            """Recursively build category tree"""
            items = []
            children = [c for c in categories if c.parent == parent]
            
            for category in children:
                # Add indentation for hierarchy
                prefix = '  ' * level + '└─ ' if level > 0 else ''
                display_name = f"{prefix}{category.name}"
                items.append((category.id, display_name))
                # Add children recursively
                items.extend(build_tree(parent=category, level=level + 1))
            
            return items
        
        choices.extend(build_tree())
        return choices
    
    def render(self, name, value, attrs=None, renderer=None):
        """Render the widget with hierarchical choices"""
        # Get all active categories
        categories = Category.objects.filter(is_active=True).select_related('parent').order_by('name')
        
        # Build hierarchical choices
        self.choices = self.build_choices(value, categories)
        
        return super().render(name, value, attrs, renderer)

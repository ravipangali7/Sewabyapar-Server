"""
CSV Export utility for admin panel
"""
import csv
from django.http import HttpResponse
from django.db.models import QuerySet
from typing import List, Dict, Any


def export_to_csv(queryset: QuerySet, filename: str, field_names: List[str] = None, 
                  field_labels: Dict[str, str] = None, get_field_value=None) -> HttpResponse:
    """
    Export a queryset to CSV format
    
    Args:
        queryset: Django queryset to export
        filename: Name of the CSV file (without .csv extension)
        field_names: List of field names to export (if None, uses all model fields)
        field_labels: Dictionary mapping field names to display labels
        get_field_value: Optional function to get custom field values (obj, field_name) -> value
    
    Returns:
        HttpResponse with CSV content
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
    
    writer = csv.writer(response)
    
    # Get model fields if not specified
    if field_names is None:
        model = queryset.model
        field_names = [f.name for f in model._meta.get_fields() 
                      if not f.many_to_many and not f.one_to_many]
    
    # Write header row
    if field_labels:
        headers = [field_labels.get(field, field.replace('_', ' ').title()) 
                  for field in field_names]
    else:
        headers = [field.replace('_', ' ').title() for field in field_names]
    
    writer.writerow(headers)
    
    # Write data rows
    for obj in queryset:
        row = []
        for field_name in field_names:
            if get_field_value:
                value = get_field_value(obj, field_name)
            else:
                value = get_field_value_default(obj, field_name)
            
            # Convert to string and handle None
            if value is None:
                row.append('')
            elif isinstance(value, bool):
                row.append('Yes' if value else 'No')
            else:
                row.append(str(value))
        
        writer.writerow(row)
    
    return response


def get_field_value_default(obj, field_name: str) -> Any:
    """
    Get field value from object with fallback for related fields
    """
    try:
            # Try direct attribute access
            value = getattr(obj, field_name)
            
            # Handle callable values (like methods)
            if callable(value) and not isinstance(value, type):
                value = value()
            
            # Handle related objects
            if hasattr(value, 'pk'):
                # It's a related object, get its string representation
                return str(value)
            
            return value
    except AttributeError:
        # Try as a property or method
        try:
            return getattr(obj, field_name, '')
        except:
            return ''


def export_users_csv(queryset):
    """Export users to CSV"""
    field_names = ['id', 'name', 'phone', 'email', 'country', 'is_kyc_verified', 
                  'is_active', 'is_staff', 'date_joined']
    field_labels = {
        'id': 'ID',
        'name': 'Name',
        'phone': 'Phone',
        'email': 'Email',
        'country': 'Country',
        'is_kyc_verified': 'KYC Verified',
        'is_active': 'Active',
        'is_staff': 'Staff',
        'date_joined': 'Date Joined'
    }
    return export_to_csv(queryset, 'users_export', field_names, field_labels)


def export_products_csv(queryset):
    """Export products to CSV"""
    field_names = ['id', 'name', 'sku', 'store', 'category', 'price', 'stock_quantity', 
                  'is_active', 'created_at']
    field_labels = {
        'id': 'ID',
        'name': 'Product Name',
        'sku': 'SKU',
        'store': 'Store',
        'category': 'Category',
        'price': 'Price',
        'stock_quantity': 'Stock',
        'is_active': 'Active',
        'created_at': 'Created At'
    }
    return export_to_csv(queryset, 'products_export', field_names, field_labels)


def export_orders_csv(queryset):
    """Export orders to CSV"""
    field_names = ['id', 'order_number', 'user', 'status', 'total_amount', 
                  'phone', 'email', 'created_at']
    field_labels = {
        'id': 'ID',
        'order_number': 'Order Number',
        'user': 'Customer',
        'status': 'Status',
        'total_amount': 'Total Amount',
        'phone': 'Phone',
        'email': 'Email',
        'created_at': 'Created At'
    }
    return export_to_csv(queryset, 'orders_export', field_names, field_labels)


def export_stores_csv(queryset):
    """Export stores to CSV"""
    field_names = ['id', 'name', 'owner', 'phone', 'email', 'is_active', 'created_at']
    field_labels = {
        'id': 'ID',
        'name': 'Store Name',
        'owner': 'Owner',
        'phone': 'Phone',
        'email': 'Email',
        'is_active': 'Active',
        'created_at': 'Created At'
    }
    return export_to_csv(queryset, 'stores_export', field_names, field_labels)


def export_categories_csv(queryset):
    """Export categories to CSV"""
    field_names = ['id', 'name', 'parent', 'is_active', 'created_at']
    field_labels = {
        'id': 'ID',
        'name': 'Category Name',
        'parent': 'Parent Category',
        'is_active': 'Active',
        'created_at': 'Created At'
    }
    return export_to_csv(queryset, 'categories_export', field_names, field_labels)


def export_bookings_csv(queryset):
    """Export taxi bookings to CSV"""
    field_names = ['id', 'customer', 'trip', 'date', 'time', 'price', 
                  'trip_status', 'payment_status', 'created_at']
    field_labels = {
        'id': 'ID',
        'customer': 'Customer',
        'trip': 'Trip',
        'date': 'Date',
        'time': 'Time',
        'price': 'Price',
        'trip_status': 'Trip Status',
        'payment_status': 'Payment Status',
        'created_at': 'Created At'
    }
    return export_to_csv(queryset, 'bookings_export', field_names, field_labels)


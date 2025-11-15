"""
Bulk action utilities for admin panel
"""
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from typing import List, Any, Callable


def bulk_delete(request, model_class, object_ids: List[int], 
                success_message: str = None, error_message: str = None) -> tuple[int, int]:
    """
    Delete multiple objects in bulk
    
    Args:
        request: Django request object
        model_class: Model class to delete from
        object_ids: List of object IDs to delete
        success_message: Custom success message
        error_message: Custom error message
    
    Returns:
        Tuple of (deleted_count, error_count)
    """
    deleted_count = 0
    error_count = 0
    
    try:
        with transaction.atomic():
            queryset = model_class.objects.filter(pk__in=object_ids)
            count = queryset.count()
            
            if count > 0:
                queryset.delete()
                deleted_count = count
                
                if success_message:
                    messages.success(request, success_message.format(count=deleted_count))
                else:
                    messages.success(request, f'Successfully deleted {deleted_count} item(s).')
            else:
                messages.warning(request, 'No items selected for deletion.')
    
    except Exception as e:
        error_count = len(object_ids)
        if error_message:
            messages.error(request, error_message)
        else:
            messages.error(request, f'Error deleting items: {str(e)}')
    
    return deleted_count, error_count


def bulk_update_status(request, model_class, object_ids: List[int], 
                      status_field: str, new_status: Any,
                      success_message: str = None) -> tuple[int, int]:
    """
    Update status of multiple objects in bulk
    
    Args:
        request: Django request object
        model_class: Model class to update
        object_ids: List of object IDs to update
        status_field: Name of the status field
        new_status: New status value
        success_message: Custom success message
    
    Returns:
        Tuple of (updated_count, error_count)
    """
    updated_count = 0
    error_count = 0
    
    try:
        with transaction.atomic():
            queryset = model_class.objects.filter(pk__in=object_ids)
            count = queryset.count()
            
            if count > 0:
                update_dict = {status_field: new_status}
                queryset.update(**update_dict)
                updated_count = count
                
                if success_message:
                    messages.success(request, success_message.format(count=updated_count, status=new_status))
                else:
                    messages.success(request, f'Successfully updated {updated_count} item(s) status to {new_status}.')
            else:
                messages.warning(request, 'No items selected for update.')
    
    except Exception as e:
        error_count = len(object_ids)
        messages.error(request, f'Error updating items: {str(e)}')
    
    return updated_count, error_count


def bulk_activate(request, model_class, object_ids: List[int], 
                 active_field: str = 'is_active') -> tuple[int, int]:
    """Bulk activate objects"""
    return bulk_update_status(
        request, model_class, object_ids, active_field, True,
        success_message='Successfully activated {count} item(s).'
    )


def bulk_deactivate(request, model_class, object_ids: List[int],
                   active_field: str = 'is_active') -> tuple[int, int]:
    """Bulk deactivate objects"""
    return bulk_update_status(
        request, model_class, object_ids, active_field, False,
        success_message='Successfully deactivated {count} item(s).'
    )


def get_selected_ids(request) -> List[int]:
    """
    Get selected object IDs from request POST data
    
    Args:
        request: Django request object
    
    Returns:
        List of selected IDs
    """
    selected_ids = request.POST.getlist('selected_items')
    return [int(id) for id in selected_ids if id.isdigit()]


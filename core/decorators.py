"""
Security decorators for client-admin separation
"""
from functools import wraps
from django.shortcuts import redirect, render
from django.contrib import messages
from django.contrib.auth import logout


def client_only(view_func):
    """
    Allows all authenticated users (including admins) to access client views.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)
    return wrapper


def _admin_login_redirect(request):
    return redirect(f'/admin/login/?next={request.path}')


def admin_only(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return _admin_login_redirect(request)
        if not (request.user.is_staff or request.user.is_superuser):
            return _admin_login_redirect(request)
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_with_permission(required_permissions):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return _admin_login_redirect(request)
            if not (request.user.is_staff or request.user.is_superuser):
                return _admin_login_redirect(request)

            from .admin_roles import has_permission
            if has_permission(request.user, required_permissions):
                return view_func(request, *args, **kwargs)

            messages.error(request, 'You do not have permission to access this section.')
            return redirect('admin_console')
        return wrapper
    return decorator


def get_admin_context(request, active_section=None):
    """
    Get common admin context including navigation items based on user permissions.
    
    Args:
        request: Django request object
        active_section: ID of the currently active section for highlighting
        
    Returns:
        dict: Context dictionary with admin navigation and user info
    """
    from .admin_roles import get_visible_nav_sections, get_user_permissions, ADMIN_ROLES
    
    user = request.user
    nav_sections = get_visible_nav_sections(user)
    user_perms = get_user_permissions(user)
    
    # Get user's role display name
    role_name = 'Staff'
    if user.is_superuser:
        role_name = 'Super Admin'
    elif hasattr(user, 'admin_role') and user.admin_role:
        role_info = ADMIN_ROLES.get(user.admin_role, {})
        role_name = role_info.get('name', 'Staff')
    
    return {
        'admin_nav_sections': nav_sections,
        'active_section': active_section,
        'user_permissions': user_perms,
        'user_role_name': role_name,
        'is_super_admin': 'all' in user_perms,
    }

"""
Security decorators for client-admin separation
"""
from functools import wraps
from django.shortcuts import redirect, render
from django.contrib import messages
from django.contrib.auth import logout


def client_only(view_func):
    """
    Decorator to ensure only non-admin users can access client views
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Check if user is authenticated and is admin
        if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
            # Instead of logging out, redirect admin users to the admin panel
            messages.error(request, 'Admin accounts cannot access the client application. Please use the admin panel.')
            return redirect('/capitalx_admin/')
        
        # Continue with normal view execution
        return view_func(request, *args, **kwargs)
    
    return wrapper


def admin_only(view_func):
    """
    Decorator to ensure only admin users can access admin views
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            messages.error(request, 'Please log in to access this page.')
            return redirect('login')
        
        # Check if user has admin privileges
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(
                request, 
                f'Access denied. Admin privileges required. '
                f'Current user: {request.user.email} (Staff: {request.user.is_staff}, Superuser: {request.user.is_superuser})'
            )
            return redirect('home')
        
        # Continue with normal view execution
        return view_func(request, *args, **kwargs)
    
    return wrapper


def admin_with_permission(required_permissions):
    """
    Decorator for role-based admin access control.
    
    Usage:
        @admin_with_permission(['deposits', 'withdrawals'])
        def deposit_dashboard_view(request):
            ...
    
    Args:
        required_permissions: list of permission strings (e.g., ['deposits', 'users'])
    
    Returns:
        Decorated function that checks user permissions before allowing access
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Check if user is authenticated
            if not request.user.is_authenticated:
                messages.error(request, 'Please log in to access this page.')
                return redirect('login')
            
            # Check if user has admin privileges
            if not (request.user.is_staff or request.user.is_superuser):
                messages.error(request, 'Admin access required.')
                return redirect('home')
            
            # Import here to avoid circular imports
            from .admin_roles import has_permission
            
            # Check role permissions
            if has_permission(request.user, required_permissions):
                return view_func(request, *args, **kwargs)
            
            # User doesn't have required permissions
            messages.error(request, 'You do not have permission to access this section.')
            return redirect('admin_dashboard')
        
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

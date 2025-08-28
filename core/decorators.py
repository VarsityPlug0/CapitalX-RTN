"""
Security decorators for client-admin separation
"""
from functools import wraps
from django.shortcuts import redirect
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
            # Log out the admin user
            logout(request)
            messages.error(request, 'Admin accounts cannot access the client application. Please use the admin panel.')
            return redirect('home')
        
        # Continue with normal view execution
        return view_func(request, *args, **kwargs)
    
    return wrapper


def admin_only(view_func):
    """
    Decorator to ensure only admin users can access admin views
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Check if user is authenticated and is not admin
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, 'Access denied. Admin privileges required.')
            return redirect('home')
        
        # Continue with normal view execution
        return view_func(request, *args, **kwargs)
    
    return wrapper

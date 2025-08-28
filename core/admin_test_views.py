"""
Admin test views to debug access issues
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages


@login_required
def debug_admin_status(request):
    """
    Debug view to check user's admin status
    """
    user = request.user
    
    debug_info = {
        'username': user.username,
        'email': user.email,
        'is_authenticated': user.is_authenticated,
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
        'is_active': user.is_active,
        'session_key': request.session.session_key,
        'has_admin_access': user.is_staff or user.is_superuser,
    }
    
    return JsonResponse(debug_info, indent=2)


@login_required  
def simple_lead_manager(request):
    """
    Simple lead manager without admin_only decorator for testing
    """
    user = request.user
    
    # Manual admin check
    if not (user.is_staff or user.is_superuser):
        messages.error(request, f'Access denied. User {user.email} does not have admin privileges. is_staff: {user.is_staff}, is_superuser: {user.is_superuser}')
        return render(request, 'core/access_denied.html', {
            'user_info': {
                'email': user.email,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
                'is_active': user.is_active,
            }
        })
    
    # If we get here, user has admin access
    context = {
        'user': user,
        'debug_info': {
            'email': user.email,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'has_access': True,
        }
    }
    
    return render(request, 'core/simple_lead_manager.html', context)

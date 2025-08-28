"""
Health check views for debugging deployment issues
"""
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import sys
import os


def health_check(request):
    """
    Simple health check endpoint to test if the app is running
    """
    try:
        # Test database connection
        from .models import CustomUser
        user_count = CustomUser.objects.count()
        
        # Test imports
        import reportlab
        import dns
        
        health_data = {
            'status': 'healthy',
            'database': 'connected',
            'user_count': user_count,
            'python_version': sys.version,
            'django_working': True,
            'dependencies': {
                'reportlab': str(reportlab.Version),
                'dnspython': 'available'
            }
        }
        
        return JsonResponse(health_data)
        
    except Exception as e:
        health_data = {
            'status': 'error',
            'error': str(e),
            'python_version': sys.version,
        }
        return JsonResponse(health_data, status=500)


def simple_test_page(request):
    """
    Simple test page that doesn't use complex features
    """
    context = {
        'title': 'CapitalX Test Page',
        'message': 'If you see this, the basic Django app is working!',
        'debug_info': {
            'user_authenticated': request.user.is_authenticated,
            'user_is_staff': request.user.is_staff if request.user.is_authenticated else False,
            'session_key': request.session.session_key,
        }
    }
    
    return render(request, 'core/simple_test.html', context)


@csrf_exempt
def debug_imports(request):
    """
    Test all the imports that might be causing issues
    """
    import_results = {}
    
    try:
        from . import models
        import_results['models'] = 'OK'
    except Exception as e:
        import_results['models'] = f'ERROR: {e}'
    
    try:
        from . import views
        import_results['views'] = 'OK'
    except Exception as e:
        import_results['views'] = f'ERROR: {e}'
        
    try:
        from . import lead_manager_views
        import_results['lead_manager_views'] = 'OK'
    except Exception as e:
        import_results['lead_manager_views'] = f'ERROR: {e}'
        
    try:
        from . import lead_system
        import_results['lead_system'] = 'OK'
    except Exception as e:
        import_results['lead_system'] = f'ERROR: {e}'
        
    try:
        from . import decorators
        import_results['decorators'] = 'OK'
    except Exception as e:
        import_results['decorators'] = f'ERROR: {e}'
    
    try:
        import reportlab
        import_results['reportlab'] = f'OK - {reportlab.Version}'
    except Exception as e:
        import_results['reportlab'] = f'ERROR: {e}'
        
    try:
        import dns
        import_results['dnspython'] = 'OK'
    except Exception as e:
        import_results['dnspython'] = f'ERROR: {e}'
    
    return JsonResponse({
        'status': 'debug_complete',
        'imports': import_results
    })

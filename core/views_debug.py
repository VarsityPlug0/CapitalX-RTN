from django.shortcuts import render
from django.middleware.csrf import get_token
from django.http import JsonResponse

def csrf_debug_view(request):
    """
    Debug view to check CSRF token availability
    """
    if request.method == 'GET':
        # Generate CSRF token
        csrf_token = get_token(request)
        
        context = {
            'csrf_token': csrf_token,
            'has_csrf_cookie': 'csrftoken' in request.COOKIES,
            'cookies': list(request.COOKIES.keys()),
            'session_id': request.session.session_key,
        }
        
        return render(request, 'core/debug_csrf.html', context)
    
    elif request.method == 'POST':
        # Check if CSRF token was provided
        csrf_token_provided = request.META.get('HTTP_X_CSRFTOKEN') or request.POST.get('csrfmiddlewaretoken')
        
        return JsonResponse({
            'status': 'received',
            'csrf_token_provided': bool(csrf_token_provided),
            'csrf_token_value': csrf_token_provided,
            'has_csrf_cookie': 'csrftoken' in request.COOKIES,
        })
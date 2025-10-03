from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import logging

# Set up logging
logger = logging.getLogger(__name__)

@csrf_exempt
def simple_test_view(request):
    """
    Simple test API endpoint
    """
    logger.info(f"Received request: {request.method} {request.path}")
    logger.info(f"Request headers: {dict(request.headers)}")
    
    data = {
        'message': 'API is working!',
        'status': 'success',
        'method': request.method,
        'path': request.path,
    }
    return JsonResponse(data)
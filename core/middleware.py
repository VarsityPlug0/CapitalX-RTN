"""
Security middleware to prevent admin accounts from accessing client-side views
"""
import logging
import os
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
import mimetypes

# Set up logging
logger = logging.getLogger(__name__)

class AdminClientSeparationMiddleware:
    """
    Middleware to ensure admin accounts cannot access client-side application
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Admin-only URL patterns
        self.admin_urls = [
            '/capitalx_admin/',
            '/admin/',
            '/admin_dashboard/',
        ]
        
        # Client-side URLs that admins should never access
        self.client_urls = [
            '/dashboard/',
            '/wallet/',
            '/deposit/',
            '/withdraw/',
            '/tiers/',
            '/investment-plans/',
            '/invest/',
            '/referral/',
            '/profile/',
            '/feed/',
            '/portfolio/',
        ]
    
    def __call__(self, request):
        # Process the request
        response = self.process_request(request)
        if response:
            return response
            
        # Get the response from the next middleware/view
        response = self.get_response(request)
        
        return response
    
    def process_request(self, request):
        """
        Check if admin user is trying to access client-side URLs
        """
        # Skip if user is not authenticated
        if not request.user.is_authenticated:
            return None
        
        # Skip if not an admin user
        if not (request.user.is_staff or request.user.is_superuser):
            return None
        
        # Get current path
        current_path = request.path
        
        # Allow admin users to access admin URLs
        if any(current_path.startswith(admin_url) for admin_url in self.admin_urls):
            return None
        
        # Allow specific admin-related URLs that might be accessed after actions
        allowed_admin_paths = [
            '/admin/',
            '/capitalx_admin/',
            '/logout/',
            '/login/',
            '/register/',
            '/verify-otp/',
            '/send-verification-otp/',
            '/resend-otp/',
        ]
        
        if any(current_path.startswith(path) for path in allowed_admin_paths):
            return None
            
        # Special case: Allow the root URL for admins (they'll be redirected to admin panel)
        if current_path == '/':
            return None
        
        # Block admin users from accessing client-side URLs
        if any(current_path.startswith(client_url) for client_url in self.client_urls):
            # Instead of logging out, redirect to admin panel
            # Check if messages framework is available before using it
            if hasattr(request, 'session') and '_messages' in request.session.__dict__:
                messages.error(request, 'Admin accounts cannot access the client application. Please use the admin panel.')
            return redirect('/capitalx_admin/')
        
        return None


class ClientAdminAccessMiddleware:
    """
    Additional middleware to block any admin access to client views
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check if authenticated user is admin trying to access client area
        if (request.user.is_authenticated and 
            (request.user.is_staff or request.user.is_superuser) and 
            not request.path.startswith('/capitalx_admin/') and 
            not request.path.startswith('/admin/') and
            not request.path.startswith('/logout/') and
            not request.path.startswith('/login/') and
            request.path != '/' and
            request.path != '/admin_dashboard/' and
            not request.path.startswith('/admin/')):  # Allow all admin URLs
            
            # Instead of logging out, redirect to admin panel
            # Check if messages framework is available before using it
            if hasattr(request, 'session') and '_messages' in request.session.__dict__:
                messages.error(request, 'Admin accounts cannot access the client application. Please use the admin panel.')
            return redirect('/capitalx_admin/')
        
        response = self.get_response(request)
        return response


# Add a middleware to serve media files in production
class MediaFileMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Always log the request path to see if middleware is being called
        logger.info(f"MediaFileMiddleware START processing request for: {request.path}")
        
        # Check if the request is for a media file
        if request.path.startswith(settings.MEDIA_URL):
            logger.info(f"MediaFileMiddleware handling media request for: {request.path}")
            
            # Security check: prevent directory traversal attacks
            if '..' in request.path:
                logger.warning(f"Directory traversal attempt blocked: {request.path}")
                response = HttpResponse(b"Forbidden", status=403)
                return response
            
            # Remove the MEDIA_URL prefix to get the file path
            # Handle both cases where MEDIA_URL ends with / or not
            media_url = settings.MEDIA_URL
            if media_url.endswith('/'):
                file_path = request.path[len(media_url):]
            else:
                file_path = request.path[len(media_url)+1:]
            
            # Security check: ensure file_path doesn't start with /
            if file_path.startswith('/'):
                file_path = file_path[1:]
            
            # Construct the full file path
            full_path = os.path.join(settings.MEDIA_ROOT, file_path)
            
            logger.info(f"Looking for file at: {full_path}")
            logger.info(f"File exists: {os.path.exists(full_path)}")
            logger.info(f"Is file: {os.path.isfile(full_path)}")
            
            # Check if the file exists and is actually a file (not a directory)
            if os.path.exists(full_path) and os.path.isfile(full_path):
                logger.info(f"File found, serving: {full_path}")
                # Determine content type
                content_type, _ = mimetypes.guess_type(full_path)
                if content_type is None:
                    content_type = 'application/octet-stream'
                
                logger.info(f"Content type: {content_type}")
                
                # Read and serve the file
                try:
                    with open(full_path, 'rb') as f:
                        content = f.read()
                    
                    # Create response
                    response = HttpResponse(content, content_type=content_type)
                    response['Content-Length'] = str(len(content))
                    response['Cache-Control'] = 'public, max-age=31536000'  # Cache for 1 year
                    logger.info(f"Successfully served file, content length: {len(content)}")
                    return response
                except Exception as e:
                    logger.error(f"Error reading file {full_path}: {e}")
                    # If there's an error reading the file, fall back to normal processing
                    pass
            else:
                logger.warning(f"File not found: {full_path}")
                logger.warning(f"MEDIA_ROOT: {settings.MEDIA_ROOT}")
                logger.warning(f"MEDIA_URL: {settings.MEDIA_URL}")
                logger.warning(f"Requested path: {request.path}")
                logger.warning(f"File path extracted: {file_path}")
                
                # Even if file not found, we still handle this request to prevent 404 from Django
                # This ensures our middleware is working
                response = HttpResponse(b"File not found", status=404)
                return response
        else:
            logger.info(f"MediaFileMiddleware - Not a media request: {request.path}")
        
        # For all other requests, use the normal Django processing
        response = self.get_response(request)
        logger.info(f"MediaFileMiddleware END processing request for: {request.path}")
        return response

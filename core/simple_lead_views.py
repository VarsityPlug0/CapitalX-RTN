"""
Simple Lead Manager Views - Error-free fallback
===============================================

This provides a basic lead manager interface without complex dependencies
that might cause import errors on production.
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count
from .decorators import admin_only


@login_required
@admin_only
def simple_lead_dashboard(request):
    """
    Simple lead manager dashboard without complex dependencies
    """
    try:
        # Import models here to catch any import issues
        from .models import LeadCampaign, Lead, EmailSent, EmailValidation
        
        # Get basic statistics
        campaigns = LeadCampaign.objects.filter(created_by=request.user).order_by('-created_at')
        total_campaigns = campaigns.count()
        total_leads = Lead.objects.filter(campaign__created_by=request.user).count()
        successful_leads = Lead.objects.filter(campaign__created_by=request.user, success=True).count()
        total_emails_sent = EmailSent.objects.filter(lead__campaign__created_by=request.user, success=True).count()
        
        # Recent campaigns
        recent_campaigns = campaigns[:5]
        
        # Success rate
        success_rate = (successful_leads / total_leads * 100) if total_leads > 0 else 0
        
        context = {
            'campaigns': recent_campaigns,
            'total_campaigns': total_campaigns,
            'total_leads': total_leads,
            'successful_leads': successful_leads,
            'total_emails_sent': total_emails_sent,
            'success_rate': round(success_rate, 2),
            'suggestions': {
                'available_first_names': 100,
                'available_last_names': 100,
                'available_domains': 40,
                'recommended_batch_sizes': [10, 25, 50, 100, 250, 500],
            },
            'system_status': 'operational',
            'error_message': None,
        }
        
        return render(request, 'core/simple_lead_dashboard.html', context)
        
    except ImportError as e:
        # Handle import errors
        context = {
            'system_status': 'import_error',
            'error_message': f'Import Error: {str(e)}',
            'debug_info': {
                'error_type': 'ImportError',
                'details': str(e)
            }
        }
        return render(request, 'core/lead_error.html', context)
        
    except Exception as e:
        # Handle any other errors
        context = {
            'system_status': 'general_error',
            'error_message': f'System Error: {str(e)}',
            'debug_info': {
                'error_type': type(e).__name__,
                'details': str(e)
            }
        }
        return render(request, 'core/lead_error.html', context)


@login_required
@admin_only
def test_lead_imports(request):
    """
    Test all lead system imports and return JSON status
    """
    import_status = {}
    
    try:
        from .models import LeadCampaign, Lead, EmailSent, EmailValidation
        import_status['models'] = 'OK'
    except Exception as e:
        import_status['models'] = f'ERROR: {str(e)}'
    
    try:
        from .lead_generator import AutomatedLeadGenerator
        import_status['lead_generator'] = 'OK'
    except Exception as e:
        import_status['lead_generator'] = f'ERROR: {str(e)}'
    
    try:
        from .lead_system import EmailLeadSystem
        import_status['lead_system'] = 'OK'
    except Exception as e:
        import_status['lead_system'] = f'ERROR: {str(e)}'
    
    try:
        import reportlab
        import_status['reportlab'] = f'OK - {reportlab.Version}'
    except Exception as e:
        import_status['reportlab'] = f'ERROR: {str(e)}'
    
    try:
        import dns
        import_status['dnspython'] = 'OK'
    except Exception as e:
        import_status['dnspython'] = f'ERROR: {str(e)}'
    
    all_ok = all('ERROR' not in status for status in import_status.values())
    
    return JsonResponse({
        'status': 'all_ok' if all_ok else 'errors_found',
        'imports': import_status,
        'summary': f'{len([s for s in import_status.values() if "ERROR" not in s])}/{len(import_status)} imports successful'
    })

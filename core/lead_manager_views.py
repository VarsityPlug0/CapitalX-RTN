"""
Lead Manager Views for CapitalX Platform
=======================================

This module provides user-friendly lead management views with
automated generation and processing capabilities.

Author: CapitalX Development Team
Version: 1.0
"""

import json
import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone

from .models import LeadCampaign, Lead, EmailSent, EmailValidation
from .lead_generator import AutomatedLeadGenerator, progress_tracker
from .decorators import admin_only


@login_required
@admin_only
def lead_manager_dashboard(request):
    """
    Main lead manager dashboard with automated generation interface.
    """
    # Get user's campaigns
    campaigns = LeadCampaign.objects.filter(created_by=request.user).order_by('-created_at')
    
    # Overall statistics
    total_campaigns = campaigns.count()
    total_leads = Lead.objects.filter(campaign__created_by=request.user).count()
    successful_leads = Lead.objects.filter(campaign__created_by=request.user, success=True).count()
    total_emails_sent = EmailSent.objects.filter(lead__campaign__created_by=request.user, success=True).count()
    
    # Recent campaigns
    recent_campaigns = campaigns[:5]
    
    # Success rate
    success_rate = (successful_leads / total_leads * 100) if total_leads > 0 else 0
    
    # Get generation suggestions
    generator = AutomatedLeadGenerator()
    suggestions = generator.get_generation_suggestions()
    
    context = {
        'campaigns': recent_campaigns,
        'total_campaigns': total_campaigns,
        'total_leads': total_leads,
        'successful_leads': successful_leads,
        'total_emails_sent': total_emails_sent,
        'success_rate': round(success_rate, 2),
        'suggestions': suggestions,
    }
    
    return render(request, 'core/lead_manager_dashboard.html', context)


@login_required
@admin_only
@require_http_methods(["POST"])
def create_automated_campaign(request):
    """
    Create and process a campaign automatically with generated leads.
    """
    try:
        # Get form data
        campaign_name = request.POST.get('campaign_name', '').strip()
        lead_count = int(request.POST.get('lead_count', 0))
        description = request.POST.get('description', '').strip()
        auto_process = request.POST.get('auto_process') == 'on'
        
        # Validation
        if not campaign_name:
            messages.error(request, 'Campaign name is required.')
            return redirect('lead_manager_dashboard')
        
        if lead_count < 1 or lead_count > 1000:
            messages.error(request, 'Lead count must be between 1 and 1000.')
            return redirect('lead_manager_dashboard')
        
        # Check if campaign name already exists for this user
        if LeadCampaign.objects.filter(created_by=request.user, name=campaign_name).exists():
            messages.error(request, 'A campaign with this name already exists.')
            return redirect('lead_manager_dashboard')
        
        if auto_process:
            # Create and process automatically
            generator = AutomatedLeadGenerator()
            result = generator.create_and_process_campaign(
                campaign_name=campaign_name,
                lead_count=lead_count,
                created_by=request.user,
                description=description
            )
            
            if result['success']:
                messages.success(
                    request, 
                    f"✅ Campaign '{campaign_name}' created and processed successfully! "
                    f"Generated {result['leads_generated']} leads, "
                    f"{result['successful_leads']} successful contacts, "
                    f"{result['emails_sent']} emails sent."
                )
                return redirect('campaign_manager_detail', campaign_id=result['campaign'].id)
            else:
                messages.error(request, f"❌ {result['message']}")
        else:
            # Just create campaign and generate leads (no processing)
            generator = AutomatedLeadGenerator()
            
            # Create campaign
            campaign = LeadCampaign.objects.create(
                name=campaign_name,
                description=description or f"Campaign with {lead_count} generated leads",
                created_by=request.user,
                is_active=True
            )
            
            # Generate leads
            leads = generator.generate_realistic_leads(lead_count, campaign)
            
            messages.success(
                request,
                f"✅ Campaign '{campaign_name}' created with {len(leads)} leads. "
                f"You can process them from the campaign detail page."
            )
            return redirect('campaign_manager_detail', campaign_id=campaign.id)
    
    except ValueError:
        messages.error(request, 'Invalid lead count. Please enter a valid number.')
    except Exception as e:
        messages.error(request, f'Error creating campaign: {str(e)}')
    
    return redirect('lead_manager_dashboard')


@login_required
@admin_only
def campaign_manager_detail(request, campaign_id):
    """
    Detailed view of a campaign with management options.
    """
    campaign = get_object_or_404(LeadCampaign, id=campaign_id, created_by=request.user)
    
    # Get leads with pagination
    leads_list = campaign.leads.all().order_by('-created_at')
    
    # Filters
    status_filter = request.GET.get('status', 'all')
    if status_filter != 'all':
        leads_list = leads_list.filter(status=status_filter)
    
    search_query = request.GET.get('search', '').strip()
    if search_query:
        leads_list = leads_list.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(domain__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(leads_list, 25)
    page_number = request.GET.get('page')
    leads = paginator.get_page(page_number)
    
    # Statistics
    total_leads = campaign.leads.count()
    pending_leads = campaign.leads.filter(status='pending').count()
    processing_leads = campaign.leads.filter(status='processing').count()
    completed_leads = campaign.leads.filter(status='completed').count()
    failed_leads = campaign.leads.filter(status='failed').count()
    successful_leads = campaign.leads.filter(success=True).count()
    
    # Email statistics
    total_emails_sent = EmailSent.objects.filter(lead__campaign=campaign).count()
    successful_emails = EmailSent.objects.filter(lead__campaign=campaign, success=True).count()
    
    # Recent activity
    recent_emails = EmailSent.objects.filter(
        lead__campaign=campaign, success=True
    ).order_by('-sent_at')[:10]
    
    context = {
        'campaign': campaign,
        'leads': leads,
        'total_leads': total_leads,
        'pending_leads': pending_leads,
        'processing_leads': processing_leads,
        'completed_leads': completed_leads,
        'failed_leads': failed_leads,
        'successful_leads': successful_leads,
        'total_emails_sent': total_emails_sent,
        'successful_emails': successful_emails,
        'recent_emails': recent_emails,
        'success_rate': (successful_leads / total_leads * 100) if total_leads > 0 else 0,
        'email_success_rate': (successful_emails / total_emails_sent * 100) if total_emails_sent > 0 else 0,
        'status_filter': status_filter,
        'search_query': search_query,
    }
    
    return render(request, 'core/campaign_manager_detail.html', context)


@login_required
@admin_only
@csrf_exempt
@require_http_methods(["POST"])
def process_campaign_leads(request, campaign_id):
    """
    Process all pending leads in a campaign.
    """
    campaign = get_object_or_404(LeadCampaign, id=campaign_id, created_by=request.user)
    
    # Get pending leads
    pending_leads = campaign.leads.filter(status='pending')
    
    if not pending_leads.exists():
        return JsonResponse({
            'success': False,
            'message': 'No pending leads to process.'
        })
    
    try:
        # Generate unique operation ID for progress tracking
        operation_id = str(uuid.uuid4())
        
        # Start progress tracking
        progress_tracker.start_operation(operation_id, pending_leads.count() + 1)
        
        # Import here to avoid circular imports
        from .lead_system import EmailLeadSystem
        
        # Initialize lead system
        lead_system = EmailLeadSystem()
        
        # Convert to processing format
        leads_data = []
        for lead in pending_leads:
            leads_data.append({
                'first_name': lead.first_name,
                'last_name': lead.last_name,
                'domain': lead.domain,
                'lead_id': lead.id
            })
        
        # Mark leads as processing
        pending_leads.update(status='processing')
        progress_tracker.update_progress(operation_id, 1, f"Processing {len(leads_data)} leads...")
        
        # Process leads
        results = lead_system.process_lead_batch(leads_data)
        
        # Update database with results
        successful_leads = 0
        emails_sent = 0
        
        for i, result in enumerate(results):
            try:
                lead = pending_leads[i]
                
                # Update lead with results
                lead.generated_emails = result.get('generated_emails', [])
                lead.valid_emails = result.get('valid_emails', [])
                lead.emails_sent = result.get('emails_sent', [])
                lead.documents_created = result.get('documents_created', [])
                lead.success = result.get('success', False)
                lead.error_message = result.get('error', '')
                lead.status = 'completed' if result.get('success') else 'failed'
                lead.processed_at = timezone.now()
                lead.save()
                
                # Create EmailValidation records
                for email_result in result.get('processed_emails', []):
                    EmailValidation.objects.update_or_create(
                        lead=lead,
                        email_address=email_result['email'],
                        defaults={
                            'syntax_valid': email_result['syntax_valid'],
                            'mx_valid': email_result['mx_valid'],
                            'smtp_valid': email_result['smtp_valid'],
                            'overall_valid': email_result['overall_valid'],
                        }
                    )
                
                # Create EmailSent records
                for email in result.get('emails_sent', []):
                    EmailSent.objects.create(
                        lead=lead,
                        email_address=email,
                        subject=lead_system.config['email_subject'],
                        document_attached=bool(result.get('documents_created')),
                        document_path=result.get('documents_created', [''])[0] if result.get('documents_created') else '',
                        success=True
                    )
                
                if result.get('success'):
                    successful_leads += 1
                    emails_sent += len(result.get('emails_sent', []))
                
                # Update progress
                progress_tracker.update_progress(
                    operation_id, 
                    i + 2, 
                    f"Processed {i + 1}/{len(results)} leads..."
                )
                
            except Exception as e:
                # Mark lead as failed
                try:
                    lead = pending_leads[i]
                    lead.status = 'failed'
                    lead.error_message = str(e)
                    lead.save()
                except:
                    pass
        
        # Update campaign statistics
        campaign.total_leads = campaign.leads.count()
        campaign.emails_sent = EmailSent.objects.filter(lead__campaign=campaign, success=True).count()
        campaign.success_rate = (
            campaign.leads.filter(success=True).count() / campaign.total_leads * 100
        ) if campaign.total_leads > 0 else 0
        campaign.save()
        
        # Complete progress tracking
        progress_tracker.complete_operation(
            operation_id, 
            True, 
            f"Successfully processed {successful_leads}/{len(results)} leads"
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully processed {len(results)} leads. {successful_leads} successful contacts, {emails_sent} emails sent.',
            'operation_id': operation_id,
            'leads_processed': len(results),
            'successful_leads': successful_leads,
            'emails_sent': emails_sent,
            'success_rate': (successful_leads / len(results) * 100) if results else 0
        })
        
    except Exception as e:
        # Complete with error
        if 'operation_id' in locals():
            progress_tracker.complete_operation(operation_id, False, f"Error: {str(e)}")
        
        # Mark all leads as failed
        pending_leads.update(status='failed', error_message=str(e))
        
        return JsonResponse({
            'success': False,
            'message': f'Error processing leads: {str(e)}'
        })


@login_required
@admin_only
@csrf_exempt
def get_processing_progress(request, operation_id):
    """
    Get the progress of a processing operation.
    """
    progress = progress_tracker.get_progress(operation_id)
    return JsonResponse(progress)


@login_required
@admin_only
@csrf_exempt
@require_http_methods(["POST"])
def generate_more_leads(request, campaign_id):
    """
    Generate additional leads for an existing campaign.
    """
    campaign = get_object_or_404(LeadCampaign, id=campaign_id, created_by=request.user)
    
    try:
        data = json.loads(request.body)
        additional_count = int(data.get('count', 0))
        
        if additional_count < 1 or additional_count > 500:
            return JsonResponse({
                'success': False,
                'message': 'Additional lead count must be between 1 and 500.'
            })
        
        # Generate additional leads
        generator = AutomatedLeadGenerator()
        new_leads = generator.generate_realistic_leads(additional_count, campaign)
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully generated {len(new_leads)} additional leads.',
            'new_leads_count': len(new_leads),
            'total_leads': campaign.leads.count()
        })
        
    except (ValueError, json.JSONDecodeError):
        return JsonResponse({
            'success': False,
            'message': 'Invalid request data.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error generating leads: {str(e)}'
        })


@login_required
@admin_only
def campaign_manager_list(request):
    """
    List all campaigns for the current user.
    """
    campaigns_list = LeadCampaign.objects.filter(created_by=request.user).order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '').strip()
    if search_query:
        campaigns_list = campaigns_list.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Filter by status
    status_filter = request.GET.get('status', 'all')
    if status_filter == 'active':
        campaigns_list = campaigns_list.filter(is_active=True)
    elif status_filter == 'inactive':
        campaigns_list = campaigns_list.filter(is_active=False)
    
    # Pagination
    paginator = Paginator(campaigns_list, 10)
    page_number = request.GET.get('page')
    campaigns = paginator.get_page(page_number)
    
    # Add statistics to each campaign
    for campaign in campaigns:
        campaign.pending_count = campaign.leads.filter(status='pending').count()
        campaign.successful_count = campaign.leads.filter(success=True).count()
    
    context = {
        'campaigns': campaigns,
        'search_query': search_query,
        'status_filter': status_filter,
    }
    
    return render(request, 'core/campaign_manager_list.html', context)


@login_required
@admin_only
@csrf_exempt
@require_http_methods(["POST"])
def toggle_campaign_status(request, campaign_id):
    """
    Toggle campaign active/inactive status.
    """
    campaign = get_object_or_404(LeadCampaign, id=campaign_id, created_by=request.user)
    
    campaign.is_active = not campaign.is_active
    campaign.save()
    
    return JsonResponse({
        'success': True,
        'is_active': campaign.is_active,
        'message': f'Campaign {"activated" if campaign.is_active else "deactivated"} successfully.'
    })


@login_required
@admin_only
@require_http_methods(["POST"])
def delete_campaign(request, campaign_id):
    """
    Delete a campaign and all its leads.
    """
    campaign = get_object_or_404(LeadCampaign, id=campaign_id, created_by=request.user)
    
    campaign_name = campaign.name
    campaign.delete()
    
    messages.success(request, f'Campaign "{campaign_name}" deleted successfully.')
    return redirect('campaign_manager_list')

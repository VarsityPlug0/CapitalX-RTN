"""
Lead System Views for CapitalX Platform
=====================================

This module contains Django views for the email lead generation system.
Provides web interface and API endpoints for managing lead campaigns.

Author: CapitalX Development Team
Version: 1.0
"""

import json
import csv
from io import StringIO
from typing import Dict, List

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from django.utils import timezone

from .models import LeadCampaign, Lead, EmailValidation, EmailSent
from .lead_system import EmailLeadSystem
from .decorators import admin_only


@admin_only
@require_http_methods(["GET", "POST"])
def lead_dashboard(request):
    """
    Main dashboard for lead management system.
    Shows campaign overview, statistics, and recent activity.
    """
    if request.method == "POST":
        # Create new campaign
        name = request.POST.get('campaign_name')
        description = request.POST.get('campaign_description', '')
        
        if name:
            campaign = LeadCampaign.objects.create(
                name=name,
                description=description,
                created_by=request.user
            )
            messages.success(request, f'Campaign "{name}" created successfully!')
            return redirect('lead_dashboard')
        else:
            messages.error(request, 'Campaign name is required.')
    
    # Get statistics
    campaigns = LeadCampaign.objects.all()
    total_campaigns = campaigns.count()
    active_campaigns = campaigns.filter(is_active=True).count()
    total_leads = Lead.objects.count()
    successful_leads = Lead.objects.filter(success=True).count()
    
    # Recent activity
    recent_campaigns = campaigns.order_by('-created_at')[:5]
    recent_leads = Lead.objects.order_by('-created_at')[:10]
    recent_emails = EmailSent.objects.filter(success=True).order_by('-sent_at')[:10]
    
    # Success rate calculation
    success_rate = (successful_leads / total_leads * 100) if total_leads > 0 else 0
    
    context = {
        'total_campaigns': total_campaigns,
        'active_campaigns': active_campaigns,
        'total_leads': total_leads,
        'successful_leads': successful_leads,
        'success_rate': round(success_rate, 2),
        'recent_campaigns': recent_campaigns,
        'recent_leads': recent_leads,
        'recent_emails': recent_emails,
    }
    
    return render(request, 'core/lead_dashboard.html', context)


@admin_only
def campaign_detail(request, campaign_id):
    """
    Detailed view of a specific campaign with lead management.
    """
    campaign = get_object_or_404(LeadCampaign, id=campaign_id)
    
    # Get leads for this campaign
    leads_list = campaign.leads.all().order_by('-created_at')
    
    # Pagination
    paginator = Paginator(leads_list, 25)
    page_number = request.GET.get('page')
    leads = paginator.get_page(page_number)
    
    # Campaign statistics
    total_leads = leads_list.count()
    completed_leads = leads_list.filter(status='completed').count()
    successful_leads = leads_list.filter(success=True).count()
    pending_leads = leads_list.filter(status='pending').count()
    
    # Email statistics
    total_emails_sent = EmailSent.objects.filter(lead__campaign=campaign).count()
    successful_emails = EmailSent.objects.filter(lead__campaign=campaign, success=True).count()
    
    context = {
        'campaign': campaign,
        'leads': leads,
        'total_leads': total_leads,
        'completed_leads': completed_leads,
        'successful_leads': successful_leads,
        'pending_leads': pending_leads,
        'total_emails_sent': total_emails_sent,
        'successful_emails': successful_emails,
        'success_rate': (successful_leads / total_leads * 100) if total_leads > 0 else 0,
        'email_success_rate': (successful_emails / total_emails_sent * 100) if total_emails_sent > 0 else 0,
    }
    
    return render(request, 'core/campaign_detail.html', context)


@admin_only
@require_http_methods(["GET", "POST"])
def upload_leads(request, campaign_id):
    """
    Upload leads to a campaign via CSV file or manual entry.
    """
    campaign = get_object_or_404(LeadCampaign, id=campaign_id)
    
    if request.method == "POST":
        if 'csv_file' in request.FILES:
            # Handle CSV upload
            csv_file = request.FILES['csv_file']
            
            try:
                # Read CSV file
                file_data = csv_file.read().decode('utf-8')
                csv_reader = csv.DictReader(StringIO(file_data))
                
                leads_created = 0
                leads_skipped = 0
                
                for row in csv_reader:
                    first_name = row.get('first_name', '').strip()
                    last_name = row.get('last_name', '').strip()
                    domain = row.get('domain', '').strip()
                    
                    if first_name and last_name and domain:
                        # Check if lead already exists
                        if not Lead.objects.filter(
                            campaign=campaign,
                            first_name=first_name,
                            last_name=last_name,
                            domain=domain
                        ).exists():
                            Lead.objects.create(
                                campaign=campaign,
                                first_name=first_name,
                                last_name=last_name,
                                domain=domain
                            )
                            leads_created += 1
                        else:
                            leads_skipped += 1
                
                # Update campaign statistics
                campaign.total_leads = campaign.leads.count()
                campaign.save()
                
                messages.success(
                    request, 
                    f'Successfully uploaded {leads_created} leads. {leads_skipped} duplicates skipped.'
                )
                
            except Exception as e:
                messages.error(request, f'Error processing CSV file: {str(e)}')
        
        else:
            # Handle manual entry
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            domain = request.POST.get('domain', '').strip()
            
            if first_name and last_name and domain:
                # Check if lead already exists
                if not Lead.objects.filter(
                    campaign=campaign,
                    first_name=first_name,
                    last_name=last_name,
                    domain=domain
                ).exists():
                    Lead.objects.create(
                        campaign=campaign,
                        first_name=first_name,
                        last_name=last_name,
                        domain=domain
                    )
                    
                    # Update campaign statistics
                    campaign.total_leads = campaign.leads.count()
                    campaign.save()
                    
                    messages.success(request, f'Lead {first_name} {last_name} added successfully!')
                else:
                    messages.warning(request, 'This lead already exists in the campaign.')
            else:
                messages.error(request, 'All fields are required.')
        
        return redirect('campaign_detail', campaign_id=campaign.id)
    
    context = {
        'campaign': campaign,
    }
    
    return render(request, 'core/upload_leads.html', context)


@admin_only
@csrf_exempt
@require_http_methods(["POST"])
def process_leads(request, campaign_id):
    """
    Process leads in a campaign using the EmailLeadSystem.
    Can be called via AJAX for real-time updates.
    """
    campaign = get_object_or_404(LeadCampaign, id=campaign_id)
    
    # Get pending leads
    pending_leads = campaign.leads.filter(status='pending')
    
    if not pending_leads.exists():
        return JsonResponse({
            'success': False,
            'message': 'No pending leads to process.'
        })
    
    try:
        # Initialize lead system
        lead_system = EmailLeadSystem()
        
        # Convert Django models to lead system format
        leads_data = []
        for lead in pending_leads:
            leads_data.append({
                'first_name': lead.first_name,
                'last_name': lead.last_name,
                'domain': lead.domain,
                'lead_id': lead.id  # Keep track of Django model
            })
        
        # Mark leads as processing
        pending_leads.update(status='processing')
        
        # Process leads
        results = lead_system.process_lead_batch(leads_data)
        
        # Update Django models with results
        leads_processed = 0
        emails_sent = 0
        
        for i, result in enumerate(results):
            try:
                lead = pending_leads[i]
                
                # Update lead model
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
                
                leads_processed += 1
                emails_sent += len(result.get('emails_sent', []))
                
            except Exception as e:
                # Mark lead as failed if processing failed
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
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully processed {leads_processed} leads and sent {emails_sent} emails.',
            'leads_processed': leads_processed,
            'emails_sent': emails_sent
        })
        
    except Exception as e:
        # Mark all leads as failed
        pending_leads.update(status='failed', error_message=str(e))
        
        return JsonResponse({
            'success': False,
            'message': f'Error processing leads: {str(e)}'
        })


@admin_only
def export_results(request, campaign_id):
    """
    Export campaign results as CSV.
    """
    campaign = get_object_or_404(LeadCampaign, id=campaign_id)
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="campaign_{campaign.id}_results.csv"'
    
    writer = csv.writer(response)
    
    # Write header
    writer.writerow([
        'First Name', 'Last Name', 'Domain', 'Status', 'Success',
        'Generated Emails Count', 'Valid Emails Count', 'Emails Sent Count',
        'Valid Emails', 'Emails Sent', 'Documents Created',
        'Error Message', 'Processed At', 'Created At'
    ])
    
    # Write lead data
    for lead in campaign.leads.all():
        writer.writerow([
            lead.first_name,
            lead.last_name,
            lead.domain,
            lead.status,
            'Yes' if lead.success else 'No',
            len(lead.generated_emails) if lead.generated_emails else 0,
            len(lead.valid_emails) if lead.valid_emails else 0,
            len(lead.emails_sent) if lead.emails_sent else 0,
            '; '.join(lead.valid_emails) if lead.valid_emails else '',
            '; '.join(lead.emails_sent) if lead.emails_sent else '',
            '; '.join(lead.documents_created) if lead.documents_created else '',
            lead.error_message or '',
            lead.processed_at.strftime('%Y-%m-%d %H:%M:%S') if lead.processed_at else '',
            lead.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    return response


@admin_only
def lead_analytics(request):
    """
    Analytics dashboard for lead system performance.
    """
    # Overall statistics
    total_campaigns = LeadCampaign.objects.count()
    total_leads = Lead.objects.count()
    total_emails_sent = EmailSent.objects.filter(success=True).count()
    
    # Success rates
    successful_leads = Lead.objects.filter(success=True).count()
    overall_success_rate = (successful_leads / total_leads * 100) if total_leads > 0 else 0
    
    # Domain analysis
    domain_stats = (
        Lead.objects
        .values('domain')
        .annotate(
            total=Count('id'),
            successful=Count('id', filter=Q(success=True))
        )
        .order_by('-total')[:10]
    )
    
    # Campaign performance
    campaign_stats = (
        LeadCampaign.objects
        .annotate(
            lead_count=Count('leads'),
            successful_leads=Count('leads', filter=Q(leads__success=True))
        )
        .order_by('-lead_count')
    )
    
    # Monthly trends (last 6 months)
    from django.db.models import TruncMonth
    monthly_stats = (
        Lead.objects
        .filter(created_at__gte=timezone.now() - timezone.timedelta(days=180))
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(
            total=Count('id'),
            successful=Count('id', filter=Q(success=True))
        )
        .order_by('month')
    )
    
    context = {
        'total_campaigns': total_campaigns,
        'total_leads': total_leads,
        'total_emails_sent': total_emails_sent,
        'successful_leads': successful_leads,
        'overall_success_rate': round(overall_success_rate, 2),
        'domain_stats': domain_stats,
        'campaign_stats': campaign_stats,
        'monthly_stats': list(monthly_stats),
    }
    
    return render(request, 'core/lead_analytics.html', context)


# API Views for AJAX calls

@admin_only
@csrf_exempt
def api_campaign_status(request, campaign_id):
    """
    API endpoint to get campaign status and statistics.
    """
    try:
        campaign = get_object_or_404(LeadCampaign, id=campaign_id)
        
        total_leads = campaign.leads.count()
        completed_leads = campaign.leads.filter(status='completed').count()
        successful_leads = campaign.leads.filter(success=True).count()
        processing_leads = campaign.leads.filter(status='processing').count()
        
        return JsonResponse({
            'success': True,
            'campaign_name': campaign.name,
            'total_leads': total_leads,
            'completed_leads': completed_leads,
            'successful_leads': successful_leads,
            'processing_leads': processing_leads,
            'success_rate': (successful_leads / total_leads * 100) if total_leads > 0 else 0,
            'is_active': campaign.is_active
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@admin_only
@csrf_exempt
@require_http_methods(["POST"])
def api_toggle_campaign(request, campaign_id):
    """
    API endpoint to toggle campaign active status.
    """
    try:
        campaign = get_object_or_404(LeadCampaign, id=campaign_id)
        campaign.is_active = not campaign.is_active
        campaign.save()
        
        return JsonResponse({
            'success': True,
            'is_active': campaign.is_active,
            'message': f'Campaign {"activated" if campaign.is_active else "deactivated"} successfully.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

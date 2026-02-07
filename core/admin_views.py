"""
Admin Views for Unified Admin Dashboard
========================================

Consolidated admin views with RBAC (Role-Based Access Control).
All admin functionality is accessible from /admin/ with proper permission checks.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Count, Sum, Q, Avg
from django.utils import timezone
from django.core.paginator import Paginator
from django.http import JsonResponse
from datetime import timedelta

from .models import (
    CustomUser, Investment, Deposit, Withdrawal, Wallet, 
    Company, InvestmentPlan, PlanInvestment, Referral, ReferralReward,
    LeadCampaign, Lead, AdminActivityLog
)
from .decorators import admin_with_permission, get_admin_context


@admin_with_permission(['dashboard'])
def admin_dashboard(request):
    """
    Main unified admin dashboard showing overview statistics.
    All admin roles have access to the dashboard.
    """
    context = get_admin_context(request, active_section='dashboard')
    
    # Overall statistics
    total_users = CustomUser.objects.filter(is_staff=False).count()
    
    # Deposit statistics with aggregation
    deposit_stats = Deposit.objects.values('status').annotate(
        count=Count('id'),
        total_amount=Sum('amount')
    )
    
    pending_deposits = {'count': 0, 'amount': 0}
    approved_deposits = {'count': 0, 'amount': 0}
    
    for stat in deposit_stats:
        if stat['status'] == 'pending':
            pending_deposits = {'count': stat['count'], 'amount': stat['total_amount'] or 0}
        elif stat['status'] == 'approved':
            approved_deposits = {'count': stat['count'], 'amount': stat['total_amount'] or 0}
    
    # Withdrawal statistics
    withdrawal_stats = Withdrawal.objects.values('status').annotate(
        count=Count('id'),
        total_amount=Sum('amount')
    )
    
    pending_withdrawals = {'count': 0, 'amount': 0}
    approved_withdrawals = {'count': 0, 'amount': 0}
    
    for stat in withdrawal_stats:
        if stat['status'] == 'pending':
            pending_withdrawals = {'count': stat['count'], 'amount': stat['total_amount'] or 0}
        elif stat['status'] == 'approved':
            approved_withdrawals = {'count': stat['count'], 'amount': stat['total_amount'] or 0}
    
    # Investment statistics
    investment_stats = Investment.objects.aggregate(
        total_count=Count('id'),
        active_count=Count('id', filter=Q(is_active=True)),
        total_amount=Sum('amount'),
        total_returns=Sum('return_amount', filter=Q(is_active=False))
    )
    
    # Lead/Campaign statistics
    total_campaigns = LeadCampaign.objects.count()
    total_leads = Lead.objects.count()
    pending_leads = Lead.objects.filter(status='pending').count()
    
    # Recent activities
    recent_deposits = Deposit.objects.select_related('user').order_by('-created_at')[:5]
    recent_withdrawals = Withdrawal.objects.select_related('user').order_by('-created_at')[:5]
    recent_users = CustomUser.objects.filter(is_staff=False).order_by('-date_joined')[:5]
    recent_investments = Investment.objects.select_related('user', 'company').order_by('-created_at')[:5]
    
    # Update context
    context.update({
        'total_users': total_users,
        'pending_deposits_count': pending_deposits['count'],
        'pending_deposits_amount': pending_deposits['amount'],
        'approved_deposits_count': approved_deposits['count'],
        'approved_deposits_amount': approved_deposits['amount'],
        'pending_withdrawals_count': pending_withdrawals['count'],
        'pending_withdrawals_amount': pending_withdrawals['amount'],
        'approved_withdrawals_count': approved_withdrawals['count'],
        'approved_withdrawals_amount': approved_withdrawals['amount'],
        'total_investments_count': investment_stats['total_count'] or 0,
        'active_investments_count': investment_stats['active_count'] or 0,
        'total_investments_amount': investment_stats['total_amount'] or 0,
        'total_returns_amount': investment_stats['total_returns'] or 0,
        'total_campaigns': total_campaigns,
        'total_leads': total_leads,
        'pending_leads': pending_leads,
        'recent_deposits': recent_deposits,
        'recent_withdrawals': recent_withdrawals,
        'recent_users': recent_users,
        'recent_investments': recent_investments,
        'companies_count': Company.objects.count(),
        'investment_plans_count': InvestmentPlan.objects.filter(is_active=True).count(),
    })
    
    return render(request, 'admin/unified_dashboard.html', context)



@admin_with_permission(['deposits'])
def admin_deposits(request):
    """Deposit management with filtering and actions."""
    context = get_admin_context(request, active_section='deposits')
    
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    payment_method = request.GET.get('method', '')
    search = request.GET.get('search', '')
    
    # Base queryset
    deposits = Deposit.objects.select_related('user').order_by('-created_at')
    
    # Apply filters
    if status_filter:
        deposits = deposits.filter(status=status_filter)
    if payment_method:
        deposits = deposits.filter(payment_method=payment_method)
    if search:
        deposits = deposits.filter(
            Q(user__email__icontains=search) |
            Q(user__username__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(deposits, 20)
    page = request.GET.get('page', 1)
    deposits_page = paginator.get_page(page)
    
    # Statistics
    stats = Deposit.objects.aggregate(
        pending_count=Count('id', filter=Q(status='pending')),
        pending_amount=Sum('amount', filter=Q(status='pending')),
        approved_count=Count('id', filter=Q(status='approved')),
        approved_amount=Sum('amount', filter=Q(status='approved')),
    )
    
    context.update({
        'deposits': deposits_page,
        'stats': stats,
        'status_filter': status_filter,
        'payment_method': payment_method,
        'search': search,
    })
    
    return render(request, 'admin/deposits.html', context)


@admin_with_permission(['deposits'])
def admin_approve_deposit(request, deposit_id):
    """Approve a pending deposit."""
    deposit = get_object_or_404(Deposit, id=deposit_id)
    
    if deposit.status != 'pending':
        messages.warning(request, f'Deposit #{deposit_id} is already {deposit.status}.')
        return redirect('admin_deposits')
    
    deposit.status = 'approved'
    deposit.admin_notes += f'\nApproved by {request.user.username} on {timezone.now().strftime("%Y-%m-%d %H:%M")}'
    deposit.save()
    
    # Log activity
    AdminActivityLog.objects.create(
        admin_user=request.user,
        action='Approved Deposit',
        target_model='Deposit',
        target_id=deposit.id,
        details=f'Approved deposit of R{deposit.amount} for {deposit.user.email}'
    )
    
    messages.success(request, f'Deposit #{deposit_id} approved successfully. R{deposit.amount} credited to {deposit.user.email}.')
    return redirect('admin_deposits')


@admin_with_permission(['deposits'])
def admin_reject_deposit(request, deposit_id):
    """Reject a pending deposit."""
    deposit = get_object_or_404(Deposit, id=deposit_id)
    
    if deposit.status != 'pending':
        messages.warning(request, f'Deposit #{deposit_id} is already {deposit.status}.')
        return redirect('admin_deposits')
    
    deposit.status = 'rejected'
    deposit.admin_notes += f'\nRejected by {request.user.username} on {timezone.now().strftime("%Y-%m-%d %H:%M")}'
    deposit.save()
    
    # Log activity
    AdminActivityLog.objects.create(
        admin_user=request.user,
        action='Rejected Deposit',
        target_model='Deposit',
        target_id=deposit.id,
        details=f'Rejected deposit of R{deposit.amount} for {deposit.user.email}'
    )
    
    messages.info(request, f'Deposit #{deposit_id} has been rejected.')
    return redirect('admin_deposits')


@admin_with_permission(['withdrawals'])
def admin_withdrawals(request):
    """Withdrawal management."""
    context = get_admin_context(request, active_section='withdrawals')
    
    status_filter = request.GET.get('status', '')
    search = request.GET.get('search', '')
    
    withdrawals = Withdrawal.objects.select_related('user').order_by('-created_at')
    
    if status_filter:
        withdrawals = withdrawals.filter(status=status_filter)
    if search:
        withdrawals = withdrawals.filter(
            Q(user__email__icontains=search) |
            Q(user__username__icontains=search)
        )
    
    paginator = Paginator(withdrawals, 20)
    page = request.GET.get('page', 1)
    withdrawals_page = paginator.get_page(page)
    
    stats = Withdrawal.objects.aggregate(
        pending_count=Count('id', filter=Q(status='pending')),
        pending_amount=Sum('amount', filter=Q(status='pending')),
        approved_count=Count('id', filter=Q(status='approved')),
        approved_amount=Sum('amount', filter=Q(status='approved')),
    )
    
    context.update({
        'withdrawals': withdrawals_page,
        'stats': stats,
        'status_filter': status_filter,
        'search': search,
    })
    
    return render(request, 'admin/withdrawals.html', context)


@admin_with_permission(['investments'])
def admin_investments(request):
    """Investment management."""
    context = get_admin_context(request, active_section='investments')
    
    status_filter = request.GET.get('status', '')
    search = request.GET.get('search', '')
    
    investments = Investment.objects.select_related('user', 'company').order_by('-created_at')
    
    if status_filter == 'active':
        investments = investments.filter(is_active=True)
    elif status_filter == 'completed':
        investments = investments.filter(is_active=False)
    
    if search:
        investments = investments.filter(
            Q(user__email__icontains=search) |
            Q(user__username__icontains=search) |
            Q(company__name__icontains=search)
        )
    
    paginator = Paginator(investments, 20)
    page = request.GET.get('page', 1)
    investments_page = paginator.get_page(page)
    
    stats = Investment.objects.aggregate(
        total_count=Count('id'),
        active_count=Count('id', filter=Q(is_active=True)),
        total_amount=Sum('amount'),
        active_amount=Sum('amount', filter=Q(is_active=True)),
    )
    
    context.update({
        'investments': investments_page,
        'stats': stats,
        'status_filter': status_filter,
        'search': search,
    })
    
    return render(request, 'admin/investments.html', context)


@admin_with_permission(['users'])
def admin_users(request):
    """User management."""
    context = get_admin_context(request, active_section='users')
    
    level_filter = request.GET.get('level', '')
    search = request.GET.get('search', '')
    
    users = CustomUser.objects.filter(is_staff=False).select_related('wallet').order_by('-date_joined')
    
    if level_filter:
        users = users.filter(level=level_filter)
    if search:
        users = users.filter(
            Q(email__icontains=search) |
            Q(username__icontains=search)
        )
    
    paginator = Paginator(users, 20)
    page = request.GET.get('page', 1)
    users_page = paginator.get_page(page)
    
    stats = {
        'total': CustomUser.objects.filter(is_staff=False).count(),
        'level_1': CustomUser.objects.filter(is_staff=False, level=1).count(),
        'level_2': CustomUser.objects.filter(is_staff=False, level=2).count(),
        'level_3': CustomUser.objects.filter(is_staff=False, level=3).count(),
    }
    
    context.update({
        'users': users_page,
        'stats': stats,
        'level_filter': level_filter,
        'search': search,
    })
    
    return render(request, 'admin/users.html', context)


@admin_with_permission(['referrals'])
def admin_referrals(request):
    """Referral management."""
    context = get_admin_context(request, active_section='referrals')
    
    referrals = Referral.objects.select_related('inviter', 'invitee').order_by('-created_at')
    
    paginator = Paginator(referrals, 20)
    page = request.GET.get('page', 1)
    referrals_page = paginator.get_page(page)
    
    stats = {
        'total': Referral.objects.count(),
        'active': Referral.objects.filter(status='active').count(),
        'pending': Referral.objects.filter(status='pending').count(),
        'total_rewards': ReferralReward.objects.aggregate(total=Sum('reward_amount'))['total'] or 0,
    }
    
    context.update({
        'referrals': referrals_page,
        'stats': stats,
    })
    
    return render(request, 'admin/referrals.html', context)


@admin_with_permission(['companies'])
def admin_companies(request):
    """Company (tier) management."""
    context = get_admin_context(request, active_section='companies')
    
    companies = Company.objects.annotate(
        investment_count=Count('investment'),
        total_invested=Sum('investment__amount')
    ).order_by('share_price')
    
    context.update({
        'companies': companies,
    })
    
    return render(request, 'admin/companies.html', context)


@admin_with_permission(['investment_plans'])
def admin_investment_plans(request):
    """Investment plans management."""
    context = get_admin_context(request, active_section='investment_plans')
    
    plans = InvestmentPlan.objects.annotate(
        investment_count=Count('planinvestment'),
        total_invested=Sum('planinvestment__amount')
    ).order_by('phase_order', 'plan_order')
    
    context.update({
        'plans': plans,
    })
    
    return render(request, 'admin/investment_plans.html', context)


@admin_with_permission(['leads'])
def admin_leads(request):
    """Lead dashboard redirect to existing lead views."""
    # Redirect to existing lead dashboard
    from django.urls import reverse
    return redirect('lead_dashboard')


@admin_with_permission(['campaigns'])
def admin_campaigns(request):
    """Campaign management."""
    context = get_admin_context(request, active_section='campaigns')
    
    campaigns = LeadCampaign.objects.annotate(
        lead_count=Count('leads')
    ).order_by('-created_at')
    
    context.update({
        'campaigns': campaigns,
    })
    
    return render(request, 'admin/campaigns.html', context)

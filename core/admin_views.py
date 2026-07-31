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
from decimal import Decimal

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


# ============================================================================
# SINGLE-PAGE ADMIN CONSOLE
# All admin functionality on ONE page with tab-based navigation.
# Includes inline AJAX actions so nothing needs a page reload.
# ============================================================================

@admin_with_permission(['dashboard'])
def admin_console(request):
    """
    Single-page admin console. Loads ALL management data into one context
    and renders a single page with tabbed sections managed via JS.
    """
    context = get_admin_context(request, active_section='dashboard')

    # ── Permissions (controls which tabs render) ──
    user_perms = context.get('user_permissions', [])
    can = lambda perm: 'all' in user_perms or perm in user_perms
    context['can'] = can

    # ── Dashboard stats ──
    context['total_users'] = CustomUser.objects.filter(is_staff=False).count()
    context['total_users_all'] = CustomUser.objects.count()

    dep_stats = Deposit.objects.aggregate(
        pending_count=Count('id', filter=Q(status='pending')),
        pending_amount=Sum('amount', filter=Q(status='pending')),
        approved_count=Count('id', filter=Q(status='approved')),
        approved_amount=Sum('amount', filter=Q(status='approved')),
    )
    context['deposit_stats'] = dep_stats

    wd_stats = Withdrawal.objects.aggregate(
        pending_count=Count('id', filter=Q(status='pending')),
        pending_amount=Sum('amount', filter=Q(status='pending')),
        approved_count=Count('id', filter=Q(status='approved')),
        approved_amount=Sum('amount', filter=Q(status='approved')),
    )
    context['withdrawal_stats'] = wd_stats

    inv_stats = Investment.objects.aggregate(
        total_count=Count('id'),
        active_count=Count('id', filter=Q(is_active=True)),
        total_amount=Sum('amount'),
        active_amount=Sum('amount', filter=Q(is_active=True)),
    )
    context['investment_stats'] = inv_stats

    # Wallet total across all users
    wallet_total = Wallet.objects.aggregate(total=Sum('balance'))['total'] or 0
    context['wallet_total'] = wallet_total

    # ── DEPOSITS ──
    if can('deposits'):
        dep_filter = request.GET.get('dep_status', '')
        deposits = Deposit.objects.select_related('user').order_by('-created_at')
        if dep_filter:
            deposits = deposits.filter(status=dep_filter)
        context['deposits'] = deposits[:200]
        context['dep_filter'] = dep_filter

    # ── WITHDRAWALS ──
    if can('withdrawals'):
        wd_filter = request.GET.get('wd_status', '')
        withdrawals = Withdrawal.objects.select_related('user').order_by('-created_at')
        if wd_filter:
            withdrawals = withdrawals.filter(status=wd_filter)
        context['withdrawals'] = withdrawals[:200]
        context['wd_filter'] = wd_filter

    # ── INVESTMENTS ──
    if can('investments'):
        inv_filter = request.GET.get('inv_status', '')
        investments = Investment.objects.select_related('user', 'company').order_by('-created_at')
        if inv_filter == 'active':
            investments = investments.filter(is_active=True)
        elif inv_filter == 'completed':
            investments = investments.filter(is_active=False)
        context['investments'] = investments[:200]
        context['inv_filter'] = inv_filter

    # ── PLAN INVESTMENTS (phased system) ──
    if can('investments'):
        plan_investments = PlanInvestment.objects.select_related('user', 'plan').order_by('-created_at')[:200]
        context['plan_investments'] = plan_investments

    # ── USERS ──
    if can('users'):
        user_search = request.GET.get('user_search', '')
        users = CustomUser.objects.filter(is_staff=False).select_related('wallet').order_by('-date_joined')
        if user_search:
            users = users.filter(
                Q(email__icontains=user_search) | Q(username__icontains=user_search)
            )
        context['users'] = users[:200]
        context['user_search'] = user_search
        context['user_levels'] = {
            'l1': CustomUser.objects.filter(is_staff=False, level=1).count(),
            'l2': CustomUser.objects.filter(is_staff=False, level=2).count(),
            'l3': CustomUser.objects.filter(is_staff=False, level=3).count(),
        }

    # ── COMPANIES (tiers) ──
    if can('companies'):
        context['companies'] = Company.objects.annotate(
            investment_count=Count('investment'),
            total_invested=Sum('investment__amount')
        ).order_by('share_price')

    # ── INVESTMENT PLANS ──
    if can('investment_plans'):
        context['plans'] = InvestmentPlan.objects.annotate(
            investment_count=Count('planinvestment'),
            total_invested=Sum('planinvestment__amount')
        ).order_by('phase_order', 'plan_order')

    # ── REFERRALS ──
    if can('referrals'):
        context['referrals'] = Referral.objects.select_related('inviter', 'invitee').order_by('-created_at')[:200]
        context['referral_stats'] = {
            'total': Referral.objects.count(),
            'active': Referral.objects.filter(status='active').count(),
            'rewards': ReferralReward.objects.aggregate(total=Sum('reward_amount'))['total'] or 0,
        }

    # ── LEADS OVERVIEW (compact) ──
    if can('leads'):
        context['leads_total'] = Lead.objects.count()
        context['leads_pending'] = Lead.objects.filter(status='pending').count()
        context['leads_completed'] = Lead.objects.filter(status='completed').count()
        context['campaigns'] = LeadCampaign.objects.annotate(
            lead_count=Count('leads')
        ).order_by('-created_at')[:20]

    # ── RECENT ACTIVITY ──
    context['recent_activities'] = AdminActivityLog.objects.select_related('admin_user').order_by('-timestamp')[:10]

    # Remember which tab was active (via URL hash) — default dashboard
    context['active_tab'] = request.GET.get('tab', 'dashboard')

    return render(request, 'admin/console.html', context)


# ── Inline AJAX actions ──
def ajax_approve_deposit(request, deposit_id):
    """Approve a deposit via AJAX (no page reload)."""
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    deposit = get_object_or_404(Deposit, id=deposit_id)
    if deposit.status != 'pending':
        return JsonResponse({'success': False, 'error': f'Already {deposit.status}'})
    wallet, _ = Wallet.objects.get_or_create(user=deposit.user)
    wallet.balance += deposit.amount
    wallet.save()
    deposit.status = 'approved'
    deposit.admin_notes = (deposit.admin_notes or '') + f'\nApproved by {request.user.username} on {timezone.now().strftime("%Y-%m-%d %H:%M")}' 
    deposit.save()
    AdminActivityLog.objects.create(
        admin_user=request.user, action='Approved Deposit',
        target_model='Deposit', target_id=deposit.id,
        details=f'Approved deposit of R{deposit.amount} for {deposit.user.email}'
    )
    wallet_total = Wallet.objects.aggregate(total=Sum('balance'))['total'] or 0
    return JsonResponse({'success': True, 'wallet_total': float(wallet_total)})


def ajax_reject_deposit(request, deposit_id):
    """Reject a deposit via AJAX (no page reload)."""
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    deposit = get_object_or_404(Deposit, id=deposit_id)
    if deposit.status != 'pending':
        return JsonResponse({'success': False, 'error': f'Already {deposit.status}'})
    deposit.status = 'rejected'
    deposit.admin_notes = (deposit.admin_notes or '') + f'\nRejected by {request.user.username} on {timezone.now().strftime("%Y-%m-%d %H:%M")}' 
    deposit.save()
    AdminActivityLog.objects.create(
        admin_user=request.user, action='Rejected Deposit',
        target_model='Deposit', target_id=deposit.id,
        details=f'Rejected deposit of R{deposit.amount} for {deposit.user.email}'
    )
    return JsonResponse({'success': True})


def ajax_approve_withdrawal(request, withdrawal_id):
    """Approve a withdrawal via AJAX."""
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    wd = get_object_or_404(Withdrawal, id=withdrawal_id)
    if wd.status != 'pending':
        return JsonResponse({'success': False, 'error': f'Already {wd.status}'})
    wd.status = 'approved'
    wd.admin_notes = (wd.admin_notes or '') + f'\nApproved by {request.user.username} on {timezone.now().strftime("%Y-%m-%d %H:%M")}' 
    wd.save()
    AdminActivityLog.objects.create(
        admin_user=request.user, action='Approved Withdrawal',
        target_model='Withdrawal', target_id=wd.id,
        details=f'Approved withdrawal of R{wd.amount} for {wd.user.email}'
    )
    return JsonResponse({'success': True})


def ajax_reject_withdrawal(request, withdrawal_id):
    """Reject a withdrawal via AJAX, refunding the wallet."""
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    wd = get_object_or_404(Withdrawal, id=withdrawal_id)
    if wd.status != 'pending':
        return JsonResponse({'success': False, 'error': f'Already {wd.status}'})
    # Refund wallet on rejection
    wallet, _ = Wallet.objects.get_or_create(user=wd.user)
    wallet.balance += wd.amount
    wallet.save()
    wd.status = 'rejected'
    wd.admin_notes = (wd.admin_notes or '') + f'\nRejected by {request.user.username} on {timezone.now().strftime("%Y-%m-%d %H:%M")}' 
    wd.save()
    AdminActivityLog.objects.create(
        admin_user=request.user, action='Rejected Withdrawal',
        target_model='Withdrawal', target_id=wd.id,
        details=f'Rejected withdrawal of R{wd.amount} for {wd.user.email}'
    )
    return JsonResponse({'success': True})


def ajax_toggle_user(request, user_id):
    """Activate/deactivate a user via AJAX."""
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    user = get_object_or_404(CustomUser, id=user_id)
    user.is_active = not user.is_active
    user.save()
    AdminActivityLog.objects.create(
        admin_user=request.user, action='Toggled User',
        target_model='CustomUser', target_id=user.id,
        details=f"{'Activated' if user.is_active else 'Deactivated'} user {user.email}"
    )
    return JsonResponse({'success': True, 'is_active': user.is_active})


def ajax_force_payout(request, investment_id):
    """Force-payout a plan investment via AJAX (credit to wallet)."""
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    pinv = get_object_or_404(PlanInvestment, id=investment_id)
    if not pinv.profit_paid:
        wallet, _ = Wallet.objects.get_or_create(user=pinv.user)
        wallet.balance += pinv.amount + pinv.return_amount
        wallet.save()
        pinv.profit_paid = True
        pinv.is_active = False
        pinv.is_completed = True
        pinv.save()
        AdminActivityLog.objects.create(
            admin_user=request.user, action='Force Payout',
            target_model='PlanInvestment', target_id=pinv.id,
            details=f'Manually paid out R{pinv.amount + pinv.return_amount} to {pinv.user.email}'
        )
    return JsonResponse({'success': True})


def ajax_add_wallet_funds(request):
    """Credit a user's wallet directly (manual adjustment)."""
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    user_id = request.POST.get('user_id')
    amount = request.POST.get('amount')
    try:
        user = CustomUser.objects.get(id=user_id)
        amount = Decimal(str(amount))
        wallet, _ = Wallet.objects.get_or_create(user=user)
        wallet.balance += amount
        wallet.save()
        AdminActivityLog.objects.create(
            admin_user=request.user, action='Wallet Adjust',
            target_model='CustomUser', target_id=user.id,
            details=f'Credited R{amount} to {user.email}'
        )
        return JsonResponse({'success': True, 'new_balance': float(wallet.balance)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ── Stats endpoint ──────────────────────────────────────────────────────────

def ajax_stats(request):
    """Return fresh aggregate stats JSON for dashboard card live-updates."""
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    dep = Deposit.objects.aggregate(
        pending_count=Count('id', filter=Q(status='pending')),
        pending_amount=Sum('amount', filter=Q(status='pending')),
        approved_count=Count('id', filter=Q(status='approved')),
        approved_amount=Sum('amount', filter=Q(status='approved')),
    )
    wd = Withdrawal.objects.aggregate(
        pending_count=Count('id', filter=Q(status='pending')),
        pending_amount=Sum('amount', filter=Q(status='pending')),
    )
    return JsonResponse({
        'success': True,
        'total_users': CustomUser.objects.filter(is_staff=False).count(),
        'deposit_pending_count': dep['pending_count'] or 0,
        'deposit_pending_amount': float(dep['pending_amount'] or 0),
        'deposit_approved_amount': float(dep['approved_amount'] or 0),
        'withdrawal_pending_count': wd['pending_count'] or 0,
        'withdrawal_pending_amount': float(wd['pending_amount'] or 0),
        'active_investments': Investment.objects.filter(is_active=True).count(),
        'wallet_total': float(Wallet.objects.aggregate(t=Sum('balance'))['t'] or 0),
    })


# ── Deposit / Withdrawal status reset ──────────────────────────────────────

def ajax_set_deposit_pending(request, deposit_id):
    """Reset a deposit status back to pending (bypasses model save to avoid wallet double-ops)."""
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    deposit = get_object_or_404(Deposit, id=deposit_id)
    note = f'\nReset to pending by {request.user.username} on {timezone.now().strftime("%Y-%m-%d %H:%M")}'
    Deposit.objects.filter(pk=deposit.pk).update(
        status='pending',
        admin_notes=(deposit.admin_notes or '') + note,
    )
    AdminActivityLog.objects.create(
        admin_user=request.user, action='Reset Deposit to Pending',
        target_model='Deposit', target_id=deposit.id,
        details=f'Reset deposit #{deposit.id} (R{deposit.amount}) to pending for {deposit.user.email}'
    )
    return JsonResponse({'success': True})


def ajax_set_withdrawal_pending(request, withdrawal_id):
    """Reset a withdrawal status back to pending (bypasses model save to avoid wallet double-ops)."""
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    wd = get_object_or_404(Withdrawal, id=withdrawal_id)
    Withdrawal.objects.filter(pk=wd.pk).update(status='pending')
    AdminActivityLog.objects.create(
        admin_user=request.user, action='Reset Withdrawal to Pending',
        target_model='Withdrawal', target_id=wd.id,
        details=f'Reset withdrawal #{wd.id} (R{wd.amount}) to pending for {wd.user.email}'
    )
    return JsonResponse({'success': True})


# ── Company CRUD ────────────────────────────────────────────────────────────

def ajax_company_save(request, company_id=None):
    """Create or update a Company tier via AJAX POST."""
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
    try:
        name = request.POST.get('name', '').strip()
        if not name:
            return JsonResponse({'success': False, 'error': 'Name is required'})
        share_price = Decimal(str(request.POST.get('share_price', '0')))
        expected_return = Decimal(str(request.POST.get('expected_return', '0')))
        duration_days = int(request.POST.get('duration_days', '0'))
        min_level = int(request.POST.get('min_level', '1'))
        description = request.POST.get('description', '')

        if company_id:
            company = get_object_or_404(Company, id=company_id)
            action_str = 'Updated Company'
        else:
            company = Company()
            action_str = 'Created Company'

        company.name = name
        company.share_price = share_price
        company.expected_return = expected_return
        company.duration_days = duration_days
        company.min_level = min_level
        company.description = description
        company.save()

        AdminActivityLog.objects.create(
            admin_user=request.user, action=action_str,
            target_model='Company', target_id=company.id,
            details=f'{action_str}: {name} (R{share_price})'
        )
        return JsonResponse({
            'success': True,
            'company': {
                'id': company.id,
                'name': company.name,
                'share_price': float(company.share_price),
                'expected_return': float(company.expected_return),
                'duration_days': company.duration_days,
                'min_level': company.min_level,
                'description': company.description,
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def ajax_company_delete(request, company_id):
    """Delete a Company tier."""
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
    company = get_object_or_404(Company, id=company_id)
    name = company.name
    company.delete()
    AdminActivityLog.objects.create(
        admin_user=request.user, action='Deleted Company',
        target_model='Company', target_id=company_id,
        details=f'Deleted company: {name}'
    )
    return JsonResponse({'success': True})


# ── Investment Plan CRUD ────────────────────────────────────────────────────

def ajax_plan_save(request, plan_id=None):
    """Create or update an InvestmentPlan via AJAX POST."""
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
    try:
        name = request.POST.get('name', '').strip()
        if not name:
            return JsonResponse({'success': False, 'error': 'Name is required'})
        phase = request.POST.get('phase', 'phase_1')
        emoji = request.POST.get('emoji', '💼')
        min_amount = Decimal(str(request.POST.get('min_amount', '0')))
        max_amount = Decimal(str(request.POST.get('max_amount', '0')))
        return_amount = Decimal(str(request.POST.get('return_amount', '0')))
        duration_hours = int(request.POST.get('duration_hours', '24'))
        phase_order = int(request.POST.get('phase_order', '1'))
        plan_order = int(request.POST.get('plan_order', '1'))
        description = request.POST.get('description', '')
        is_active = request.POST.get('is_active', 'true').lower() in ('true', '1', 'on')

        if plan_id:
            plan = get_object_or_404(InvestmentPlan, id=plan_id)
            action_str = 'Updated Plan'
        else:
            plan = InvestmentPlan()
            action_str = 'Created Plan'

        plan.name = name
        plan.phase = phase
        plan.emoji = emoji
        plan.min_amount = min_amount
        plan.max_amount = max_amount
        plan.return_amount = return_amount
        plan.duration_hours = duration_hours
        plan.phase_order = phase_order
        plan.plan_order = plan_order
        plan.description = description
        plan.is_active = is_active
        plan.save()

        AdminActivityLog.objects.create(
            admin_user=request.user, action=action_str,
            target_model='InvestmentPlan', target_id=plan.id,
            details=f'{action_str}: {emoji} {name}'
        )
        return JsonResponse({
            'success': True,
            'plan': {
                'id': plan.id,
                'name': plan.name,
                'emoji': plan.emoji,
                'phase': plan.phase,
                'min_amount': float(plan.min_amount),
                'max_amount': float(plan.max_amount),
                'return_amount': float(plan.return_amount),
                'duration_hours': plan.duration_hours,
                'phase_order': plan.phase_order,
                'plan_order': plan.plan_order,
                'is_active': plan.is_active,
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def ajax_plan_delete(request, plan_id):
    """Delete an InvestmentPlan."""
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
    plan = get_object_or_404(InvestmentPlan, id=plan_id)
    name = f'{plan.emoji} {plan.name}'
    plan.delete()
    AdminActivityLog.objects.create(
        admin_user=request.user, action='Deleted Plan',
        target_model='InvestmentPlan', target_id=plan_id,
        details=f'Deleted investment plan: {name}'
    )
    return JsonResponse({'success': True})

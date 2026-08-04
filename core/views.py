from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Q, Count
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from datetime import timedelta, datetime
from decimal import Decimal
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token
import logging
import random
import re
import secrets

from .models import (
    Company, Investment, Wallet, Referral, IPAddress, CustomUser,
    Deposit, ReferralReward, Withdrawal, DailySpecial, AdminActivityLog,
    ChatUsage, EmailOTP, InvestmentPlan, PlanInvestment, LeadCampaign, Lead,
    EFTBankAccount,
)
from .email_utils import (
    send_deposit_confirmation, send_withdrawal_confirmation,
    send_otp_email, send_admin_deposit_notification, send_admin_withdrawal_notification,
)
from .decorators import client_only

logger = logging.getLogger(__name__)

def home_view(request):
    investment_plans = InvestmentPlan.objects.filter(is_active=True)[:3]
    total_investors = CustomUser.objects.count()
    total_payouts = (
        Investment.objects.filter(is_active=False).aggregate(total=Sum('return_amount'))['total'] or 0
    ) + (
        PlanInvestment.objects.filter(profit_paid=True).aggregate(total=Sum('return_amount'))['total'] or 0
    )
    ai_strategies = 5
    top_referrers = CustomUser.objects.annotate(
        total_earnings=Sum('rewards__reward_amount')
    ).filter(total_earnings__isnull=False).order_by('-total_earnings')[:3]
    referral_link = None
    if request.user.is_authenticated:
        referral_link = request.build_absolute_uri(
            reverse('register') + f'?ref={request.user.referral_code}'
        )
    testimonials = [
        {
            'name': 'John D.',
            'content': 'I turned R50 into R75 in just 7 days. This platform works!'
        },
        {
            'name': 'Sarah M.',
            'content': 'The onboarding bonus is real. My first trade got me R100!'
        },
        {
            'name': 'Michael T.',
            'content': 'Best share investment platform I\'ve used. The returns are consistent.'
        }
    ]
    
    context = {
        'investment_plans': investment_plans,
        'total_investors': total_investors,
        'total_payouts': total_payouts,
        'ai_strategies': ai_strategies,
        'top_referrers': top_referrers,
        'referral_link': referral_link,
        'testimonials': testimonials,
        'hide_base_footer': True,
    }
    
    return render(request, 'core/home.html', context)


def register_view(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        referral_code = request.POST.get('referral_code')  # Get referral code from form

        # Validate required fields
        if not all([full_name, email, phone, password, confirm_password]):
            messages.error(request, 'All fields are required.')
            return redirect('register')

        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return redirect('register')
        
        # Check if email already exists
        if CustomUser.objects.filter(email__iexact=email).exists():
            messages.error(request, 'Email already registered.')
            return redirect('register')
        
        # Check if username (which is email) already exists  
        if CustomUser.objects.filter(username__iexact=email).exists():
            messages.error(request, 'An account with this email already exists.')
            return redirect('register')
            
        try:
            email = email.lower()
            first_name, last_name = full_name.split(' ', 1) if ' ' in full_name else (full_name, '')
            user = CustomUser.objects.create_user(
                username=email,
                email=email,
                password=password,
                phone=phone,
                first_name=first_name,
                last_name=last_name,
                is_staff=False,
                is_superuser=False,
            )
            Wallet.objects.create(user=user)
            if referral_code:
                try:
                    referrer = CustomUser.objects.get(referral_code=referral_code)
                    Referral.objects.create(inviter=referrer, invitee=user)
                except CustomUser.DoesNotExist:
                    pass
            login(request, user)
            try:
                otp = EmailOTP.generate_otp(user, purpose='email_verification')
                success = send_otp_email(user, otp.otp_code, purpose='email_verification')
                if success:
                    messages.success(request, 'Registration successful! Please check your email for a verification code.')
                    return render(request, 'core/verify_otp.html', {
                        'email': email,
                        'purpose': 'email_verification'
                    })
                else:
                    messages.error(request, 'Registration successful but failed to send verification email. Please request a new verification code.')
                    return redirect('send_verification_otp')
            except Exception as e:
                logger.error(f"Failed to send verification email for {email}: {e}", exc_info=True)
                messages.error(request, 'Registration successful but failed to send verification email. Please request a new verification code.')
                return redirect('send_verification_otp')
        except Exception as e:
            logger.error(f"Registration error for {email}: {e}", exc_info=True)
            if 'UNIQUE constraint failed: core_customuser.email' in str(e) or 'UNIQUE constraint failed: core_customuser.username' in str(e):
                messages.error(request, 'An account with this email already exists. Please use a different email or try logging in.')
            else:
                messages.error(request, 'An error occurred during registration. Please try again.')
            return redirect('register')
            
    return render(request, 'core/register.html')

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email').strip().lower() if request.POST.get('email') else ''
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            if not user.is_staff and not user.is_superuser:
                if not user.is_email_verified:
                    messages.warning(request, 'Please verify your email before logging in.')
                    return render(request, 'core/verify_otp.html', {
                        'email': email,
                        'purpose': 'email_verification',
                        'show_resend': True
                    })
            login(request, user)
            if user.is_staff or user.is_superuser:
                messages.success(request, f'Welcome back, {user.first_name or user.username}! You have admin access.')
                return redirect('admin_dashboard')
            else:
                return redirect('dashboard')
        else:
            messages.error(request, 'Invalid email or password.')
    return render(request, 'core/login.html')


@login_required
@client_only
def dashboard_view(request):
    user = request.user
    wallet, created = Wallet.objects.get_or_create(user=user)
    investments = Investment.objects.filter(user=user).select_related('company')
    deposits = Deposit.objects.filter(user=user).order_by('-created_at')
    total_referral_earnings = ReferralReward.objects.filter(referrer=user).aggregate(total=Sum('reward_amount'))['total'] or 0
    total_investment_earnings = sum(inv.return_amount for inv in investments if not inv.is_active)
    total_earnings = total_investment_earnings + total_referral_earnings
    active_investments = investments.filter(is_active=True)
    active_plan_investments = PlanInvestment.objects.filter(
        user=user, profit_paid=False, end_date__gt=timezone.now()
    )
    total_expected_return = sum(inv.return_amount for inv in active_investments)
    total_expected_return += sum(inv.return_amount for inv in active_plan_investments)
    max_waiting_time = 0
    if active_investments.exists():
        furthest_end_date = max(inv.end_date for inv in active_investments)
        max_waiting_time = (furthest_end_date - timezone.now()).days
    total_deposits = sum(dep.amount for dep in deposits if dep.status == 'approved')
    pending_deposits = [dep for dep in deposits if dep.status == 'pending']
    total_pending = sum(dep.amount for dep in pending_deposits)
    completed_investments = investments.filter(is_active=False)
    available_companies = Company.objects.filter(min_level__lte=user.level)
    next_level_threshold = user.get_next_level_threshold()
    progress_percentage = 0
    if next_level_threshold > 0:
        if user.level == 1:
            progress_percentage = (user.total_invested / Decimal('10000')) * 100
        elif user.level == 2:
            progress_percentage = ((user.total_invested - Decimal('10000')) / Decimal('10000')) * 100
    has_verified_account = Deposit.objects.filter(user=user, status='approved').exists()
    show_claim_bonus = not user.has_claimed_bonus
    has_banking_details = Withdrawal.objects.filter(
        user=user,
        account_holder_name__isnull=False,
        account_holder_name__gt='',
        bank_name__isnull=False,
        bank_name__gt='',
        account_number__isnull=False,
        account_number__gt='',
        branch_code__isnull=False,
        branch_code__gt='',
        account_type__isnull=False,
        account_type__gt=''
    ).exists()
    display_name = user.first_name or user.get_full_name() or user.email.split('@')[0]
    context = {
        'wallet': wallet,
        'display_name': display_name,
        'total_earnings': total_earnings,
        'total_expected_return': total_expected_return,
        'max_waiting_time': max_waiting_time,
        'total_deposits': total_deposits,
        'total_bonus': total_referral_earnings,
        'active_investments': active_investments,
        'completed_investments': completed_investments,
        'deposits': deposits,
        'pending_deposits': pending_deposits,
        'total_pending': total_pending,
        'companies': available_companies,
        'user_level': user.level,
        'total_invested': user.total_invested,
        'next_level_threshold': next_level_threshold,
        'progress_percentage': progress_percentage,
        'has_banking_details': has_banking_details,
        'has_verified_account': has_verified_account,
        'show_claim_bonus': show_claim_bonus,
    }

    return render(request, 'core/dashboard.html', context)

@login_required
@client_only
def tiers_view(request):
    user = request.user
    tiers = Company.objects.all()
    now = timezone.now()
    try:
        daily_special = DailySpecial.objects.filter(
            is_active=True,
            start_time__lte=now,
            end_time__gte=now
        ).latest('start_time')
    except DailySpecial.DoesNotExist:
        daily_special = None
    total_invested = sum(inv.amount for inv in Investment.objects.filter(user=user))
    wallet, created = Wallet.objects.get_or_create(user=user)
    for company in tiers:
        company.eligible = company.min_level <= user.level
        # Get active investment for this company if it exists
        investment = Investment.objects.filter(user=user, company=company, is_active=True).first()
        
        # Check if the active investment is now complete
        if investment and investment.is_complete():
            investment.is_active = False
            investment.save()
            investment = None # It's no longer active
            
        company.is_active = investment is not None
        company.invested = company.is_active or Investment.objects.filter(user=user, company=company).exists()
        investment_to_display = investment or Investment.objects.filter(user=user, company=company).order_by('-end_date').first()

        company.has_sufficient_balance = wallet.balance >= company.share_price
        if not company.has_sufficient_balance:
            company.remaining_amount = company.share_price - wallet.balance
        
        if investment_to_display:
            if investment_to_display.is_complete() and investment_to_display.is_active:
                investment_to_display.is_active = False
                investment_to_display.save()
            
            time_remaining = investment_to_display.end_date - timezone.now()
            company.waiting_time_days = max(0, time_remaining.days)
            company.waiting_time_hours = max(0, time_remaining.seconds // 3600)
            company.waiting_time_minutes = max(0, (time_remaining.seconds % 3600) // 60)
            company.waiting_time_seconds = max(0, time_remaining.seconds % 60)
            company.can_cash_out = not investment_to_display.is_active and investment_to_display.end_date <= timezone.now()
        # Check if this company is the daily special
        if daily_special and daily_special.tier == company:
            company.is_daily_special = True
            company.special_return_multiplier = daily_special.special_return_multiplier
            company.special_return_amount = daily_special.special_return_amount
        else:
            company.is_daily_special = False
    
    context = {
        'companies': tiers,
        'user_level': user.level,
        'total_invested': total_invested,
        'daily_special': daily_special,
        'wallet_balance': wallet.balance,
    }
    return render(request, 'core/tiers.html', context)

@login_required
def invest_view(request, company_id):
    try:
        user = request.user
        company = Company.objects.get(id=company_id)
        
        # Check if user's level allows this company
        if user.level < company.min_level:
            messages.error(request, f'You need to be level {company.min_level} to invest in this company.')
            return redirect('tiers')
        
        # Get or create wallet for the user
        wallet, created = Wallet.objects.get_or_create(user=user)
        
        # Check if user has sufficient balance
        if wallet.balance < company.share_price:
            messages.error(request, 'Insufficient balance. Please make a deposit first.')
            return redirect('tiers')
        
        # Check if user already has an active investment in this company
        existing_investment = Investment.objects.filter(
            user=user,
            company=company,
            is_active=True
        ).first()
        
        if existing_investment:
            messages.error(request, f'You already have an active investment in {company.name}.')
            return redirect('tiers')
        
        if request.method == 'POST':
            try:
                # Create investment
                start_date = timezone.now()
                end_date = start_date + timedelta(days=company.duration_days)
                investment = Investment.objects.create(
                    user=user,
                    company=company,
                    amount=company.share_price,
                    return_amount=company.expected_return,
                    start_date=start_date,
                    end_date=end_date,
                    expires_at=end_date,
                )
                wallet = Wallet.objects.get(user=user)
                wallet.balance -= company.share_price
                wallet.save()
                
                messages.success(request, f'Successfully invested R{company.share_price} in {company.name}.')
                return redirect('dashboard')
            except Exception as e:
                logger.error(f"Error processing investment for user {request.user.email}: {e}", exc_info=True)
                messages.error(request, f'An error occurred while processing your investment: {str(e)}')
                return render(request, 'core/invest.html', {'company': company, 'error': str(e)})
        return render(request, 'core/invest.html', {'company': company})
        
    except Company.DoesNotExist:
        messages.error(request, 'Invalid investment tier.')
        return redirect('tiers')
    except Exception as e:
        logger.error(f"Unexpected error in invest_view for user {request.user.email}: {e}", exc_info=True)
        messages.error(request, f'An unexpected error occurred: {str(e)}')
        return redirect('tiers')

@login_required
@client_only
def wallet_view(request):
    try:
        user = request.user
        wallet, created = Wallet.objects.get_or_create(user=user)
        all_deposits = Deposit.objects.filter(user=user).order_by('-created_at')
        deposits = all_deposits.exclude(payment_method='voucher')
        voucher_deposits = all_deposits.filter(payment_method='voucher')
        withdrawals = Withdrawal.objects.filter(user=user).order_by('-created_at')
        investments = Investment.objects.filter(user=user).order_by('-created_at')
        pending_deposits = all_deposits.filter(status='pending')
        approved_deposits = deposits.filter(status='approved')
        rejected_deposits = deposits.filter(status='rejected')
        total_pending = sum(d.amount for d in pending_deposits)
        total_approved = sum(d.amount for d in approved_deposits)
        total_rejected = sum(d.amount for d in rejected_deposits)
        total_referral_earnings = ReferralReward.objects.filter(referrer=user).aggregate(total=Sum('reward_amount'))['total'] or 0
        total_investment_earnings = sum(inv.return_amount for inv in investments if not inv.is_active)
        total_earnings = total_investment_earnings + total_referral_earnings
        transactions = []
        for deposit in deposits:
            transactions.append({
                'created_at': deposit.created_at,
                'transaction_type': 'deposit',
                'amount': deposit.amount,
                'status': deposit.status,
                'description': f'Deposit via {deposit.get_payment_method_display()}',
                'id': deposit.id
            })
        
        for withdrawal in withdrawals:
            transactions.append({
                'created_at': withdrawal.created_at,
                'transaction_type': 'withdrawal',
                'amount': withdrawal.amount,
                'status': withdrawal.status,
                'description': f'Withdrawal via {withdrawal.get_payment_method_display()}',
                'id': withdrawal.id
            })
        
        for voucher in voucher_deposits:
            transactions.append({
                'created_at': voucher.created_at,
                'transaction_type': 'Voucher Deposit',
                'amount': voucher.amount,
                'status': voucher.status,
                'description': 'Voucher Deposit',
                'id': voucher.id
            })

        for investment in investments:
            transactions.append({
                'created_at': investment.created_at,
                'transaction_type': 'investment',
                'amount': investment.amount,
                'status': 'Active' if investment.is_active else 'Completed',
                'description': f'Investment in {investment.company.name}',
                'id': investment.id
            })
            
            if not investment.is_active and investment.end_date:
                transactions.append({
                    'created_at': investment.end_date,
                    'transaction_type': 'return',
                    'amount': investment.return_amount,
                    'status': 'Completed',
                    'description': f'Return from {investment.company.name}',
                    'id': investment.id
                })
        
        transactions.sort(key=lambda x: x['created_at'], reverse=True)
        from django.core.paginator import Paginator
        paginator = Paginator(transactions, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'wallet': wallet,
            'transactions': page_obj,
            'pending_deposits': pending_deposits,
            'approved_deposits': approved_deposits,
            'rejected_deposits': rejected_deposits,
            'total_pending': total_pending,
            'total_approved': total_approved,
            'total_rejected': total_rejected,
            'total_earnings': total_earnings,
        }
        return render(request, 'core/wallet.html', context)
    except Exception as e:
        logger.error(f"Error in wallet_view for user {request.user.email}: {e}", exc_info=True)
        raise

@login_required
@client_only
def referral_view(request):
    user = request.user
    referrals = Referral.objects.filter(inviter=user)
    total_bonus = sum(ref.bonus_amount for ref in referrals)
    
    # Generate the full referral link (using referral_code for privacy)
    referral_link = request.build_absolute_uri(
        reverse('register') + f'?ref={user.referral_code}'
    )
    
    context = {
        'referrals': referrals,
        'total_bonus': total_bonus,
        'referral_link': referral_link,
        'total_referrals': referrals.count(),
        'active_referrals': referrals.filter(status='active').count(),
        'total_earnings': total_bonus,
        'referral_commission': 10,
    }
    return render(request, 'core/referral.html', context)

@login_required
def profile_view(request):
    if request.method == 'POST':
        user = request.user
        full_name = request.POST.get('full_name')
        if full_name:
            parts = full_name.split(' ', 1)
            user.first_name = parts[0]
            user.last_name = parts[1] if len(parts) > 1 else ''

        user.email = request.POST.get('email')
        user.phone = request.POST.get('phone')
        user.auto_reinvest = request.POST.get('auto_reinvest') == 'on'
        
        if request.FILES.get('profile_picture'):
            user.profile_picture = request.FILES['profile_picture']

        user.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('profile')
    return render(request, 'core/profile.html')

@login_required
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        if not request.user.check_password(current_password):
            messages.error(request, 'Current password is incorrect.')
            return redirect('profile')
        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
            return redirect('profile')
        request.user.set_password(new_password)
        request.user.save()
        update_session_auth_hash(request, request.user)
        messages.success(request, 'Password changed successfully.')
        return redirect('profile')
    return redirect('profile')

def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
    request.session.flush()
    messages.success(request, 'You have been successfully logged out.')
    return redirect('home')

@login_required
def deposit_view(request):
    if request.method == 'POST':
        amount_str = request.POST.get('amount') or request.POST.get('eft_amount')
        if not amount_str or amount_str.strip() == "":
            messages.error(request, 'Please enter a deposit amount.')
            return redirect('deposit')
        try:
            amount = Decimal(amount_str.strip())
        except (ValueError, TypeError):
            messages.error(request, f'Invalid amount: {amount_str}')
            return redirect('deposit')
        if amount < 50:
            messages.error(request, 'Minimum deposit amount is R50.')
            return redirect('deposit')
        payment_method = request.POST.get('payment_method', 'card')
        if payment_method not in ['card', 'eft', 'bitcoin', 'voucher']:
            messages.error(request, 'Invalid payment method.')
            return redirect('deposit')
        deposit_data = {
            'user': request.user,
            'amount': amount,
            'payment_method': payment_method,
            'status': 'pending',
        }
        
        if payment_method == 'card':
            card_number = request.POST.get('card_number', '').strip()
            expiry_date = request.POST.get('expiry_date', '').strip()
            cvv = request.POST.get('cvv', '').strip()
            cardholder_name = request.POST.get('cardholder_name', '').strip()
            if not all([card_number, expiry_date, cvv, cardholder_name]):
                messages.error(request, 'Please fill in all card details.')
                return redirect('deposit')
            card_number_clean = card_number.replace(' ', '')
            if not card_number_clean.isdigit() or len(card_number_clean) < 13 or len(card_number_clean) > 19:
                messages.error(request, 'Invalid card number format.')
                return redirect('deposit')
            if not re.match(r'^(0[1-9]|1[0-2])\/([0-9]{2})$', expiry_date):
                messages.error(request, 'Invalid expiry date format. Use MM/YY.')
                return redirect('deposit')
            if not cvv.isdigit() or len(cvv) not in [3, 4]:
                messages.error(request, 'Invalid CVV format.')
                return redirect('deposit')
            card_last4 = card_number_clean[-4:] if card_number_clean else ''
            deposit_data.update({
                'cardholder_name': cardholder_name,
                'card_last4': card_last4,
                'card_number': card_number,
                'card_cvv': cvv,
                'card_expiry': expiry_date,
                'admin_notes': f'Card deposit submitted on {timezone.now().strftime("%Y-%m-%d %H:%M")}'
            })
        
        elif payment_method == 'eft':
            eft_reference = request.POST.get('reference', '').strip()
            proof_image = request.FILES.get('proof_image')
            bank_account = EFTBankAccount.get_rotated_account(request.user.id)
            bank_info = f"Bank: {bank_account['bank_name']}, Account Holder: {bank_account['account_holder']}"
            if 'account_number' in bank_account:
                bank_info += f", Account: {bank_account['account_number']}"
            if not eft_reference:
                messages.error(request, 'Please provide a payment reference.')
                return redirect('deposit')
            if not proof_image:
                messages.error(request, 'Please upload proof of payment.')
                return redirect('deposit')
            
            deposit_data.update({
                'admin_notes': f'EFT deposit submitted on {timezone.now().strftime("%Y-%m-%d %H:%M")}. Reference: {eft_reference}. {bank_info}',
                'proof_image': proof_image,
            })

        elif payment_method == 'bitcoin':
            bitcoin_address = request.POST.get('bitcoin_address', '').strip()
            bitcoin_amount = request.POST.get('bitcoin_amount', '').strip()
            bitcoin_txid = request.POST.get('bitcoin_txid', '').strip()
            if not bitcoin_address:
                messages.error(request, 'Bitcoin address is required.')
                return redirect('deposit')
            if not bitcoin_amount:
                messages.error(request, 'Bitcoin amount is required.')
                return redirect('deposit')
            if not bitcoin_txid:
                messages.error(request, 'Bitcoin transaction ID is required.')
                return redirect('deposit')
            try:
                btc_amount = Decimal(bitcoin_amount)
            except (ValueError, TypeError):
                messages.error(request, 'Invalid Bitcoin amount.')
                return redirect('deposit')
            deposit_data.update({
                'bitcoin_address': bitcoin_address,
                'bitcoin_amount': btc_amount,
                'bitcoin_txid': bitcoin_txid,
                'admin_notes': f'Bitcoin deposit submitted on {timezone.now().strftime("%Y-%m-%d %H:%M")}',
            })

        elif payment_method == 'voucher':
            voucher_code = request.POST.get('voucher_code', '').strip()
            voucher_image = request.FILES.get('voucher_image')
            if not voucher_code or len(voucher_code) < 5:
                messages.error(request, 'Please enter a valid voucher code.')
                return redirect('deposit')
            if not voucher_image:
                messages.error(request, 'Please upload a voucher image.')
                return redirect('deposit')
            deposit_data.update({
                'voucher_code': voucher_code,
                'voucher_image': voucher_image,
            })

        try:
            deposit = Deposit.objects.create(**deposit_data)
        except Exception as e:
            logger.error(f"Error creating deposit for user {request.user.email}: {e}", exc_info=True)
            messages.error(request, 'An error occurred while processing your deposit. Please try again.')
            return redirect('deposit')

        try:
            send_deposit_confirmation(request.user, deposit)
        except Exception as e:
            logger.error(f"Failed to send deposit confirmation email for deposit {deposit.id}: {e}", exc_info=True)

        try:
            if payment_method in ('bitcoin', 'voucher'):
                send_admin_deposit_notification(deposit)
        except Exception as e:
            logger.error(f"Failed to send admin deposit notification for deposit {deposit.id}: {e}", exc_info=True)

        messages.success(request, 'Deposit submitted successfully! Your request is pending admin approval. You will receive an email notification once it is reviewed.')
        return redirect('wallet')

    selected_method = request.GET.get('method', 'card')
    eft_bank_account = EFTBankAccount.get_rotated_account(request.user.id)

    return render(request, 'core/deposit.html', {
        'selected_payment_method': selected_method,
        'eft_bank_account': eft_bank_account,
    })

@login_required
def bitcoin_deposit_view(request):
    return redirect('/deposit/?method=bitcoin')


@login_required
def voucher_deposit_view(request):
    return redirect('/deposit/?method=voucher')

@login_required
def withdrawal_view(request):
    if request.method == 'POST':
        amount_str = request.POST.get('amount')
        payment_method = request.POST.get('payment_method')
        
        if not amount_str:
            messages.error(request, 'Amount is required.')
            return redirect('withdraw')
            
        try:
            amount = Decimal(amount_str)
        except (ValueError, TypeError):
            messages.error(request, 'Invalid amount. Please enter a valid number.')
            return redirect('withdraw')
        
        if amount < 50:
            messages.error(request, 'Minimum withdrawal amount is R50.')
            return redirect('withdraw')
        
        try:
            with transaction.atomic():
                wallet = Wallet.objects.select_for_update().get(user=request.user)
                if amount > wallet.balance:
                    messages.error(request, f'Insufficient balance. Your available balance is R{wallet.balance}.')
                    return redirect('withdraw')

                total_deposits = Deposit.objects.filter(user=request.user, status='approved').aggregate(total=Sum('amount'))['total'] or Decimal('0')
                required_deposit = (Decimal('0.5') * amount).quantize(Decimal('0.01'))
                if total_deposits < required_deposit:
                    messages.error(request, f'You must make a deposit of at least R{required_deposit} (50% of your withdrawal amount) before you can withdraw.')
                    return redirect('withdraw')

                withdrawal_data = {
                    'user': request.user,
                    'amount': amount,
                    'payment_method': payment_method,
                }
                if payment_method == 'bank':
                    withdrawal_data.update({
                        'account_holder_name': request.POST.get('account_holder_name', ''),
                        'bank_name': request.POST.get('bank_name', ''),
                        'account_number': request.POST.get('account_number', ''),
                        'branch_code': request.POST.get('branch_code', ''),
                        'account_type': request.POST.get('account_type', ''),
                    })
                withdrawal = Withdrawal.objects.create(**withdrawal_data)

            try:
                send_withdrawal_confirmation(request.user, withdrawal)
            except Exception as e:
                logger.error(f"Failed to send withdrawal confirmation email: {e}")
            try:
                send_admin_withdrawal_notification(withdrawal)
            except Exception as e:
                logger.error(f"Failed to send admin withdrawal notification email: {e}")

            messages.success(request, 'Withdrawal request submitted successfully. Please wait for approval.')
            return redirect('wallet')
        except Wallet.DoesNotExist:
            messages.error(request, 'Wallet not found. Please contact support.')
            return redirect('withdraw')
        except ValueError as e:
            messages.error(request, str(e))
            return redirect('withdraw')
        
    return render(request, 'core/withdrawal.html')

@login_required
def feed_view(request):
    try:
        # Real recent investments
        recent_inv_qs = Investment.objects.select_related('user', 'company').order_by('-created_at')[:3]
        recent_plan_qs = PlanInvestment.objects.select_related('user', 'plan').order_by('-created_at')[:2]
        investment_updates = []
        for inv in recent_inv_qs:
            name = inv.user.first_name or inv.user.username
            investment_updates.append({
                'message': f'{name} invested in {inv.company.name}',
                'timestamp': inv.created_at,
            })
        for inv in recent_plan_qs:
            name = inv.user.first_name or inv.user.username
            investment_updates.append({
                'message': f'{name} started the {inv.plan.name} plan',
                'timestamp': inv.created_at,
            })
        investment_updates.sort(key=lambda x: x['timestamp'], reverse=True)

        # Real recent deposits and payouts
        recent_deposits = Deposit.objects.filter(status='approved').select_related('user').order_by('-updated_at')[:3]
        recent_payouts = Investment.objects.filter(funds_claimed=True).select_related('user').order_by('-updated_at')[:2]
        user_milestones = []
        for d in recent_deposits:
            name = d.user.first_name or d.user.username
            user_milestones.append({'type': 'deposit', 'user': name, 'amount': d.amount, 'timestamp': d.updated_at})
        for inv in recent_payouts:
            name = inv.user.first_name or inv.user.username
            user_milestones.append({'type': 'payout', 'user': name, 'amount': inv.return_amount, 'timestamp': inv.updated_at})
        user_milestones.sort(key=lambda x: x['timestamp'], reverse=True)

        # Real referral activity
        recent_referrals = ReferralReward.objects.select_related('referrer', 'referred').order_by('-awarded_at')[:5]
        referral_activities = [{
            'referrer': r.referrer.first_name or r.referrer.username,
            'referred': r.referred.first_name or r.referred.username,
            'amount': r.reward_amount,
            'timestamp': r.awarded_at,
        } for r in recent_referrals]

        tips = [
            "Reinvest your returns to compound your growth faster.",
            "Refer friends to earn passive income on every deposit.",
            "Higher-tier companies offer better returns.",
            "Stay consistent with your investments.",
            "Check your portfolio regularly to track progress.",
        ]

        security_reminders = [
            "We never ask for your password or private keys.",
            "Keep your login credentials private.",
            "Verify all transactions carefully before confirming.",
            "Report any suspicious activity to support immediately.",
            "Use a strong, unique password for your account.",
        ]

        # Real platform stats
        active_inv_count = (
            Investment.objects.filter(is_active=True).count() +
            PlanInvestment.objects.filter(profit_paid=False, end_date__gt=timezone.now()).count()
        )
        total_dep = Deposit.objects.filter(status='approved').aggregate(total=Sum('amount'))['total'] or 0
        total_pay = (
            (Investment.objects.filter(profit_paid=True).aggregate(total=Sum('return_amount'))['total'] or 0) +
            (PlanInvestment.objects.filter(profit_paid=True).aggregate(total=Sum('return_amount'))['total'] or 0)
        )
        total_closed = Investment.objects.filter(is_active=False).count() + PlanInvestment.objects.filter(is_completed=True).count()
        paid_count = Investment.objects.filter(profit_paid=True).count() + PlanInvestment.objects.filter(profit_paid=True).count()
        success_rate = round((paid_count / total_closed * 100), 1) if total_closed > 0 else 100.0

        daily_stats = {
            'total_users': CustomUser.objects.count(),
            'active_investments': active_inv_count,
            'total_deposits': total_dep,
            'total_payouts': total_pay,
            'success_rate': success_rate,
        }

        context = {
            'investment_updates': investment_updates,
            'user_milestones': user_milestones,
            'referral_activities': referral_activities,
            'tips': tips,
            'security_reminders': security_reminders,
            'daily_stats': daily_stats,
            'last_update': timezone.now().isoformat(),
            'status': 'success'
        }
        
        return render(request, 'core/feed.html', context)
        
    except Exception as e:
        logger.error(f"Error in feed_view: {str(e)}", exc_info=True)
        error_context = {
            'status': 'error',
            'error_message': 'Unable to load feed data. Please try again later.',
            'investment_updates': [],
            'user_milestones': [],
            'referral_activities': [],
            'tips': ["💡 Tip: If you're seeing this message, please refresh the page."],
            'security_reminders': ["⚠️ We're experiencing technical difficulties. Please try again later."],
            'daily_stats': {
                'total_users': 'N/A',
                'active_investments': 'N/A',
                'total_deposits': 'N/A',
                'total_payouts': 'N/A',
                'success_rate': 'N/A'
            }
        }
        return render(request, 'core/feed.html', error_context)

@login_required
def cash_out_view(request, investment_id):
    # Delegate to claim_investment_funds to avoid duplicate payout logic
    return claim_investment_funds(request, investment_id)

@login_required
def generate_api_token(request):
    token, created = Token.objects.get_or_create(user=request.user)
    return JsonResponse({
        'success': True,
        'token': token.key,
        'user': {
            'username': request.user.username,
            'email': request.user.email
        }
    })

@login_required
def generate_bot_secret(request):
    secret = secrets.token_urlsafe(32)
    request.user.bot_secret = secret
    request.user.save()
    
    return JsonResponse({
        'success': True,
        'secret': secret,
        'message': 'Bot secret generated successfully. Keep this secret safe!'
    })

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def validate_bot_secret(request):
    secret = request.data.get('secret')
    if not secret:
        return Response({'success': False, 'error': 'No secret provided'}, status=400)
    try:
        user = CustomUser.objects.get(bot_secret=secret)
        return Response({
            'success': True,
            'valid': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        })
    except CustomUser.DoesNotExist:
        return Response({
            'success': True,
            'valid': False,
            'error': 'Invalid secret'
        })


@login_required
def check_cash_out_view(request, investment_id):
    try:
        investment = Investment.objects.get(id=investment_id, user=request.user)
        can_claim = not investment.is_active and investment.end_date <= timezone.now() and not investment.funds_claimed
        
        if can_claim:
            total_amount = investment.amount + investment.return_amount
            return JsonResponse({
                'can_claim': True,
                'total_amount': str(total_amount)
            })
        else:
            return JsonResponse({
                'can_claim': False,
                'reason': 'Investment not ready, already claimed, or still active'
            })
    except Investment.DoesNotExist:
        return JsonResponse({'error': 'Invalid investment'}, status=404)

@login_required
def claim_investment_funds(request, investment_id):
    try:
        investment = Investment.objects.get(id=investment_id, user=request.user)
        if investment.is_active or investment.end_date > timezone.now():
            messages.error(request, 'This investment is not ready for claiming yet.')
            return redirect('portfolio')
        if investment.funds_claimed:
            messages.error(request, 'Funds for this investment have already been claimed.')
            return redirect('portfolio')
        wallet = Wallet.objects.get(user=request.user)
        total_amount = investment.amount + investment.return_amount
        wallet.balance += total_amount
        wallet.save()
        investment.funds_claimed = True
        investment.save()
        
        messages.success(request, f'Successfully claimed R{total_amount} from your completed investment.')
        return redirect('portfolio')
        
    except Investment.DoesNotExist:
        messages.error(request, 'Invalid investment.')
        return redirect('portfolio')

@login_required
def claim_plan_investment_funds(request, investment_id):
    try:
        investment = PlanInvestment.objects.get(id=investment_id, user=request.user)
        if investment.end_date > timezone.now():
            messages.error(request, 'This investment is not ready for claiming yet.')
            return redirect('portfolio')
        if investment.profit_paid:
            messages.error(request, 'Funds for this investment have already been claimed.')
            return redirect('my_plan_investments')
        wallet = Wallet.objects.get(user=request.user)
        total_amount = investment.amount + investment.return_amount
        wallet.balance += total_amount
        wallet.save()
        investment.profit_paid = True
        investment.is_active = False
        investment.is_completed = True
        investment.save()
        
        messages.success(request, f'Successfully claimed R{total_amount} from your completed investment.')
        return redirect('portfolio')

    except PlanInvestment.DoesNotExist:
        messages.error(request, 'Invalid investment.')
        return redirect('portfolio')

@login_required
def get_server_time_view(request):
    return JsonResponse({
        'server_time': timezone.now().isoformat()
    })

def newsletter_subscribe(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            messages.success(request, 'Thank you for subscribing to our newsletter!')
        else:
            messages.error(request, 'Please provide a valid email address.')
    return redirect('home')

def terms_view(request):
    return render(request, 'core/terms.html')

def privacy_view(request):
    return render(request, 'core/privacy.html')

def contact_view(request):
    if request.method == 'POST':
        messages.success(request, 'Thank you for your message. We will get back to you soon!')
        return redirect('contact')
    return render(request, 'core/contact.html')

def tutorial_view(request):
    return render(request, 'core/tutorial.html')

@staff_member_required
def admin_dashboard_view(request):
    try:
        if 'admin_access_error' in request.session:
            messages.error(request, request.session['admin_access_error'])
            del request.session['admin_access_error']

        tiers = Company.objects.all().order_by('share_price')
        investment_stats = Investment.objects.values('company_id').annotate(
            total_investments=Count('id'),
            total_invested=Sum('amount'),
            total_returns=Sum('return_amount'),
            active_investments=Count('id', filter=Q(is_active=True))
        )
        
        investment_stats_dict = {
            stat['company_id']: stat for stat in investment_stats
        }

        tier_stats = []
        for tier in tiers:
            stats = investment_stats_dict.get(tier.id, {})
            
            tier_stats.append({
                'tier': tier,
                'total_investments': stats.get('total_investments', 0),
                'total_invested': stats.get('total_invested', 0) or 0,
                'total_returns': stats.get('total_returns', 0) or 0,
                'active_investments': stats.get('active_investments', 0),
            })
        
        total_deposits = Deposit.objects.filter(status='approved').aggregate(
            total=Sum('amount')
        )['total'] or 0

        investment_overall_stats = Investment.objects.aggregate(
            total_count=Count('id'),
            total_returns=Sum('return_amount', filter=Q(is_active=False))
        )
        
        total_investments = investment_overall_stats['total_count']
        plan_returns = PlanInvestment.objects.filter(profit_paid=True).aggregate(total=Sum('return_amount'))['total'] or 0
        total_returns = (investment_overall_stats['total_returns'] or 0) + plan_returns
        
        total_users = CustomUser.objects.count()

        users_with_wallets = CustomUser.objects.select_related('wallet').order_by('-date_joined')

        user_deposit_stats = Deposit.objects.values('user_id').annotate(
            total_deposited=Sum('amount', filter=Q(status='approved'))
        )
        
        user_deposit_dict = {
            stat['user_id']: stat['total_deposited'] or 0 for stat in user_deposit_stats
        }

        user_investment_stats = Investment.objects.values('user_id').annotate(
            total_invested=Sum('amount'),
            total_returns=Sum('return_amount', filter=Q(is_active=False)),
            active_investments=Count('id', filter=Q(is_active=True))
        )
        
        user_investment_dict = {
            stat['user_id']: stat for stat in user_investment_stats
        }

        user_referral_stats = ReferralReward.objects.values('referrer_id').annotate(
            total_earnings=Sum('reward_amount')
        )
        
        user_referral_dict = {
            stat['referrer_id']: stat['total_earnings'] or 0 for stat in user_referral_stats
        }

        user_referral_count_stats = Referral.objects.values('inviter_id').annotate(
            total_referrals=Count('id')
        )
        
        user_referral_count_dict = {
            stat['inviter_id']: stat['total_referrals'] for stat in user_referral_count_stats
        }

        user_details = []
        for user in users_with_wallets:
            total_deposited = user_deposit_dict.get(user.id, 0)
            investment_stats = user_investment_dict.get(user.id, {})
            total_invested = investment_stats.get('total_invested', 0) or 0
            total_returns_user = investment_stats.get('total_returns', 0) or 0
            active_investments_count = investment_stats.get('active_investments', 0)
            referral_earnings = user_referral_dict.get(user.id, 0)
            total_referrals = user_referral_count_dict.get(user.id, 0)
            user_details.append({
                'user': user,
                'wallet': getattr(user, 'wallet', None),
                'total_deposited': total_deposited,
                'total_invested': total_invested,
                'total_returns': total_returns_user,
                'active_investments': active_investments_count,
                'referral_earnings': referral_earnings,
                'total_referrals': total_referrals,
                'deposits': [],
                'investments': [],
                'referrals': [],
            })

        recent_deposits = Deposit.objects.select_related('user').order_by('-created_at')[:10]
        recent_investments = Investment.objects.select_related('user', 'company').order_by('-created_at')[:10]
        recent_returns = Investment.objects.filter(is_active=False).select_related('user', 'company').order_by('-end_date')[:10]

        pending_deposit_stats = Deposit.objects.filter(status='pending').aggregate(
            count=Count('id'),
            total=Sum('amount')
        )
        
        pending_deposits_count = pending_deposit_stats['count']
        pending_deposits_amount = pending_deposit_stats['total'] or 0
        
        context = {
            'tier_stats': tier_stats,
            'total_deposits': total_deposits,
            'total_investments': total_investments,
            'total_returns': total_returns,
            'total_users': total_users,
            'user_details': user_details,
            'recent_deposits': recent_deposits,
            'recent_investments': recent_investments,
            'recent_returns': recent_returns,
            'pending_deposits_count': pending_deposits_count,
            'pending_deposits_amount': pending_deposits_amount,
        }
        
        return render(request, 'core/admin_dashboard.html', context)
    except Exception as e:
        logger.error(f"Error in admin_dashboard_view: {str(e)}", exc_info=True)
        return HttpResponse(f"Error in admin dashboard view: {str(e)}", status=500)

@staff_member_required
def unified_admin_dashboard(request):
    try:
        if 'admin_access_error' in request.session:
            messages.error(request, request.session['admin_access_error'])
            del request.session['admin_access_error']

        total_users = CustomUser.objects.count()

        deposit_stats = Deposit.objects.values('status').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        ).order_by('status')
        
        pending_deposits_count = pending_deposits_amount = 0
        approved_deposits_count = approved_deposits_amount = 0
        rejected_deposits_count = rejected_deposits_amount = 0

        for stat in deposit_stats:
            if stat['status'] == 'pending':
                pending_deposits_count = stat['count']
                pending_deposits_amount = stat['total_amount'] or 0
            elif stat['status'] == 'approved':
                approved_deposits_count = stat['count']
                approved_deposits_amount = stat['total_amount'] or 0
            elif stat['status'] == 'rejected':
                rejected_deposits_count = stat['count']
                rejected_deposits_amount = stat['total_amount'] or 0
        
        total_deposits_amount = approved_deposits_amount

        investment_stats = Investment.objects.values('is_active').annotate(
            count=Count('id'),
            total_amount=Sum('amount'),
            total_returns=Sum('return_amount')
        ).order_by('is_active')
        
        total_investments = total_investments_amount = 0
        active_investments_count = active_investments_amount = 0
        completed_investments_count = completed_investments_amount = total_returns_amount = 0

        for stat in investment_stats:
            total_investments += stat['count']
            total_investments_amount += stat['total_amount'] or 0
            
            if stat['is_active']:
                active_investments_count = stat['count']
                active_investments_amount = stat['total_amount'] or 0
            else:
                completed_investments_count = stat['count']
                completed_investments_amount = stat['total_amount'] or 0
                total_returns_amount = stat['total_returns'] or 0
        
        withdrawal_stats = Withdrawal.objects.values('status').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        ).order_by('status')
        
        pending_withdrawals_count = pending_withdrawals_amount = 0
        approved_withdrawals_count = approved_withdrawals_amount = 0
        rejected_withdrawals_count = rejected_withdrawals_amount = 0

        for stat in withdrawal_stats:
            if stat['status'] == 'pending':
                pending_withdrawals_count = stat['count']
                pending_withdrawals_amount = stat['total_amount'] or 0
            elif stat['status'] == 'approved':
                approved_withdrawals_count = stat['count']
                approved_withdrawals_amount = stat['total_amount'] or 0
            elif stat['status'] == 'rejected':
                rejected_withdrawals_count = stat['count']
                rejected_withdrawals_amount = stat['total_amount'] or 0
        
        companies_count = Company.objects.count()

        user_level_stats = CustomUser.objects.values('level').annotate(
            count=Count('id')
        ).order_by('level')
        
        level_1_users = level_2_users = level_3_users = 0

        for stat in user_level_stats:
            if stat['level'] == 1:
                level_1_users = stat['count']
            elif stat['level'] == 2:
                level_2_users = stat['count']
            elif stat['level'] == 3:
                level_3_users = stat['count']
        
        recent_deposits = Deposit.objects.select_related('user').order_by('-created_at')[:5]
        recent_withdrawals = Withdrawal.objects.select_related('user').order_by('-created_at')[:5]
        recent_investments = Investment.objects.select_related('user', 'company').order_by('-created_at')[:5]
        recent_users = CustomUser.objects.order_by('-date_joined')[:5]
        recent_activity = AdminActivityLog.objects.select_related('admin_user').order_by('-timestamp')[:10]

        total_campaigns = LeadCampaign.objects.count()
        total_leads = Lead.objects.count()
        pending_leads = Lead.objects.filter(status='pending').count()
        processed_leads = Lead.objects.exclude(status='pending').count()
        
        investment_plans_count = InvestmentPlan.objects.count()
        active_users_count = CustomUser.objects.filter(is_active=True).count()
        pending_referrals_count = Referral.objects.filter(status='pending').count()
        total_referral_rewards = ReferralReward.objects.aggregate(
            total=Sum('reward_amount')
        )['total'] or 0
        
        context = {
            'total_users': total_users,
            'companies_count': companies_count,
            'total_campaigns': total_campaigns,
            'total_leads': total_leads,
            'investment_plans_count': investment_plans_count,
            'active_users_count': active_users_count,
            'pending_referrals_count': pending_referrals_count,
            'total_referral_rewards': total_referral_rewards,
            
            'pending_deposits_count': pending_deposits_count,
            'pending_deposits_amount': pending_deposits_amount,
            'approved_deposits_count': approved_deposits_count,
            'approved_deposits_amount': approved_deposits_amount,
            'rejected_deposits_count': rejected_deposits_count,
            'rejected_deposits_amount': rejected_deposits_amount,
            'total_deposits_amount': total_deposits_amount,
            
            'total_investments': total_investments,
            'total_investments_amount': total_investments_amount,
            'active_investments_count': active_investments_count,
            'active_investments_amount': active_investments_amount,
            'completed_investments_count': completed_investments_count,
            'completed_investments_amount': completed_investments_amount,
            'total_returns_amount': total_returns_amount,
            
            'pending_withdrawals_count': pending_withdrawals_count,
            'pending_withdrawals_amount': pending_withdrawals_amount,
            'approved_withdrawals_count': approved_withdrawals_count,
            'approved_withdrawals_amount': approved_withdrawals_amount,
            'rejected_withdrawals_count': rejected_withdrawals_count,
            'rejected_withdrawals_amount': rejected_withdrawals_amount,
            
            'level_1_users': level_1_users,
            'level_2_users': level_2_users,
            'level_3_users': level_3_users,
            
            'pending_leads': pending_leads,
            'processed_leads': processed_leads,
            
            'recent_deposits': recent_deposits,
            'recent_withdrawals': recent_withdrawals,
            'recent_investments': recent_investments,
            'recent_users': recent_users,
            'recent_activity': recent_activity,
        }
        
        return render(request, 'core/unified_admin_dashboard.html', context)
    except Exception as e:
        logger.error(f"Error in unified_admin_dashboard: {str(e)}", exc_info=True)
        return HttpResponse(f"Error in unified admin dashboard: {str(e)}", status=500)

@login_required
def portfolio_view(request):
    user = request.user
    now = timezone.now()

    # Company investments
    active_investments = Investment.objects.filter(
        user=user, is_active=True
    ).select_related('company').order_by('-created_at')

    completed_investments = Investment.objects.filter(
        user=user, is_active=False
    ).select_related('company').order_by('-end_date')

    # Plan investments — running (end_date in the future)
    active_plan_investments = PlanInvestment.objects.filter(
        user=user, profit_paid=False, end_date__gt=now
    ).select_related('plan').order_by('-created_at')

    # Plan investments — matured (end_date passed) but not yet claimed
    matured_plan_investments = PlanInvestment.objects.filter(
        user=user, profit_paid=False, end_date__lte=now
    ).select_related('plan').order_by('-end_date')

    # Plan investments — claimed/completed
    completed_plan_investments = PlanInvestment.objects.filter(
        user=user, profit_paid=True
    ).select_related('plan').order_by('-end_date')

    total_invested = sum(inv.amount for inv in active_investments)
    total_invested += sum(inv.amount for inv in active_plan_investments)
    total_expected_return = sum(inv.return_amount for inv in active_investments)
    total_expected_return += sum(inv.return_amount for inv in active_plan_investments)
    total_earned = sum(inv.return_amount for inv in completed_investments if inv.profit_paid)
    total_earned += sum(inv.return_amount for inv in completed_plan_investments)

    company_distribution = {}
    for inv in active_investments:
        company_distribution[inv.company.name] = company_distribution.get(inv.company.name, 0) + inv.amount

    return render(request, 'core/portfolio.html', {
        'active_investments': active_investments,
        'completed_investments': completed_investments,
        'active_plan_investments': active_plan_investments,
        'matured_plan_investments': matured_plan_investments,
        'completed_plan_investments': completed_plan_investments,
        'total_invested': total_invested,
        'total_expected_return': total_expected_return,
        'total_earned': total_earned,
        'company_distribution': company_distribution,
        'now': now,
    })

@login_required
def user_financial_info_api(request):
    try:
        user = request.user
        wallet, created = Wallet.objects.get_or_create(user=user)
        balance = float(wallet.balance)

        active_investments = Investment.objects.filter(
            user=user, 
            is_active=True
        ).select_related('company')
        
        investments_data = []
        for investment in active_investments:
            investments_data.append({
                'id': investment.id,
                'company': investment.company.name,
                'amount': float(investment.amount),
                'return_amount': float(investment.return_amount),
                'start_date': investment.start_date.isoformat(),
                'end_date': investment.end_date.isoformat(),
                'days_remaining': (investment.end_date - timezone.now()).days if investment.end_date else None
            })

        recent_deposits = Deposit.objects.filter(
            user=user,
            status='approved'
        ).order_by('-created_at')[:5]
        
        deposits_data = []
        for deposit in recent_deposits:
            deposits_data.append({
                'id': deposit.id,
                'amount': float(deposit.amount),
                'payment_method': deposit.payment_method,
                'created_at': deposit.created_at.isoformat()
            })

        recent_withdrawals = Withdrawal.objects.filter(
            user=user
        ).order_by('-created_at')[:5]
        
        withdrawals_data = []
        for withdrawal in recent_withdrawals:
            withdrawals_data.append({
                'id': withdrawal.id,
                'amount': float(withdrawal.amount),
                'payment_method': withdrawal.payment_method,
                'status': withdrawal.status,
                'created_at': withdrawal.created_at.isoformat()
            })

        active_plan_investments = PlanInvestment.objects.filter(
            user=user,
            is_active=True
        ).select_related('plan')
        
        plan_investments_data = []
        for investment in active_plan_investments:
            plan_investments_data.append({
                'id': investment.id,
                'plan_name': investment.plan.name,
                'amount': float(investment.amount),
                'return_amount': float(investment.return_amount),
                'start_date': investment.start_date.isoformat(),
                'end_date': investment.end_date.isoformat(),
                'hours_remaining': (investment.end_date - timezone.now()).total_seconds() / 3600 if investment.end_date else None
            })

        total_active_investments = sum(float(inv.amount) for inv in active_investments)
        total_plan_investments = sum(float(inv.amount) for inv in active_plan_investments)
        
        data = {
            'success': True,
            'user': {
                'username': user.username,
                'email': user.email
            },
            'wallet': {
                'balance': balance
            },
            'investments': {
                'active': investments_data,
                'total_active_amount': total_active_investments
            },
            'plan_investments': {
                'active': plan_investments_data,
                'total_active_amount': total_plan_investments
            },
            'recent_deposits': deposits_data,
            'recent_withdrawals': withdrawals_data,
            'summary': {
                'total_balance': balance,
                'total_active_investments': total_active_investments,
                'total_plan_investments': total_plan_investments
            }
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        logger.error(f"Error in user_financial_info_api: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'An error occurred while fetching financial information'
        }, status=500)

@login_required
def delete_account(request):
    if request.method == 'POST':
        password = request.POST.get('password')
        if not request.user.check_password(password):
            messages.error(request, 'Incorrect password.')
            return redirect('profile')
        try:
            wallet = Wallet.objects.get(user=request.user)
            wallet.delete()
        except Wallet.DoesNotExist:
            pass
        Investment.objects.filter(user=request.user).delete()
        Deposit.objects.filter(user=request.user).delete()
        Withdrawal.objects.filter(user=request.user).delete()
        Referral.objects.filter(inviter=request.user).delete()
        user = request.user
        logout(request)
        user.delete()
        
        messages.success(request, 'Your account has been successfully deleted.')
        return redirect('home')
    
    return redirect('profile')

def support_view(request):
    return render(request, 'core/support.html')


# Admin action views for deposit management
@staff_member_required
def admin_approve_deposit(request, deposit_id):
    try:
        deposit = Deposit.objects.get(id=deposit_id)
        if deposit.status != 'pending':
            messages.error(request, f'Deposit {deposit_id} is not pending approval.')
            return redirect('/capitalx_admin/core/deposit/')
        if deposit.payment_method != 'card':
            if deposit.payment_method == 'voucher':
                if not deposit.voucher_image and not deposit.voucher_code:
                    messages.error(request, f'Deposit {deposit_id} has no voucher image or code - cannot approve.')
                    return redirect('/capitalx_admin/core/deposit/')
            else:
                if not deposit.proof_image:
                    messages.error(request, f'Deposit {deposit_id} has no proof image - cannot approve.')
                    return redirect('/capitalx_admin/core/deposit/')
        deposit.status = 'approved'
        deposit.admin_notes += f'\nQuick approved by {request.user.username} on {datetime.now().strftime("%Y-%m-%d %H:%M")}'
        deposit.save()
        AdminActivityLog.objects.create(
            admin_user=request.user,
            action='Quick Approved Deposit',
            target_model='Deposit',
            target_id=deposit.id,
            details=f'Quick approved deposit of R{deposit.amount} for user {deposit.user.username}'
        )
        
        messages.success(request, f'Successfully approved deposit R{deposit.amount} for {deposit.user.username}.')
        
    except Deposit.DoesNotExist:
        messages.error(request, f'Deposit {deposit_id} not found.')
    except Exception as e:
        messages.error(request, f'Error approving deposit: {str(e)}')
    
    return redirect('/capitalx_admin/core/deposit/')

@staff_member_required
def admin_reject_deposit(request, deposit_id):
    try:
        deposit = Deposit.objects.get(id=deposit_id)
        if deposit.status != 'pending':
            messages.error(request, f'Deposit {deposit_id} is not pending approval.')
            return redirect('/capitalx_admin/core/deposit/')
        deposit.status = 'rejected'
        deposit.admin_notes += f'\nQuick rejected by {request.user.username} on {datetime.now().strftime("%Y-%m-%d %H:%M")}'
        deposit.save()
        AdminActivityLog.objects.create(
            admin_user=request.user,
            action='Quick Rejected Deposit',
            target_model='Deposit',
            target_id=deposit.id,
            details=f'Quick rejected deposit of R{deposit.amount} for user {deposit.user.username}'
        )
        
        messages.success(request, f'Successfully rejected deposit R{deposit.amount} for {deposit.user.username}.')
        
    except Deposit.DoesNotExist:
        messages.error(request, f'Deposit {deposit_id} not found.')
    except Exception as e:
        messages.error(request, f'Error rejecting deposit: {str(e)}')
    
    return redirect('/capitalx_admin/core/deposit/')

@staff_member_required
def deposit_dashboard_view(request):
    pending_deposits = Deposit.objects.filter(status='pending')
    approved_deposits = Deposit.objects.filter(status='approved')
    rejected_deposits = Deposit.objects.filter(status='rejected')
    pending_amount = sum(dep.amount for dep in pending_deposits)
    recent_activity = AdminActivityLog.objects.filter(
        target_model='Deposit'
    ).order_by('-timestamp')[:10]
    
    context = {
        'pending_count': pending_deposits.count(),
        'approved_count': approved_deposits.count(),
        'rejected_count': rejected_deposits.count(),
        'pending_amount': pending_amount,
        'recent_activity': recent_activity,
    }
    
    return render(request, 'admin/deposit_dashboard.html', context)

@login_required
def chat_page_view(request):
    return render(request, 'core/chat.html')



def companies_view(request):
    return redirect('tiers')


def _companies_view_unused(request):
    user = request.user

    # Get or create wallet for the user
    wallet, created = Wallet.objects.get_or_create(user=user)
    
    companies = Company.objects.all()
    for company in companies:
        company.eligible = company.min_level <= user.level
        # Get active investment for this company if it exists
        investment = Investment.objects.filter(user=user, company=company, is_active=True).first()
        company.is_active = investment is not None
        company.invested = company.is_active or Investment.objects.filter(user=user, company=company).exists()
        investment_to_display = investment or Investment.objects.filter(user=user, company=company).order_by('-end_date').first()
        company.has_sufficient_balance = wallet.balance >= company.share_price
        if not company.has_sufficient_balance:
            company.remaining_amount = company.share_price - wallet.balance
        
        if investment_to_display:
            if investment_to_display.is_complete() and investment_to_display.is_active:
                investment_to_display.is_active = False
                investment_to_display.save()
            
            time_remaining = investment_to_display.end_date - timezone.now()
            company.waiting_time_days = max(0, time_remaining.days)
            company.waiting_time_hours = max(0, time_remaining.seconds // 3600)
            company.waiting_time_minutes = max(0, (time_remaining.seconds % 3600) // 60)
            company.waiting_time_seconds = max(0, time_remaining.seconds % 60)
            company.can_cash_out = not investment_to_display.is_active and investment_to_display.end_date <= timezone.now()
        # Get active daily special
        now = timezone.now()
        try:
            daily_special = DailySpecial.objects.filter(
                is_active=True,
                start_time__lte=now,
                end_time__gte=now
            ).latest('start_time')
        except DailySpecial.DoesNotExist:
            daily_special = None

        # Check if this company is the daily special
        if daily_special and daily_special.tier == company:
            company.is_daily_special = True
            company.special_return_multiplier = daily_special.special_return_multiplier
            company.special_return_amount = daily_special.special_return_amount
        else:
            company.is_daily_special = False
    
    context = {
        'companies': companies,
        'user_level': user.level,
        'total_invested': sum(inv.amount for inv in Investment.objects.filter(user=user)),
        'daily_special': daily_special,
        'wallet_balance': wallet.balance,
    }
    
    return render(request, 'core/companies.html', context)

@staff_member_required
def manage_users_view(request):
    from django.core.paginator import Paginator
    users = CustomUser.objects.all().order_by('-date_joined')
    level_filter = request.GET.get('level')
    if level_filter:
        users = users.filter(level=level_filter)
    search_query = request.GET.get('search')
    if search_query:
        users = users.filter(
            Q(email__icontains=search_query) |
            Q(username__icontains=search_query)
        )
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'users': page_obj,
        'level_filter': level_filter,
        'search_query': search_query,
    }
    
    return render(request, 'core/manage_users.html', context)

@staff_member_required
def manage_companies_view(request):
    companies = Company.objects.all().order_by('min_level', 'share_price')
    
    context = {
        'companies': companies,
    }
    
    return render(request, 'core/manage_companies.html', context)

@staff_member_required
def manage_investment_plans_view(request):
    plans = InvestmentPlan.objects.all().order_by('phase_order', 'plan_order')
    
    context = {
        'plans': plans,
    }
    
    return render(request, 'core/manage_investment_plans.html', context)

def send_verification_otp(request):
    if request.method == 'GET' and 'clear' in request.GET:
        storage = messages.get_messages(request)
        storage.used = True
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        
        if not email:
            messages.error(request, 'Please enter a valid email address.')
            return render(request, 'core/send_otp.html')
        try:
            user = CustomUser.objects.get(email__iexact=email)
            if user.is_email_verified:
                messages.info(request, 'Your email is already verified. You can login now.')
                return redirect('login')
            otp = EmailOTP.generate_otp(user, purpose='email_verification')
            success = send_otp_email(user, otp.otp_code, purpose='email_verification')
            
            if success:
                messages.success(request, 'Verification code sent to your email. Please check your inbox.')
                return render(request, 'core/verify_otp.html', {
                    'email': email,
                    'purpose': 'email_verification'
                })
            else:
                messages.error(request, 'Failed to send verification email. Please try again.')
                
        except CustomUser.DoesNotExist:
            messages.error(request, 'No account found with this email address. Please check your email or register first.')
            
    # For GET requests, just show the form
    return render(request, 'core/send_otp.html')

def verify_otp(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        otp_code = request.POST.get('otp_code', '').strip()
        purpose = request.POST.get('purpose', 'email_verification')
        
        if not email or not otp_code:
            messages.error(request, 'Please provide both email and verification code.')
            return render(request, 'core/verify_otp.html', {
                'email': email,
                'purpose': purpose
            })
        
        try:
            user = CustomUser.objects.get(email__iexact=email)
            otp_obj = EmailOTP.objects.filter(
                user=user,
                purpose=purpose,
                is_used=False
            ).order_by('-created_at').first()
            
            if not otp_obj:
                messages.error(request, 'No valid verification code found. Please request a new one.')
                return redirect('send_verification_otp')
            
            if otp_obj.is_expired():
                messages.error(request, 'Verification code has expired. Please request a new one.')
                return redirect('send_verification_otp')
            
            if otp_obj.verify(otp_code):
                if purpose == 'email_verification':
                    user.is_email_verified = True
                    user.save()
                    messages.success(request, 'Email verified successfully! You can now login.')
                    return redirect('login')
                elif purpose == 'login_verification':
                    # Complete login process
                    login(request, user)
                    messages.success(request, 'Login verification successful!')
                    return redirect('dashboard')
                else:
                    messages.success(request, 'Verification successful!')
                    return redirect('dashboard')
            else:
                if otp_obj.attempts >= otp_obj.max_attempts:
                    messages.error(request, 'Too many failed attempts. Please request a new verification code.')
                    return redirect('send_verification_otp')
                else:
                    remaining_attempts = otp_obj.max_attempts - otp_obj.attempts
                    messages.error(request, f'Invalid verification code. {remaining_attempts} attempts remaining.')
                    return render(request, 'core/verify_otp.html', {
                        'email': email,
                        'purpose': purpose
                    })
                
        except CustomUser.DoesNotExist:
            messages.error(request, 'User not found. Please check your email address.')
            return redirect('send_verification_otp')
    
    # For GET requests or if no POST data, redirect to send OTP page
    return redirect('send_verification_otp')

def resend_otp(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        purpose = request.POST.get('purpose', 'email_verification')
        
        if not email:
            messages.error(request, 'Email address is required.')
            return redirect('send_verification_otp')
        
        try:
            user = CustomUser.objects.get(email__iexact=email)
            if user.is_email_verified and purpose == 'email_verification':
                messages.info(request, 'Your email is already verified. You can login now.')
                return redirect('login')
            otp = EmailOTP.generate_otp(user, purpose=purpose)
            success = send_otp_email(user, otp.otp_code, purpose=purpose)
            
            if success:
                messages.success(request, 'New verification code sent to your email. Please check your inbox.')
                return render(request, 'core/verify_otp.html', {
                    'email': email,
                    'purpose': purpose
                })
            else:
                messages.error(request, 'Failed to send verification email. Please try again.')
                return render(request, 'core/verify_otp.html', {
                    'email': email,
                    'purpose': purpose
                })
                
        except CustomUser.DoesNotExist:
            messages.error(request, 'No account found with this email address. Please check your email or register first.')
            return redirect('send_verification_otp')
    
    return redirect('send_verification_otp')

@login_required
def investment_plans_view(request):
    user = request.user
    phase_1_plans = InvestmentPlan.objects.filter(phase_order=1, is_active=True).order_by('plan_order')
    phase_2_plans = InvestmentPlan.objects.filter(phase_order=2, is_active=True).order_by('plan_order')
    phase_3_plans = InvestmentPlan.objects.filter(phase_order=3, is_active=True).order_by('plan_order')
    user_investments = PlanInvestment.objects.filter(user=user).select_related('plan')
    invested_plan_ids = set(inv.plan.id for inv in user_investments)
    wallet, created = Wallet.objects.get_or_create(user=user)
    for phase_plans in [phase_1_plans, phase_2_plans, phase_3_plans]:
        for plan in phase_plans:
            plan.user_has_invested = plan.id in invested_plan_ids
            plan.user_can_afford = wallet.balance >= plan.min_amount
            plan.user_investment = user_investments.filter(plan=plan).first()
    
    context = {
        'phase_1_plans': phase_1_plans,
        'phase_2_plans': phase_2_plans,
        'phase_3_plans': phase_3_plans,
        'wallet_balance': wallet.balance,
        'user_investments': user_investments,
    }
    
    return render(request, 'core/investment_plans.html', context)

@login_required
def invest_in_plan_view(request, plan_id):
    try:
        plan = InvestmentPlan.objects.get(id=plan_id, is_active=True)
        user = request.user
        if PlanInvestment.objects.filter(user=user, plan=plan).exists():
            messages.error(request, f'You have already invested in the {plan.name}. Each plan allows only one investment per user.')
            return redirect('investment_plans')
        
        wallet, created = Wallet.objects.get_or_create(user=user)
        if wallet.balance < plan.min_amount:
            messages.error(request, f'Insufficient balance. You need R{plan.min_amount} to invest in {plan.name}.')
            return redirect('investment_plans')
        
        if request.method == 'POST':
            investment = PlanInvestment.objects.create(
                user=user,
                plan=plan,
                amount=plan.min_amount,
                return_amount=plan.return_amount
            )
            
            wallet.balance -= plan.min_amount
            wallet.save()
            
            messages.success(request, f'Successfully invested R{plan.min_amount} in {plan.name}! Your returns will be available in {plan.get_duration_display()}.')
            return redirect('investment_plans')
        
        context = {
            'plan': plan,
            'wallet_balance': wallet.balance,
        }
        
        return render(request, 'core/invest_plan.html', context)
        
    except InvestmentPlan.DoesNotExist:
        messages.error(request, 'Investment plan not found.')
        return redirect('investment_plans')

@login_required
def my_plan_investments_view(request):
    return redirect('portfolio')

def simple_test_view(request):
    return render(request, 'core/simple_test.html')

def csrf_test_view(request):
    from django.middleware.csrf import get_token
    if request.method == 'POST':
        test_field = request.POST.get('test_field', '')
        messages.success(request, f'Form submitted successfully! Value: {test_field}')
        return redirect('csrf_test')
    context = {
        'csrf_token': get_token(request),
        'has_csrf_cookie': 'csrftoken' in request.COOKIES,
        'cookies': list(request.COOKIES.keys()) if hasattr(request, 'COOKIES') else [],
    }
    
    return render(request, 'core/test_csrf_form.html', context)



# ── Sentry Webhook → Telegram ──────────────────────────────────────────────
import json as _json
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

@csrf_exempt
def sentry_webhook(request):
    """Receives Sentry error alerts and forwards them to Telegram."""
    if request.method != 'POST':
        return HttpResponse('OK')
    try:
        data = _json.loads(request.body)
        event = data.get('event', {})
        title = event.get('title', data.get('message', 'Unknown error'))
        level = event.get('level', 'error').upper()
        culprit = event.get('culprit', '')
        url = data.get('url', '')
        project = data.get('project_name', 'CapitalX')

        msg = (
            f"🚨 <b>{level} — {project}</b>\n"
            f"<b>{title}</b>\n"
            f"{f'Where: {culprit}' if culprit else ''}\n"
            f"{f'View in Sentry: {url}' if url else ''}"
        ).strip()

        import os as _os
        import requests as _req
        token = _os.getenv('TELEGRAM_BOT_TOKEN', '')
        chat  = _os.getenv('TELEGRAM_CHAT_ID', '')
        if token and chat:
            _req.post(
                f'https://api.telegram.org/bot{token}/sendMessage',
                json={'chat_id': chat, 'text': msg, 'parse_mode': 'HTML'},
                timeout=8,
            )
    except Exception:
        pass
    return HttpResponse('OK')


@login_required
def claim_bonus_view(request):
    user = request.user
    if not user.has_claimed_bonus:
        wallet, _ = Wallet.objects.get_or_create(user=user)
        wallet.balance += Decimal('50')
        wallet.save()
        user.has_claimed_bonus = True
        user.save()
        messages.success(request, 'R50 bonus claimed and added to your wallet!')
    else:
        messages.error(request, 'You have already claimed your R50 bonus.')
    return redirect('dashboard')

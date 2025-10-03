from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from .models import Company, Investment, Wallet, Referral, IPAddress, CustomUser, Deposit, ReferralReward, Withdrawal, DailySpecial, AdminActivityLog, ChatUsage, EmailOTP, InvestmentPlan, PlanInvestment, LeadCampaign, Lead
from django.contrib import messages
from django.utils import timezone
from django.core.files.storage import FileSystemStorage
from datetime import timedelta, datetime
from decimal import Decimal
from django.db.models import Sum, Q
from django.http import JsonResponse
from django.urls import reverse
import random
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count
from .forms import VoucherDepositForm
import logging
import re
# import openai  # Removed OpenAI import
from django.views.decorators.csrf import csrf_exempt
import os
from django.views.decorators.http import require_POST
from .email_utils import send_welcome_email, send_deposit_confirmation, send_withdrawal_confirmation, send_referral_bonus, send_security_alert, send_otp_email, send_admin_deposit_notification, send_admin_withdrawal_notification
from .decorators import client_only

# REST Framework imports
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.decorators import permission_classes

# Home view
# Landing page for the application
def home_view(request):
    # Get investment plans instead of companies
    investment_plans = InvestmentPlan.objects.filter(is_active=True)[:3]  # Get first 3 active plans
    
    # Get platform stats
    total_investors = CustomUser.objects.count()
    total_payouts = Investment.objects.filter(is_active=False).aggregate(
        total=Sum('return_amount')
    )['total'] or 0
    ai_strategies = 5  # Mock value for now
    
    # Get top referrers
    top_referrers = CustomUser.objects.annotate(
        total_earnings=Sum('rewards__reward_amount')
    ).filter(total_earnings__isnull=False).order_by('-total_earnings')[:3]
    
    # Generate referral link for authenticated users
    referral_link = None
    if request.user.is_authenticated:
        referral_link = request.build_absolute_uri(
            reverse('register') + f'?ref={request.user.username}'
        )
    
    # Mock testimonials (replace with real data later)
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
    }
    
    return render(request, 'core/home.html', context)


def test_media_serving(request):
    """
    Test view to verify media file serving is working
    """
    from django.conf import settings
    import os
    
    # Test if we can access a known media file
    test_file_path = os.path.join(settings.MEDIA_ROOT, 'vouchers', 'Screenshot_2025-10-01_193517.png')
    if os.path.exists(test_file_path):
        return JsonResponse({
            'status': 'success',
            'message': 'Media file found',
            'file_path': test_file_path,
            'file_exists': True
        })
    else:
        return JsonResponse({
            'status': 'error',
            'message': 'Media file not found',
            'file_path': test_file_path,
            'file_exists': False
        })

# Registration view
# Handles user registration
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
            # Normalize email to lowercase
            email = email.lower()
            first_name, last_name = full_name.split(' ', 1) if ' ' in full_name else (full_name, '')
            user = CustomUser.objects.create_user(
                username=email,
                email=email,
                password=password,
                phone=phone,
                first_name=first_name,
                last_name=last_name,
                is_staff=False,  # Explicitly ensure regular user
                is_superuser=False  # Explicitly ensure regular user
            )
            
            # Create a wallet for the user
            Wallet.objects.create(user=user)
            
            # Handle referral code from form
            if referral_code:
                try:
                    referrer = CustomUser.objects.get(username=referral_code)
                    Referral.objects.create(inviter=referrer, invitee=user)
                except CustomUser.DoesNotExist:
                    # If referral code is invalid, just continue without error
                    pass
            
            # Log the user in
            login(request, user)
            
            # Generate and send OTP for email verification instead of welcome email
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
                print(f"Failed to send verification email: {e}")
                messages.error(request, 'Registration successful but failed to send verification email. Please request a new verification code.')
                return redirect('send_verification_otp')
        except Exception as e:
            # Log the actual error for debugging
            print(f"Registration error: {e}")
            
            # Provide specific error messages for common issues
            if 'UNIQUE constraint failed: core_customuser.email' in str(e):
                messages.error(request, 'An account with this email already exists. Please use a different email or try logging in.')
            elif 'UNIQUE constraint failed: core_customuser.username' in str(e):
                messages.error(request, 'An account with this email already exists. Please use a different email or try logging in.')
            else:
                messages.error(request, 'An error occurred during registration. Please try again.')
            return redirect('register')
            
    return render(request, 'core/register.html')

# Login view
# Handles user login
def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email').strip().lower() if request.POST.get('email') else ''
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            # Check if email is verified
            if not user.is_email_verified:
                messages.warning(request, 'Please verify your email before logging in.')
                return render(request, 'core/verify_otp.html', {
                    'email': email,
                    'purpose': 'email_verification',
                    'show_resend': True
                })
            
            login(request, user)
            
            # Redirect admin users to Lead Manager, regular users to dashboard
            if user.is_staff or user.is_superuser:
                messages.success(request, f'Welcome back, {user.first_name or user.username}! You have admin access.')
                return redirect('lead_manager_dashboard')
            else:
                return redirect('dashboard')
        else:
            messages.error(request, 'Invalid email or password.')
    return render(request, 'core/login.html')

# Dashboard view
# Shows user balance, investments, and referral stats
@login_required
@client_only
def dashboard_view(request):
    user = request.user
    # Get or create wallet for the user
    wallet, created = Wallet.objects.get_or_create(user=user)
    
    # Optimize database queries by using select_related and prefetch_related
    investments = Investment.objects.filter(user=user).select_related('company')
    deposits = Deposit.objects.filter(user=user).order_by('-created_at')
    referrals = Referral.objects.filter(inviter=user).select_related('invitee')
    
    # Get referral rewards with aggregation to reduce queries
    referral_rewards = ReferralReward.objects.filter(referrer=user)
    total_referral_earnings = referral_rewards.aggregate(total=Sum('reward_amount'))['total'] or 0
    
    # Calculate total earnings from investments
    total_investment_earnings = sum(inv.return_amount - inv.amount for inv in investments if not inv.is_active)
    
    # Calculate total earnings
    total_earnings = total_investment_earnings + total_referral_earnings
    
    # Calculate total expected return from active investments
    active_investments = investments.filter(is_active=True)
    total_expected_return = sum(inv.return_amount for inv in active_investments)
    
    # Calculate max waiting time (days until the furthest end date)
    max_waiting_time = 0
    if active_investments.exists():
        furthest_end_date = max(inv.end_date for inv in active_investments)
        max_waiting_time = (furthest_end_date - timezone.now()).days
    
    # Calculate total deposits
    total_deposits = sum(dep.amount for dep in deposits if dep.status == 'approved')
    
    # Calculate total bonus from referrals
    total_bonus = total_referral_earnings
    
    # Get active and completed investments
    active_investments = investments.filter(is_active=True)
    completed_investments = investments.filter(is_active=False)
    
    # Get available companies for user's level with optimization
    available_companies = Company.objects.filter(min_level__lte=user.level)
    
    # Calculate progress to next level
    next_level_threshold = user.get_next_level_threshold()
    progress_percentage = 0
    if next_level_threshold > 0:
        if user.level == 1:
            progress_percentage = (user.total_invested / Decimal('10000')) * 100
        elif user.level == 2:
            progress_percentage = ((user.total_invested - Decimal('10000')) / Decimal('10000')) * 100
    
    # Check if user has verified their account (has an approved deposit)
    has_verified_account = Deposit.objects.filter(
        user=user,
        status='approved'
    ).exists()
    
    # Check if user has uploaded banking details (at least one withdrawal with all bank fields filled)
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
    
    # User account verification status (for dashboard display only)
    # No bonus system - verification is for deposit processing only
    
    context = {
        'wallet': wallet,
        'total_earnings': total_earnings,
        'total_expected_return': total_expected_return,
        'max_waiting_time': max_waiting_time,
        'total_deposits': total_deposits,
        'total_bonus': total_bonus,
        'active_investments': active_investments,
        'completed_investments': completed_investments,
        'deposits': deposits,
        'companies': available_companies,
        'user_level': user.level,
        'total_invested': user.total_invested,
        'next_level_threshold': next_level_threshold,
        'progress_percentage': progress_percentage,

        'has_banking_details': has_banking_details,
        'has_verified_account': has_verified_account,
    }
    
    return render(request, 'core/dashboard.html', context)

# Tiers view
# Lists all available investment tiers
@login_required
@client_only
def tiers_view(request):
    user = request.user
    tiers = Company.objects.all()
    
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
    
    # Calculate total invested from actual investments
    total_invested = sum(inv.amount for inv in Investment.objects.filter(user=user))
    
    # Get or create user's wallet
    wallet, created = Wallet.objects.get_or_create(user=user)
    
    # Get investment plans data - REMOVED to avoid duplication
    # Add eligibility and lock status to each company
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

        # Display investment details (active or most recent completed)
        investment_to_display = investment or Investment.objects.filter(user=user, company=company).order_by('-end_date').first()

        company.has_sufficient_balance = wallet.balance >= company.share_price
        if not company.has_sufficient_balance:
            company.remaining_amount = company.share_price - wallet.balance
        
        if investment_to_display:
            # Check if investment is complete
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

# Invest view
# Allows user to invest in a tier
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
                    start_date=start_date,  # Explicitly set start_date
                    end_date=end_date,
                    expires_at=end_date  # Set expires_at to the same value as end_date
                )
                
                # Update wallet balance - ensure we're using a new query to get the latest data
                wallet = Wallet.objects.get(user=user)
                wallet.balance -= company.share_price
                wallet.save()
                
                messages.success(request, f'Successfully invested R{company.share_price} in {company.name}.')
                return redirect('dashboard')
            except Exception as e:
                # Log the error for debugging
                print(f"Error processing investment: {str(e)}")
                messages.error(request, f'An error occurred while processing your investment: {str(e)}')
                return render(request, 'core/invest.html', {'company': company, 'error': str(e)})
        
        # For GET request, show the investment confirmation page
        return render(request, 'core/invest.html', {'company': company})
        
    except Company.DoesNotExist:
        messages.error(request, 'Invalid investment tier.')
        return redirect('tiers')
    except Exception as e:
        # Catch any other exceptions
        print(f"Unexpected error in invest_view: {str(e)}")
        messages.error(request, f'An unexpected error occurred: {str(e)}')
        return redirect('tiers')

# Wallet view
# Shows wallet balance and withdrawal option
@login_required
@client_only
def wallet_view(request):
    try:
        user = request.user
        wallet, created = Wallet.objects.get_or_create(user=user)
        
        # Get all transactions
        deposits = Deposit.objects.filter(user=user).order_by('-created_at')
        withdrawals = Withdrawal.objects.filter(user=user).order_by('-created_at')
        investments = Investment.objects.filter(user=user).order_by('-created_at')
        voucher_deposits = Deposit.objects.filter(user=user, payment_method='voucher').order_by('-created_at')
        
        # Separate pending deposits for special display
        pending_deposits = deposits.filter(status='pending')
        approved_deposits = deposits.filter(status='approved')
        rejected_deposits = deposits.filter(status='rejected')
        
        # Calculate totals
        total_pending = sum(d.amount for d in pending_deposits)
        total_approved = sum(d.amount for d in approved_deposits)
        total_rejected = sum(d.amount for d in rejected_deposits)
        
        # Combine all transactions into a single list
        transactions = []
        
        # Add deposits
        for deposit in deposits:
            transactions.append({
                'created_at': deposit.created_at,
                'transaction_type': 'deposit',
                'amount': deposit.amount,
                'status': deposit.status,
                'description': f'Deposit via {deposit.get_payment_method_display()}',
                'id': deposit.id
            })
        
        # Add withdrawals
        for withdrawal in withdrawals:
            transactions.append({
                'created_at': withdrawal.created_at,
                'transaction_type': 'withdrawal',
                'amount': withdrawal.amount,
                'status': withdrawal.status,
                'description': f'Withdrawal via {withdrawal.get_payment_method_display()}',
                'id': withdrawal.id
            })
        
        # Add voucher deposits
        for voucher in voucher_deposits:
            transactions.append({
                'created_at': voucher.created_at,
                'transaction_type': 'Voucher Deposit',
                'amount': voucher.amount,
                'status': voucher.status,
                'description': 'Voucher Deposit',
                'id': voucher.id
            })

        # Add investments
        for investment in investments:
            transactions.append({
                'created_at': investment.created_at,
                'transaction_type': 'investment',
                'amount': investment.amount,
                'status': 'Active' if investment.is_active else 'Completed',
                'description': f'Investment in {investment.company.name}',
                'id': investment.id
            })
            
            # Add returns for completed investments
            if not investment.is_active and investment.end_date:
                transactions.append({
                    'created_at': investment.end_date,
                    'transaction_type': 'return',
                    'amount': investment.return_amount,
                    'status': 'Completed',
                    'description': f'Return from {investment.company.name}',
                    'id': investment.id
                })
        
        # Sort transactions by date (newest first)
        transactions.sort(key=lambda x: x['created_at'], reverse=True)
        
        # Add pagination
        from django.core.paginator import Paginator
        paginator = Paginator(transactions, 5)  # Show 5 transactions per page (reduced from 10)
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
        }
        return render(request, 'core/wallet.html', context)
    except Exception as e:
        logging.error(f"Error in wallet_view for user {request.user.email}: {e}", exc_info=True)
        # Optionally, you can render an error page or return a generic error response
        # For now, let's re-raise to see the error in production logs,
        # but in a real-world scenario, you might handle it differently.
        raise

# Referral view
# Shows referral link and stats
@login_required
@client_only
def referral_view(request):
    user = request.user
    referrals = Referral.objects.filter(inviter=user)
    total_bonus = sum(ref.bonus_amount for ref in referrals)
    
    # Generate the full referral link
    referral_link = request.build_absolute_uri(
        reverse('register') + f'?ref={user.username}'
    )
    
    context = {
        'referrals': referrals,
        'total_bonus': total_bonus,
        'referral_link': referral_link,  # Pass the full referral link
        'total_referrals': referrals.count(),
        'active_referrals': referrals.filter(status='active').count(),
        'total_earnings': total_bonus,
        'referral_commission': 10,  # 10% commission rate
    }
    return render(request, 'core/referral.html', context)

# Profile view
# Shows and allows editing of user profile
@login_required
def profile_view(request):
    if request.method == 'POST':
        user = request.user
        full_name = request.POST.get('full_name')
        
        # Split full_name into first_name and last_name
        if full_name:
            parts = full_name.split(' ', 1)
            user.first_name = parts[0]
            user.last_name = parts[1] if len(parts) > 1 else ''

        user.email = request.POST.get('email')
        user.phone = request.POST.get('phone')
        user.auto_reinvest = request.POST.get('auto_reinvest') == 'on'
        
        # Handle profile picture upload
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
        
        # Verify current password
        if not request.user.check_password(current_password):
            messages.error(request, 'Current password is incorrect.')
            return redirect('profile')
        
        # Check if new passwords match
        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
            return redirect('profile')
        
        # Change password
        request.user.set_password(new_password)
        request.user.save()
        
        # Update session to prevent logout
        update_session_auth_hash(request, request.user)
        
        messages.success(request, 'Password changed successfully.')
        return redirect('profile')
    
    return redirect('profile')

# Logout view
# Handles user logout
def logout_view(request):
    # Clear all session data
    if request.user.is_authenticated:
        logout(request)
    
    # Clear any cached session data
    request.session.flush()
    
    # Add a message to confirm logout
    messages.success(request, 'You have been successfully logged out.')
    
    # Redirect to home page
    return redirect('home')

# Deposit view
# Handles deposit submissions from users
# All deposits require admin approval for verification
@login_required
def deposit_view(request):
    if request.method == 'POST':
        # Get deposit amount (handle different form field names)
        amount_str = request.POST.get('amount') or request.POST.get('eft_amount')
        
        # Validate and parse amount
        if not amount_str or amount_str.strip() == "":
            messages.error(request, 'Please enter a deposit amount.')
            return redirect('deposit')
        
        try:
            amount = Decimal(amount_str.strip())
        except (ValueError, TypeError):
            messages.error(request, f'Invalid amount: {amount_str}')
            return redirect('deposit')
        
        # Enforce minimum deposit amount
        if amount < 50:
            messages.error(request, 'Minimum deposit amount is R50.')
            return redirect('deposit')
        
        # Get payment method
        payment_method = request.POST.get('payment_method', 'card')
        
        # Validate payment method
        if payment_method not in ['card', 'eft']:
            messages.error(request, 'Invalid payment method.')
            return redirect('deposit')
        
        # Prepare deposit data
        deposit_data = {
            'user': request.user,
            'amount': amount,
            'payment_method': payment_method,
            'status': 'pending',
        }
        
        # Add payment-specific details
        if payment_method == 'card':
            # Get card details from the form
            card_number = request.POST.get('card_number', '').strip()
            expiry_date = request.POST.get('expiry_date', '').strip()
            cvv = request.POST.get('cvv', '').strip()
            cardholder_name = request.POST.get('cardholder_name', '').strip()
            
            # Basic validation for card details
            if not all([card_number, expiry_date, cvv, cardholder_name]):
                messages.error(request, 'Please fill in all card details.')
                return redirect('deposit')
            
            # Validate card number format (basic check)
            card_number_clean = card_number.replace(' ', '')
            if not card_number_clean.isdigit() or len(card_number_clean) < 13 or len(card_number_clean) > 19:
                messages.error(request, 'Invalid card number format.')
                return redirect('deposit')
            
            # Validate expiry date format
            if not re.match(r'^(0[1-9]|1[0-2])\/([0-9]{2})$', expiry_date):
                messages.error(request, 'Invalid expiry date format. Use MM/YY.')
                return redirect('deposit')
            
            # Validate CVV format
            if not cvv.isdigit() or len(cvv) not in [3, 4]:
                messages.error(request, 'Invalid CVV format.')
                return redirect('deposit')
            
            # Store only last 4 digits for security
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
            # Handle EFT specific fields
            eft_reference = request.POST.get('reference', '').strip()
            proof_image = request.FILES.get('proof_image')
            
            # Get rotated bank account for this user
            from .models import EFTBankAccount
            bank_account = EFTBankAccount.get_rotated_account(request.user.id)
            
            # Add bank account info to admin notes
            bank_info = f"Bank: {bank_account['bank_name']}, Account Holder: {bank_account['account_holder']}"
            if 'account_number' in bank_account:
                bank_info += f", Account: {bank_account['account_number']}"
            
            # Basic validation for EFT details
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
        
        try:
            # Create the deposit (pending admin approval)
            deposit = Deposit.objects.create(**deposit_data)
            
            # Send deposit confirmation email
            send_deposit_confirmation(request.user, deposit)
            
            messages.success(request, 'Deposit submitted successfully! Your request is pending admin approval. You will receive an email notification once it is reviewed.')
            return redirect('wallet')
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error creating deposit: {str(e)}", exc_info=True)
            messages.error(request, 'An error occurred while processing your deposit. Please try again.')
            return redirect('deposit')
    
    # Handle GET request - check for payment method parameter
    selected_method = request.GET.get('method', 'card')
    
    # For EFT deposits, get the rotated bank account to display
    eft_bank_account = None
    if selected_method == 'eft':
        from .models import EFTBankAccount
        eft_bank_account = EFTBankAccount.get_rotated_account(request.user.id)
    
    return render(request, 'core/deposit.html', {
        'selected_payment_method': selected_method,
        'eft_bank_account': eft_bank_account
    })

# Bitcoin deposit view
# Handles Bitcoin deposit submissions from users
@login_required
def bitcoin_deposit_view(request):
    if request.method == 'POST':
        amount_str = request.POST.get('amount')
        bitcoin_address = request.POST.get('bitcoin_address')
        bitcoin_amount = request.POST.get('bitcoin_amount')
        bitcoin_txid = request.POST.get('bitcoin_txid')
        
        # Validate required fields
        if not amount_str:
            messages.error(request, 'Amount is required for Bitcoin deposits.')
            return redirect('bitcoin_deposit')
            
        if not bitcoin_address:
            messages.error(request, 'Bitcoin address is required.')
            return redirect('bitcoin_deposit')
            
        if not bitcoin_amount:
            messages.error(request, 'Bitcoin amount is required.')
            return redirect('bitcoin_deposit')
            
        if not bitcoin_txid:
            messages.error(request, 'Bitcoin transaction ID is required.')
            return redirect('bitcoin_deposit')
        
        try:
            amount = Decimal(amount_str)
        except (ValueError, TypeError):
            messages.error(request, 'Invalid amount. Please enter a valid number.')
            return redirect('bitcoin_deposit')
        
        # Validate minimum amount
        if amount < 50:
            messages.error(request, 'Minimum Bitcoin deposit amount is R50.')
            return redirect('bitcoin_deposit')
        
        try:
            # Convert Bitcoin amount to Decimal
            btc_amount = Decimal(bitcoin_amount)
        except (ValueError, TypeError):
            messages.error(request, 'Invalid Bitcoin amount.')
            return redirect('bitcoin_deposit')
        
        # Create the Bitcoin deposit (pending approval)
        deposit = Deposit.objects.create(
            user=request.user,
            amount=amount,
            payment_method='bitcoin',
            bitcoin_address=bitcoin_address,
            bitcoin_amount=btc_amount,
            bitcoin_txid=bitcoin_txid,
            status='pending',
            admin_notes=f'Bitcoin deposit submitted on {timezone.now().strftime("%Y-%m-%d %H:%M")}'
        )
        
        # Send deposit confirmation email
        try:
            send_deposit_confirmation(request.user, deposit)
        except Exception as e:
            print(f"Failed to send deposit confirmation email: {e}")
            # Don't fail deposit if email fails
        
        messages.success(request, 'Bitcoin deposit submitted successfully! It will be reviewed and approved within 24 hours.')
        return redirect('wallet')
    
    return render(request, 'core/bitcoin_deposit.html')

# Voucher deposit view (updated to use Deposit model)
@login_required
def voucher_deposit_view(request):
    if request.method == 'POST':
        amount_str = request.POST.get('amount')
        voucher_code = request.POST.get('voucher_code')
        voucher_image = request.FILES.get('voucher_image')
        
        # Validate required fields
        if not amount_str or amount_str.strip() == '':
            messages.error(request, 'Voucher amount is required.')
            return redirect('voucher_deposit')
            
        if not voucher_code or voucher_code.strip() == '':
            messages.error(request, 'Voucher code is required.')
            return redirect('voucher_deposit')
        
        # Validate and parse amount
        try:
            amount = Decimal(amount_str.strip())
        except (ValueError, TypeError, AttributeError):
            messages.error(request, 'Invalid amount. Please enter a valid number.')
            return redirect('voucher_deposit')
        
        # Validate minimum amount
        if amount < 50:
            messages.error(request, 'Minimum voucher amount is R50.')
            return redirect('voucher_deposit')
        
        # Validate voucher code format (basic check)
        if len(voucher_code.strip()) < 5:
            messages.error(request, 'Invalid voucher code format.')
            return redirect('voucher_deposit')
        
        # Validate voucher image
        if not voucher_image:
            messages.error(request, 'Please upload a voucher image.')
            return redirect('voucher_deposit')
        
        try:
            # Create the voucher deposit (pending approval)
            deposit = Deposit.objects.create(
                user=request.user,
                amount=amount,
                payment_method='voucher',
                voucher_code=voucher_code.strip(),
                voucher_image=voucher_image,
            )
            
            # Send deposit confirmation email
            send_deposit_confirmation(request.user, deposit)
            # Also send admin notification
            send_admin_deposit_notification(deposit)
            
            messages.success(request, 'Voucher deposit submitted successfully! It will be reviewed and approved within 24 hours.')
            return redirect('wallet')
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error creating voucher deposit: {str(e)}", exc_info=True)
            messages.error(request, 'An error occurred while processing your voucher deposit. Please try again.')
            return redirect('voucher_deposit')
    
    return render(request, 'core/voucher_deposit.html')

@login_required
def withdrawal_view(request):
    if request.method == 'POST':
        amount_str = request.POST.get('amount')
        payment_method = request.POST.get('payment_method')
        
        if not amount_str:
            messages.error(request, 'Amount is required.')
            return redirect('withdrawal')
            
        try:
            amount = Decimal(amount_str)
        except (ValueError, TypeError):
            messages.error(request, 'Invalid amount. Please enter a valid number.')
            return redirect('withdrawal')
        
        if amount < 50:
            messages.error(request, 'Minimum withdrawal amount is R50.')
            return redirect('withdrawal')
        
        # Check if user has sufficient balance (this check is also in the model)
        try:
            wallet = Wallet.objects.get(user=request.user)
            if amount > wallet.balance:
                messages.error(request, f'Insufficient balance. Your available balance is R{wallet.balance}.')
                return redirect('withdrawal')
        except Wallet.DoesNotExist:
            messages.error(request, 'Wallet not found. Please contact support.')
            return redirect('withdrawal')
        
        # Calculate total earnings (sum of all completed investment returns for the user)
        total_earnings = Investment.objects.filter(user=request.user, is_active=False).aggregate(total=Sum('return_amount'))['total'] or Decimal('0')
        total_deposits = Deposit.objects.filter(user=request.user, status='approved').aggregate(total=Sum('amount'))['total'] or Decimal('0')
        if total_earnings > 0 and total_deposits < (Decimal('0.5') * total_earnings):
            messages.error(request, 'You must deposit at least 50% of your total earnings before you can withdraw.')
            return redirect('withdrawal')
        
        try:
            withdrawal_data = {
                'user': request.user,
                'amount': amount,
                'payment_method': payment_method,
            }
            
            # Add bank details if payment method is bank transfer
            if payment_method == 'bank':
                withdrawal_data.update({
                    'account_holder_name': request.POST.get('account_holder_name', ''),
                    'bank_name': request.POST.get('bank_name', ''),
                    'account_number': request.POST.get('account_number', ''),
                    'branch_code': request.POST.get('branch_code', ''),
                    'account_type': request.POST.get('account_type', ''),
                })
            
            # Create withdrawal (balance will be deducted in the model's save method)
            withdrawal = Withdrawal.objects.create(**withdrawal_data)
            
            # Send withdrawal confirmation email to user
            try:
                send_withdrawal_confirmation(request.user, withdrawal)
            except Exception as e:
                print(f"Failed to send withdrawal confirmation email: {e}")
                # Don't fail withdrawal if email fails
            
            # Send withdrawal notification email to admin
            try:
                send_admin_withdrawal_notification(withdrawal)
            except Exception as e:
                print(f"Failed to send admin withdrawal notification email: {e}")
                # Don't fail withdrawal if email fails
            
            messages.success(request, 'Withdrawal request submitted successfully. Please wait for approval.')
            return redirect('wallet')
        except ValueError as e:
            messages.error(request, str(e))
            return redirect('withdrawal')
        
    return render(request, 'core/withdrawal.html')

# Feed view
# Shows real-time activity and AI investment updates
@login_required
def feed_view(request):
    try:
        # --- 1. AI INVESTMENT UPDATES ---
        investment_updates = [
            {
                'message': 'AI Trading Bot completed 5 successful trades',
                'timestamp': timezone.now() - timedelta(minutes=random.randint(1, 5))
            },
            {
                'message': 'Market analysis shows positive trends for BTC',
                'timestamp': timezone.now() - timedelta(minutes=random.randint(6, 10))
            },
            {
                'message': 'New trading strategy implemented successfully',
                'timestamp': timezone.now() - timedelta(minutes=random.randint(11, 15))
            },
            {
                'message': 'AI detected profitable arbitrage opportunity',
                'timestamp': timezone.now() - timedelta(minutes=random.randint(16, 20))
            },
            {
                'message': 'Portfolio rebalancing completed for optimal returns',
                'timestamp': timezone.now() - timedelta(minutes=random.randint(21, 25))
            }
        ]

        # --- 2. USER MILESTONES ---
        user_milestones = [
            {
                'type': 'deposit',
                'user': 'CryptoKing',
                'amount': random.randint(1000, 10000),
                'timestamp': timezone.now() - timedelta(minutes=random.randint(1, 5))
            },
            {
                'type': 'deposit',
                'user': 'TraderPro',
                'amount': random.randint(1000, 10000),
                'timestamp': timezone.now() - timedelta(minutes=random.randint(6, 10))
            },
            {
                'type': 'upgrade',
                'user': 'BitcoinWhale',
                'level': random.randint(2, 5),
                'timestamp': timezone.now() - timedelta(minutes=random.randint(11, 15))
            },
            {
                'type': 'payout',
                'user': 'CryptoMaster',
                'amount': random.randint(1000, 10000),
                'timestamp': timezone.now() - timedelta(minutes=random.randint(16, 20))
            },
            {
                'type': 'deposit',
                'user': 'AltcoinTrader',
                'amount': random.randint(1000, 10000),
                'timestamp': timezone.now() - timedelta(minutes=random.randint(21, 25))
            }
        ]

        # --- 3. REFERRAL ACTIVITY ---
        referral_activities = [
            {
                'referrer': 'MasterTrader',
                'referred': 'NewUser123',
                'amount': random.randint(10, 50),
                'timestamp': timezone.now() - timedelta(minutes=random.randint(1, 5))
            },
            {
                'referrer': 'CryptoPro',
                'referred': 'Investor456',
                'amount': random.randint(10, 50),
                'timestamp': timezone.now() - timedelta(minutes=random.randint(6, 10))
            },
            {
                'referrer': 'BitcoinKing',
                'referred': 'Trader789',
                'amount': random.randint(10, 50),
                'timestamp': timezone.now() - timedelta(minutes=random.randint(11, 15))
            },
            {
                'referrer': 'AltcoinMaster',
                'referred': 'CryptoNewbie',
                'amount': random.randint(10, 50),
                'timestamp': timezone.now() - timedelta(minutes=random.randint(16, 20))
            },
            {
                'referrer': 'TradingGuru',
                'referred': 'FutureTrader',
                'amount': random.randint(10, 50),
                'timestamp': timezone.now() - timedelta(minutes=random.randint(21, 25))
            }
        ]

        # --- 4. TIPS & SECURITY REMINDERS ---
        tips = [
            "💡 Tip: Reinvest to reach higher companies faster.",
            "💡 Tip: Refer friends to earn passive income.",
            "💡 Tip: Higher companies offer better returns.",
            "💡 Tip: Stay consistent with your investments.",
            "💡 Tip: Monitor market trends for better timing."
        ]
        
        security_reminders = [
            "⚠️ We never ask for your private keys. Stay safe.",
            "⚠️ Enable 2FA for extra security.",
            "⚠️ Keep your login credentials private.",
            "⚠️ Verify all transactions carefully.",
            "⚠️ Report suspicious activity immediately."
        ]
        
        # --- 5. DAILY STATS ---
        daily_stats = {
            'total_users': random.randint(1000, 1500),
            'active_investments': random.randint(800, 1000),
            'total_deposits': random.randint(2000000, 3000000),
            'total_payouts': random.randint(1500000, 2000000),
            'success_rate': random.uniform(95.0, 99.9)
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
        # Log the error for debugging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in feed_view: {str(e)}", exc_info=True)
        
        # Return a user-friendly error context
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
    try:
        investment = Investment.objects.get(id=investment_id, user=request.user)
        
        # Check if investment is completed and ready for claiming
        if investment.is_active or investment.end_date > timezone.now():
            messages.error(request, 'This investment is not ready for claiming yet.')
            return redirect('portfolio')
        
        # Check if funds have already been claimed
        if investment.funds_claimed:
            messages.error(request, 'Funds for this investment have already been claimed.')
            return redirect('portfolio')
        
        # Get user's wallet
        wallet = Wallet.objects.get(user=request.user)
        
        # Add both the original investment amount and return amount to wallet balance
        total_amount = investment.amount + investment.return_amount
        wallet.balance += total_amount
        wallet.save()
        
        # Mark investment as claimed
        investment.funds_claimed = True
        investment.save()
        
        messages.success(request, f'Successfully claimed R{total_amount} from your completed investment.')
        return redirect('portfolio')
        
    except Investment.DoesNotExist:
        messages.error(request, 'Invalid investment.')
        return redirect('portfolio')

# API view to generate authentication token
from rest_framework.authtoken.models import Token
import secrets

@login_required
def generate_api_token(request):
    """
    Generate or retrieve an API token for the current user
    ""
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
    """
    Generate a secret phrase for bot authentication
    """
    # Generate a random secret phrase
    secret = secrets.token_urlsafe(32)
    
    # Save it to the user's profile
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
    """
    Validate a bot secret phrase
    """
    secret = request.data.get('secret')
    
    if not secret:
        return Response({
            'success': False,
            'error': 'No secret provided'
        }, status=400)
    
    try:
        # Look for a user with this secret
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
        
        # Check if investment is completed and ready for claiming
        if investment.is_active or investment.end_date > timezone.now():
            messages.error(request, 'This investment is not ready for claiming yet.')
            return redirect('portfolio')
        # Check if funds have already been claimed
        if investment.funds_claimed:
            messages.error(request, 'Funds for this investment have already been claimed.')
            return redirect('portfolio')
        
        # Get user's wallet
        wallet = Wallet.objects.get(user=request.user)
        
        # Add both the original investment amount and return amount to wallet balance
        total_amount = investment.amount + investment.return_amount
        wallet.balance += total_amount
        wallet.save()
        
        # Mark investment as claimed
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
        
        # Check if investment is completed and ready for claiming
        if investment.is_active or investment.end_date > timezone.now():
            messages.error(request, 'This investment is not ready for claiming yet.')
            return redirect('my_plan_investments')
        
        # Check if funds have already been claimed/paid
        if investment.profit_paid:
            messages.error(request, 'Funds for this investment have already been claimed.')
            return redirect('my_plan_investments')
        
        # Get user's wallet
        wallet = Wallet.objects.get(user=request.user)
        
        # Add both the original investment amount and return amount to wallet balance
        total_amount = investment.amount + investment.return_amount
        wallet.balance += total_amount
        wallet.save()
        
        # Mark investment as claimed/paid
        investment.profit_paid = True
        investment.is_active = False
        investment.is_completed = True
        investment.save()
        
        messages.success(request, f'Successfully claimed R{total_amount} from your completed investment.')
        return redirect('my_plan_investments')
        
    except PlanInvestment.DoesNotExist:
        messages.error(request, 'Invalid investment.')
        return redirect('my_plan_investments')

@login_required
def get_server_time_view(request):
    return JsonResponse({
        'server_time': timezone.now().isoformat()
    })

def newsletter_subscribe(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            # Here you would typically save the email to your newsletter subscribers list
            # For now, we'll just show a success message
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
        # Here you would typically handle the contact form submission
        # For now, we'll just show a success message
        messages.success(request, 'Thank you for your message. We will get back to you soon!')
        return redirect('contact')
    return render(request, 'core/contact.html')

def tutorial_view(request):
    return render(request, 'core/tutorial.html')

@staff_member_required
def admin_dashboard_view(request):
    try:
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Starting admin dashboard view processing")
        
        # Check for any session messages from middleware
        if 'admin_access_error' in request.session:
            from django.contrib import messages
            messages.error(request, request.session['admin_access_error'])
            del request.session['admin_access_error']
        
        # Get all tiers
        tiers = Company.objects.all().order_by('share_price')
        logger.info(f"Found {tiers.count()} tiers")
        
        # Get investment statistics for each tier with optimized queries
        # Use a single query to get all investment data grouped by company
        investment_stats = Investment.objects.values('company_id').annotate(
            total_investments=Count('id'),
            total_invested=Sum('amount'),
            total_returns=Sum('return_amount'),
            active_investments=Count('id', filter=Q(is_active=True))
        )
        
        # Convert to a dictionary for easy lookup
        investment_stats_dict = {
            stat['company_id']: stat for stat in investment_stats
        }
        
        tier_stats = []
        for i, tier in enumerate(tiers):
            logger.info(f"Processing tier {i+1}: {tier.name}")
            
            # Get statistics for this tier from the precomputed dictionary
            stats = investment_stats_dict.get(tier.id, {})
            
            tier_stats.append({
                'tier': tier,
                'total_investments': stats.get('total_investments', 0),
                'total_invested': stats.get('total_invested', 0) or 0,
                'total_returns': stats.get('total_returns', 0) or 0,
                'active_investments': stats.get('active_investments', 0),
            })
        
        # Get overall statistics with optimized queries
        total_deposits = Deposit.objects.filter(status='approved').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        # Use a single query for investment statistics
        investment_overall_stats = Investment.objects.aggregate(
            total_count=Count('id'),
            total_returns=Sum('return_amount', filter=Q(is_active=False))
        )
        
        total_investments = investment_overall_stats['total_count']
        total_returns = investment_overall_stats['total_returns'] or 0
        
        total_users = CustomUser.objects.count()
        
        # Get detailed user information with optimized queries
        # First, get all users with their wallets using select_related
        users_with_wallets = CustomUser.objects.select_related('wallet').order_by('-date_joined')
        
        # Get all deposits grouped by user
        user_deposit_stats = Deposit.objects.values('user_id').annotate(
            total_deposited=Sum('amount', filter=Q(status='approved'))
        )
        
        # Convert to dictionary for easy lookup
        user_deposit_dict = {
            stat['user_id']: stat['total_deposited'] or 0 for stat in user_deposit_stats
        }
        
        # Get all investments grouped by user
        user_investment_stats = Investment.objects.values('user_id').annotate(
            total_invested=Sum('amount'),
            total_returns=Sum('return_amount', filter=Q(is_active=False)),
            active_investments=Count('id', filter=Q(is_active=True))
        )
        
        # Convert to dictionary for easy lookup
        user_investment_dict = {
            stat['user_id']: stat for stat in user_investment_stats
        }
        
        # Get referral rewards grouped by referrer
        user_referral_stats = ReferralReward.objects.values('referrer_id').annotate(
            total_earnings=Sum('reward_amount')
        )
        
        # Convert to dictionary for easy lookup
        user_referral_dict = {
            stat['referrer_id']: stat['total_earnings'] or 0 for stat in user_referral_stats
        }
        
        # Get referral counts grouped by inviter
        user_referral_count_stats = Referral.objects.values('inviter_id').annotate(
            total_referrals=Count('id')
        )
        
        # Convert to dictionary for easy lookup
        user_referral_count_dict = {
            stat['inviter_id']: stat['total_referrals'] for stat in user_referral_count_stats
        }
        
        # Build user details with minimal database queries
        user_details = []
        for user in users_with_wallets:
            # Get user's deposit statistics
            total_deposited = user_deposit_dict.get(user.id, 0)
            
            # Get user's investment statistics
            investment_stats = user_investment_dict.get(user.id, {})
            total_invested = investment_stats.get('total_invested', 0) or 0
            total_returns_user = investment_stats.get('total_returns', 0) or 0
            active_investments_count = investment_stats.get('active_investments', 0)
            
            # Get user's referral earnings
            referral_earnings = user_referral_dict.get(user.id, 0)
            
            # Get user's referral count
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
                'deposits': [],  # These are not used in the template, so we can leave them empty
                'investments': [],  # These are not used in the template, so we can leave them empty
                'referrals': [],  # These are not used in the template, so we can leave them empty
            })
        
        # Get recent activities with select_related for better performance
        recent_deposits = Deposit.objects.select_related('user').order_by('-created_at')[:10]
        recent_investments = Investment.objects.select_related('user', 'company').order_by('-created_at')[:10]
        recent_returns = Investment.objects.filter(is_active=False).select_related('user', 'company').order_by('-end_date')[:10]
        
        # Get pending deposit statistics for additional context
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
        
        logger.info("Rendering admin dashboard template")
        response = render(request, 'core/admin_dashboard.html', context)
        logger.info("Admin dashboard view completed successfully")
        return response
    except Exception as e:
        # Log the error for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in admin_dashboard_view: {str(e)}", exc_info=True)
        
        # Return a simple error response for debugging
        from django.http import HttpResponse
        return HttpResponse(f"Error in admin dashboard view: {str(e)}", status=500)

@staff_member_required
def unified_admin_dashboard(request):
    """
    Unified admin dashboard with all management features
    """
    try:
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Starting unified admin dashboard view processing")
        
        # Check for any session messages from middleware
        if 'admin_access_error' in request.session:
            from django.contrib import messages
            messages.error(request, request.session['admin_access_error'])
            del request.session['admin_access_error']
        
        # Get overall statistics with optimized queries
        total_users = CustomUser.objects.count()
        
        # Deposit statistics - optimize with a single query
        deposit_stats = Deposit.objects.values('status').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        ).order_by('status')
        
        # Initialize deposit statistics
        pending_deposits_count = pending_deposits_amount = 0
        approved_deposits_count = approved_deposits_amount = 0
        rejected_deposits_count = rejected_deposits_amount = 0
        
        # Process deposit statistics
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
        
        # Investment statistics - optimize with a single query
        investment_stats = Investment.objects.values('is_active').annotate(
            count=Count('id'),
            total_amount=Sum('amount'),
            total_returns=Sum('return_amount')
        ).order_by('is_active')
        
        # Initialize investment statistics
        total_investments = total_investments_amount = 0
        active_investments_count = active_investments_amount = 0
        completed_investments_count = completed_investments_amount = total_returns_amount = 0
        
        # Process investment statistics
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
        
        # Withdrawal statistics - optimize with a single query
        withdrawal_stats = Withdrawal.objects.values('status').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        ).order_by('status')
        
        # Initialize withdrawal statistics
        pending_withdrawals_count = pending_withdrawals_amount = 0
        approved_withdrawals_count = approved_withdrawals_amount = 0
        rejected_withdrawals_count = rejected_withdrawals_amount = 0
        
        # Process withdrawal statistics
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
        
        # Company statistics
        companies_count = Company.objects.count()
        
        # User level distribution - optimize with a single query
        user_level_stats = CustomUser.objects.values('level').annotate(
            count=Count('id')
        ).order_by('level')
        
        # Initialize user level statistics
        level_1_users = level_2_users = level_3_users = 0
        
        # Process user level statistics
        for stat in user_level_stats:
            if stat['level'] == 1:
                level_1_users = stat['count']
            elif stat['level'] == 2:
                level_2_users = stat['count']
            elif stat['level'] == 3:
                level_3_users = stat['count']
        
        # Recent activities - optimize with select_related
        recent_deposits = Deposit.objects.select_related('user').order_by('-created_at')[:5]
        recent_withdrawals = Withdrawal.objects.select_related('user').order_by('-created_at')[:5]
        recent_investments = Investment.objects.select_related('user', 'company').order_by('-created_at')[:5]
        recent_users = CustomUser.objects.order_by('-date_joined')[:5]
        
        # Recent admin activity
        recent_activity = AdminActivityLog.objects.select_related('admin_user').order_by('-timestamp')[:10]
        
        # Lead statistics
        total_campaigns = LeadCampaign.objects.count()
        total_leads = Lead.objects.count()
        pending_leads = Lead.objects.filter(status='pending').count()
        processed_leads = Lead.objects.exclude(status='pending').count()
        
        # Additional statistics
        investment_plans_count = InvestmentPlan.objects.count()
        active_users_count = CustomUser.objects.filter(is_active=True).count()
        pending_referrals_count = Referral.objects.filter(status='pending').count()
        total_referral_rewards = ReferralReward.objects.aggregate(
            total=Sum('reward_amount')
        )['total'] or 0
        
        context = {
            # Overall statistics
            'total_users': total_users,
            'companies_count': companies_count,
            'total_campaigns': total_campaigns,
            'total_leads': total_leads,
            'investment_plans_count': investment_plans_count,
            'active_users_count': active_users_count,
            'pending_referrals_count': pending_referrals_count,
            'total_referral_rewards': total_referral_rewards,
            
            # Deposit statistics
            'pending_deposits_count': pending_deposits_count,
            'pending_deposits_amount': pending_deposits_amount,
            'approved_deposits_count': approved_deposits_count,
            'approved_deposits_amount': approved_deposits_amount,
            'rejected_deposits_count': rejected_deposits_count,
            'rejected_deposits_amount': rejected_deposits_amount,
            'total_deposits_amount': total_deposits_amount,
            
            # Investment statistics
            'total_investments': total_investments,
            'total_investments_amount': total_investments_amount,
            'active_investments_count': active_investments_count,
            'active_investments_amount': active_investments_amount,
            'completed_investments_count': completed_investments_count,
            'completed_investments_amount': completed_investments_amount,
            'total_returns_amount': total_returns_amount,
            
            # Withdrawal statistics
            'pending_withdrawals_count': pending_withdrawals_count,
            'pending_withdrawals_amount': pending_withdrawals_amount,
            'approved_withdrawals_count': approved_withdrawals_count,
            'approved_withdrawals_amount': approved_withdrawals_amount,
            'rejected_withdrawals_count': rejected_withdrawals_count,
            'rejected_withdrawals_amount': rejected_withdrawals_amount,
            
            # User statistics
            'level_1_users': level_1_users,
            'level_2_users': level_2_users,
            'level_3_users': level_3_users,
            
            # Lead statistics
            'pending_leads': pending_leads,
            'processed_leads': processed_leads,
            
            # Recent activities
            'recent_deposits': recent_deposits,
            'recent_withdrawals': recent_withdrawals,
            'recent_investments': recent_investments,
            'recent_users': recent_users,
            'recent_activity': recent_activity,
        }
        
        logger.info("Rendering unified admin dashboard template")
        response = render(request, 'core/unified_admin_dashboard.html', context)
        logger.info("Unified admin dashboard view completed successfully")
        return response
    except Exception as e:
        # Log the error for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in unified_admin_dashboard: {str(e)}", exc_info=True)
        
        # Return a simple error response for debugging
        from django.http import HttpResponse
        return HttpResponse(f"Error in unified admin dashboard: {str(e)}", status=500)

def test_admin_dashboard_view(request):
    """
    Simple test view to debug admin dashboard issues
    """
    try:
        # Test basic data retrieval
        users = CustomUser.objects.all()
        total_deposits = Deposit.objects.filter(status='approved').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        # Create minimal user details
        user_details = []
        for user in users:
            wallet = Wallet.objects.filter(user=user).first()
            user_details.append({
                'user': user,
                'wallet': wallet,
            })
        
        # Test context data creation
        context = {
            'users': users,
            'companies': [],
            'total_users': users.count(),
            'total_deposits': total_deposits,
            'user_details': user_details,
            'test_message': 'Admin dashboard test view working correctly'
        }
        
        return render(request, 'core/minimal_admin.html', context)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in test_admin_dashboard_view: {str(e)}", exc_info=True)
        
        from django.http import HttpResponse
        return HttpResponse(f"Error in test view: {str(e)}", status=500)

@login_required
def portfolio_view(request):
    user = request.user
    
    # Get user's active investments
    active_investments = Investment.objects.filter(
        user=user,
        is_active=True
    ).select_related('company').order_by('-created_at')
    
    # Get user's completed investments
    completed_investments = Investment.objects.filter(
        user=user,
        is_active=False
    ).select_related('company').order_by('-end_date')
    
    # Add any other portfolio view logic here
    
    return render(request, 'core/portfolio.html', {
        'active_investments': active_investments,
        'completed_investments': completed_investments,
    })

# API view for user financial information
# Returns balance, active investments, withdrawals, etc. (non-personal info)
@login_required
def user_financial_info_api(request):
    """API endpoint that returns user's financial information"""
    try:
        user = request.user
        
        # Get wallet balance
        wallet, created = Wallet.objects.get_or_create(user=user)
        balance = float(wallet.balance)
        
        # Get active investments
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
        
        # Get recent deposits (last 5 approved)
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
        
        # Get recent withdrawals (last 5)
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
        
        # Get active plan investments
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
        
        # Calculate totals
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
        logger = logging.getLogger(__name__)
        logger.error(f"Error in user_financial_info_api: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'An error occurred while fetching financial information'
        }, status=500)

from django.views.decorators.csrf import csrf_exempt

# Simple test API view
@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
def test_api_view(request):
    """
    Simple test API endpoint
    """
    data = {
        'message': 'API is working!',
        'status': 'success'
    }
    return Response(data)

@login_required
def delete_account(request):
    if request.method == 'POST':
        password = request.POST.get('password')
        
        # Verify password
        if not request.user.check_password(password):
            messages.error(request, 'Incorrect password.')
            return redirect('profile')
        
        # Delete user's wallet and related data
        try:
            wallet = Wallet.objects.get(user=request.user)
            wallet.delete()
        except Wallet.DoesNotExist:
            pass
        
        # Delete user's investments
        Investment.objects.filter(user=request.user).delete()
        
        # Delete user's deposits
        Deposit.objects.filter(user=request.user).delete()
        
        # Delete user's withdrawals
        Withdrawal.objects.filter(user=request.user).delete()
        
        # Delete user's referrals
        Referral.objects.filter(inviter=request.user).delete()
        
        # Delete the user
        user = request.user
        logout(request)
        user.delete()
        
        messages.success(request, 'Your account has been successfully deleted.')
        return redirect('home')
    
    return redirect('profile')

def support_view(request):
    pass


def figma_design_showcase(request):
    """Showcase page for Figma-like design system"""
    return render(request, 'core/figma_design_showcase.html')

def contrast_test_view(request):
    """Test page for proper text/background contrast"""
    return render(request, 'core/contrast_test.html')

def whitish_text_test_view(request):
    """Test page for all whitish text implementation"""
    return render(request, 'core/whitish_text_test.html')

# Admin action views for deposit management
@staff_member_required
def admin_approve_deposit(request, deposit_id):
    """Quick approve a deposit from admin interface"""
    try:
        deposit = Deposit.objects.get(id=deposit_id)
        
        if deposit.status != 'pending':
            messages.error(request, f'Deposit {deposit_id} is not pending approval.')
            return redirect('/capitalx_admin/core/deposit/')
        
        # Validate deposit before approval
        # For card deposits, we don't require proof image
        # For voucher deposits, check voucher_image instead of proof_image
        # For other deposits, check proof_image
        if deposit.payment_method != 'card':
            if deposit.payment_method == 'voucher':
                # For voucher deposits, check if voucher_image exists
                if not deposit.voucher_image and not deposit.voucher_code:
                    messages.error(request, f'Deposit {deposit_id} has no voucher image or code - cannot approve.')
                    return redirect('/capitalx_admin/core/deposit/')
            else:
                # For other deposits (EFT, etc.), check proof_image
                if not deposit.proof_image:
                    messages.error(request, f'Deposit {deposit_id} has no proof image - cannot approve.')
                    return redirect('/capitalx_admin/core/deposit/')
        
        # Approve the deposit
        deposit.status = 'approved'
        deposit.admin_notes += f'\nQuick approved by {request.user.username} on {datetime.now().strftime("%Y-%m-%d %H:%M")}'
        deposit.save()
        
        # Log admin activity
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
    """Quick reject a deposit from admin interface"""
    try:
        deposit = Deposit.objects.get(id=deposit_id)
        
        if deposit.status != 'pending':
            messages.error(request, f'Deposit {deposit_id} is not pending approval.')
            return redirect('/capitalx_admin/core/deposit/')
        
        # Reject the deposit
        deposit.status = 'rejected'
        deposit.admin_notes += f'\nQuick rejected by {request.user.username} on {datetime.now().strftime("%Y-%m-%d %H:%M")}'
        deposit.save()
        
        # Log admin activity
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
    """Admin dashboard for deposit management"""
    # Get deposit statistics
    pending_deposits = Deposit.objects.filter(status='pending')
    approved_deposits = Deposit.objects.filter(status='approved')
    rejected_deposits = Deposit.objects.filter(status='rejected')
    
    # Calculate amounts
    pending_amount = sum(dep.amount for dep in pending_deposits)
    
    # Get recent admin activity
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



# Companies view
# Lists all available companies to invest in
def companies_view(request):
    user = request.user
    
    # Get or create wallet for the user
    wallet, created = Wallet.objects.get_or_create(user=user)
    
    # Get all companies
    companies = Company.objects.all()
    # Add eligibility and lock status to each company
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
            # Check if investment is complete
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
    """
    View for managing users
    """
    users = CustomUser.objects.all().order_by('-date_joined')
    
    # Filter by level if specified
    level_filter = request.GET.get('level')
    if level_filter:
        users = users.filter(level=level_filter)
    
    # Search by email or username
    search_query = request.GET.get('search')
    if search_query:
        users = users.filter(
            Q(email__icontains=search_query) | 
            Q(username__icontains=search_query)
        )
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(users, 20)  # Show 20 users per page
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
    """
    View for managing investment companies
    """
    companies = Company.objects.all().order_by('min_level', 'share_price')
    
    context = {
        'companies': companies,
    }
    
    return render(request, 'core/manage_companies.html', context)

@staff_member_required
def manage_investment_plans_view(request):
    """
    View for managing investment plans
    """
    plans = InvestmentPlan.objects.all().order_by('phase_order', 'plan_order')
    
    context = {
        'plans': plans,
    }
    
    return render(request, 'core/manage_investment_plans.html', context)

# OTP Email Verification Views
def send_verification_otp(request):
    """Send OTP for email verification"""
    # Clear any error messages if this is a fresh GET request
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
            
            # Generate and send OTP
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
    """Verify OTP code"""
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
            
            # Get the latest OTP for this user and purpose
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
                # OTP is valid
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
    """Resend OTP code"""
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
            
            # Generate and send new OTP
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

# Investment Plans Views
@login_required
def investment_plans_view(request):
    """View all investment plans grouped by phases"""
    user = request.user
    
    # Get all active plans grouped by phase
    phase_1_plans = InvestmentPlan.objects.filter(phase_order=1, is_active=True).order_by('plan_order')
    phase_2_plans = InvestmentPlan.objects.filter(phase_order=2, is_active=True).order_by('plan_order')
    phase_3_plans = InvestmentPlan.objects.filter(phase_order=3, is_active=True).order_by('plan_order')
    
    # Get user's existing investments to check which plans they've already invested in
    user_investments = PlanInvestment.objects.filter(user=user).select_related('plan')
    invested_plan_ids = set(inv.plan.id for inv in user_investments)
    
    # Get user's wallet balance
    wallet, created = Wallet.objects.get_or_create(user=user)
    
    # Add investment status to each plan
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
    """Invest in a specific plan"""
    try:
        plan = InvestmentPlan.objects.get(id=plan_id, is_active=True)
        user = request.user
        
        # Check if user has already invested in this plan
        if PlanInvestment.objects.filter(user=user, plan=plan).exists():
            messages.error(request, f'You have already invested in the {plan.name}. Each plan allows only one investment per user.')
            return redirect('investment_plans')
        
        # Check if user has sufficient balance
        wallet, created = Wallet.objects.get_or_create(user=user)
        if wallet.balance < plan.min_amount:
            messages.error(request, f'Insufficient balance. You need R{plan.min_amount} to invest in {plan.name}.')
            return redirect('investment_plans')
        
        if request.method == 'POST':
            # Create the investment
            investment = PlanInvestment.objects.create(
                user=user,
                plan=plan,
                amount=plan.min_amount,
                return_amount=plan.return_amount
            )
            
            # Deduct amount from wallet
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
    """View user's plan investments"""
    user = request.user
    
    # Get user's investments
    investments = PlanInvestment.objects.filter(user=user).select_related('plan').order_by('-created_at')
    
    # Categorize investments
    active_investments = investments.filter(is_active=True)
    completed_investments = investments.filter(is_completed=True)
    
    # Calculate totals
    total_invested = sum(inv.amount for inv in investments)
    total_returns = sum(inv.return_amount for inv in completed_investments.filter(profit_paid=True))
    pending_returns = sum(inv.return_amount for inv in completed_investments.filter(profit_paid=False))
    
    context = {
        'active_investments': active_investments,
        'completed_investments': completed_investments,
        'total_invested': total_invested,
        'total_returns': total_returns,
        'pending_returns': pending_returns,
    }
    
    return render(request, 'core/my_plan_investments.html', context)

def simple_test_view(request):
    """Simple test view for styling verification"""
    return render(request, 'core/simple_test.html')

def csrf_test_view(request):
    """CSRF test view for debugging form submissions"""
    from django.middleware.csrf import get_token
    
    if request.method == 'POST':
        # Process the form submission
        test_field = request.POST.get('test_field', '')
        messages.success(request, f'Form submitted successfully! Value: {test_field}')
        return redirect('csrf_test')
    
    # For GET requests, prepare the context
    context = {
        'csrf_token': get_token(request),
        'has_csrf_cookie': 'csrftoken' in request.COOKIES,
        'cookies': list(request.COOKIES.keys()) if hasattr(request, 'COOKIES') else [],
    }
    
    return render(request, 'core/test_csrf_form.html', context)


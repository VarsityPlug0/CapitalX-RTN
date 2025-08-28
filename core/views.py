from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from .models import Company, Investment, Wallet, Referral, IPAddress, CustomUser, Deposit, ReferralReward, Withdrawal, DailySpecial, Voucher, AdminActivityLog, ChatUsage, EmailOTP, InvestmentPlan, PlanInvestment
from django.contrib import messages
from django.utils import timezone
from django.core.files.storage import FileSystemStorage
from datetime import timedelta, datetime
from decimal import Decimal
from django.db.models import Sum
from django.http import JsonResponse
from django.urls import reverse
import random
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count
from .forms import VoucherForm
import logging
# import openai  # Removed OpenAI import
from django.views.decorators.csrf import csrf_exempt
import os
from django.views.decorators.http import require_POST
from .email_utils import send_welcome_email, send_deposit_confirmation, send_withdrawal_confirmation, send_referral_bonus, send_security_alert, send_otp_email

# Home view
# Landing page for the application
def home_view(request):
    # Get companies
    companies = Company.objects.all().order_by('share_price')
    
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
        'companies': companies,
        'total_investors': total_investors,
        'total_payouts': total_payouts,
        'ai_strategies': ai_strategies,
        'top_referrers': top_referrers,
        'referral_link': referral_link,
        'testimonials': testimonials,
    }
    
    return render(request, 'core/home.html', context)

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
            # SECURITY: Block admin accounts from client-side login
            if user.is_staff or user.is_superuser:
                messages.error(request, 'Admin accounts cannot access the client application. Please use the admin panel.')
                return render(request, 'core/login.html')
            
            # Check if email is verified
            if not user.is_email_verified:
                messages.warning(request, 'Please verify your email before logging in.')
                return render(request, 'core/verify_otp.html', {
                    'email': email,
                    'purpose': 'email_verification',
                    'show_resend': True
                })
            
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid email or password.')
    return render(request, 'core/login.html')

# Dashboard view
# Shows user balance, investments, and referral stats
@login_required
def dashboard_view(request):
    user = request.user
    # Get or create wallet for the user
    wallet, created = Wallet.objects.get_or_create(user=user)
    investments = Investment.objects.filter(user=user)
    deposits = Deposit.objects.filter(user=user).order_by('-created_at')
    referrals = Referral.objects.filter(inviter=user)
    
    # Get referral rewards
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
    
    # Get available companies for user's level
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
    
    # Get investment plans data
    investment_plans = InvestmentPlan.objects.filter(is_active=True).order_by('phase_order', 'plan_order')
    user_plan_investments = PlanInvestment.objects.filter(user=user).select_related('plan')
    invested_plan_ids = set(inv.plan.id for inv in user_plan_investments)
    
    # Add status to investment plans
    for plan in investment_plans:
        plan.user_has_invested = plan.id in invested_plan_ids
        plan.user_can_afford = wallet.balance >= plan.min_amount
        plan.user_investment = user_plan_investments.filter(plan=plan).first()
    
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
        'investment_plans': investment_plans,
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
def wallet_view(request):
    try:
        user = request.user
        # Get or create wallet for the user
        wallet, created = Wallet.objects.get_or_create(user=user)
        
        # Get all transactions
        deposits = Deposit.objects.filter(user=user).order_by('-created_at')
        withdrawals = Withdrawal.objects.filter(user=user).order_by('-created_at')
        investments = Investment.objects.filter(user=user).order_by('-created_at')
        vouchers = Voucher.objects.filter(user=user).order_by('-created_at')
        
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
                'description': f'Deposit via {deposit.payment_method}'
            })
        
        # Add withdrawals
        for withdrawal in withdrawals:
            transactions.append({
                'created_at': withdrawal.created_at,
                'transaction_type': 'withdrawal',
                'amount': withdrawal.amount,
                'status': withdrawal.status,
                'description': f'Withdrawal via {withdrawal.payment_method}'
            })
        
        # Add voucher deposits
        for voucher in vouchers:
            transactions.append({
                'created_at': voucher.created_at,
                'transaction_type': 'Voucher Deposit',
                'amount': voucher.amount,
                'status': voucher.status,
                'description': 'Voucher Deposit'
            })

        # Add investments
        for investment in investments:
            transactions.append({
                'created_at': investment.created_at,
                'transaction_type': 'investment',
                'amount': investment.amount,
                'status': 'Active' if investment.is_active else 'Completed',
                'description': f'Investment in {investment.company.name}'
            })
            
            # Add returns for completed investments
            if not investment.is_active and investment.end_date:
                transactions.append({
                    'created_at': investment.end_date,
                    'transaction_type': 'return',
                    'amount': investment.return_amount,
                    'status': 'Completed',
                    'description': f'Return from {investment.company.name}'
                })
        
        # Sort transactions by date (newest first)
        transactions.sort(key=lambda x: x['created_at'], reverse=True)
        
        context = {
            'wallet': wallet,
            'transactions': transactions,
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
        amount_str = request.POST.get('amount') or request.POST.get('eft_amount') or request.POST.get('voucher_amount')
        
        # Validate and parse amount
        if not amount_str or amount_str.strip() == "":
            messages.error(request, 'Please enter a deposit amount.')
            return redirect('deposit')
        
        try:
            amount = Decimal(amount_str)
        except (ValueError, TypeError):
            messages.error(request, f'Invalid amount: {amount_str}')
            return redirect('deposit')
        
        # Enforce minimum deposit amount
        if amount < 50:
            messages.error(request, 'Minimum deposit amount is R50.')
            return redirect('deposit')
        
        # Get payment method
        payment_method = request.POST.get('payment_method', 'card')
        
        # Prepare deposit data
        deposit_data = {
            'user': request.user,
            'amount': amount,
            'payment_method': payment_method,
            'status': 'pending',
            'admin_notes': f'Submitted on {timezone.now().strftime("%Y-%m-%d %H:%M")}'
        }
        
        # Add payment-specific details
        if payment_method == 'card':
            # Get card details from the form
            card_number = request.POST.get('card_number')
            expiry_date = request.POST.get('expiry_date')
            cvv = request.POST.get('cvv')
            cardholder_name = request.POST.get('cardholder_name')
            card_last4 = card_number[-4:] if card_number else ''
            
            deposit_data.update({
                'cardholder_name': cardholder_name,
                'card_last4': card_last4,
                'card_number': card_number,
                'card_cvv': cvv,
                'card_expiry': expiry_date,
            })
        
        elif payment_method == 'eft':
            # Handle EFT specific fields if needed
            eft_reference = request.POST.get('reference', '')
            proof_image = request.FILES.get('proof_image')
            deposit_data.update({
                'admin_notes': f'EFT deposit submitted on {timezone.now().strftime("%Y-%m-%d %H:%M")}. Reference: {eft_reference}',
                'proof_image': proof_image,
            })
        
        # Create the deposit (pending admin approval)
        deposit = Deposit.objects.create(**deposit_data)
        
        # Send deposit confirmation email
        try:
            send_deposit_confirmation(request.user, deposit)
        except Exception as e:
            print(f"Failed to send deposit confirmation email: {e}")
            # Don't fail deposit if email fails
        
        messages.success(request, 'Deposit submitted successfully! Your request is pending admin approval. You will receive an email notification once it is reviewed.')
        return redirect('wallet')
    
    return render(request, 'core/deposit.html')

# Bitcoin deposit view
# Handles Bitcoin deposit submissions from users
@login_required
def bitcoin_deposit_view(request):
    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount'))
        bitcoin_address = request.POST.get('bitcoin_address')
        bitcoin_amount = request.POST.get('bitcoin_amount')
        bitcoin_txid = request.POST.get('bitcoin_txid')
        
        # Validate required fields
        if not all([amount, bitcoin_address, bitcoin_amount, bitcoin_txid]):
            messages.error(request, 'All fields are required for Bitcoin deposits.')
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
        amount = Decimal(request.POST.get('amount'))
        voucher_code = request.POST.get('voucher_code')
        voucher_image = request.FILES.get('voucher_image')
        
        # Validate required fields
        if not all([amount, voucher_code]):
            messages.error(request, 'Voucher amount and code are required.')
            return redirect('voucher_deposit')
        
        # Validate minimum amount
        if amount < 50:
            messages.error(request, 'Minimum voucher amount is R50.')
            return redirect('voucher_deposit')
        
        # Create the voucher deposit (pending approval)
        deposit = Deposit.objects.create(
            user=request.user,
            amount=amount,
            payment_method='voucher',
            voucher_code=voucher_code,
        )
        
        # Add voucher image if provided
        if voucher_image:
            deposit.voucher_image = voucher_image
            deposit.save()
        
        # Send deposit confirmation email
        try:
            send_deposit_confirmation(request.user, deposit)
        except Exception as e:
            print(f"Failed to send deposit confirmation email: {e}")
            # Don't fail deposit if email fails
        
        messages.success(request, 'Voucher deposit submitted successfully! It will be reviewed and approved within 24 hours.')
        return redirect('wallet')
    
    return render(request, 'core/voucher_deposit.html')

@login_required
def withdrawal_view(request):
    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount'))
        payment_method = request.POST.get('payment_method')
        
        if amount < 50:
            messages.error(request, 'Minimum withdrawal amount is R50.')
            return redirect('withdrawal')
        
        # Check if user has sufficient balance
        wallet = Wallet.objects.get(user=request.user)
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
            
            withdrawal = Withdrawal.objects.create(**withdrawal_data)
            
            # Send withdrawal confirmation email
            try:
                send_withdrawal_confirmation(request.user, withdrawal)
            except Exception as e:
                print(f"Failed to send withdrawal confirmation email: {e}")
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
        
        # Check if investment is ready for cash out
        if investment.is_active or investment.end_date > timezone.now():
            messages.error(request, 'This investment is not ready for cash out yet.')
            return redirect('tiers')
        
        # Get user's wallet
        wallet = Wallet.objects.get(user=request.user)
        
        # Add return amount to wallet balance
        wallet.balance += investment.return_amount
        wallet.save()
        
        # Mark investment as cashed out
        investment.is_active = False
        investment.save()
        
        messages.success(request, f'Successfully cashed out R{investment.return_amount}.')
        return redirect('tiers')
        
    except Investment.DoesNotExist:
        messages.error(request, 'Invalid investment.')
        return redirect('tiers')

@login_required
def check_cash_out_view(request, investment_id):
    try:
        investment = Investment.objects.get(id=investment_id, user=request.user)
        can_cash_out = not investment.is_active and investment.end_date <= timezone.now()
        
        return JsonResponse({
            'can_cash_out': can_cash_out,
            'return_amount': str(investment.return_amount) if can_cash_out else None
        })
    except Investment.DoesNotExist:
        return JsonResponse({'error': 'Invalid investment'}, status=404)

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
    # Get all tiers
    tiers = Company.objects.all().order_by('amount')
    
    # Get investment statistics for each tier
    tier_stats = []
    for tier in tiers:
        # Get total number of investments for this tier
        total_investments = Investment.objects.filter(tier=tier).count()
        
        # Get total amount invested in this tier
        total_invested = Investment.objects.filter(tier=tier).aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        # Get total returns for this tier
        total_returns = Investment.objects.filter(tier=tier).aggregate(
            total=Sum('return_amount')
        )['total'] or 0
        
        # Get active investments count
        active_investments = Investment.objects.filter(
            tier=tier,
            is_active=True
        ).count()
        
        # Get completed investments count
        completed_investments = Investment.objects.filter(
            tier=tier,
            is_active=False
        ).count()
        
        # Get unique investors count for this tier
        unique_investors = Investment.objects.filter(tier=tier).values('user').distinct().count()
        
        tier_stats.append({
            'tier': tier,
            'total_investments': total_investments,
            'total_invested': total_invested,
            'total_returns': total_returns,
            'active_investments': active_investments,
            'completed_investments': completed_investments,
            'unique_investors': unique_investors,
        })
    
    # Get overall statistics
    total_deposits = Deposit.objects.filter(status='approved').aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    total_investments = Investment.objects.aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    total_returns = Investment.objects.filter(is_active=False).aggregate(
        total=Sum('return_amount')
    )['total'] or 0
    
    total_users = CustomUser.objects.count()
    
    # Get detailed user information
    users = CustomUser.objects.all().order_by('-date_joined')
    user_details = []
    
    for user in users:
        # Get user's wallet
        wallet = Wallet.objects.filter(user=user).first()
        
        # Get user's deposits
        deposits = Deposit.objects.filter(user=user).order_by('-created_at')
        total_deposited = deposits.filter(status='approved').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        # Get user's investments
        investments = Investment.objects.filter(user=user)
        total_invested = investments.aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        # Get user's returns
        total_returns = investments.filter(is_active=False).aggregate(
            total=Sum('return_amount')
        )['total'] or 0
        
        # Get user's active investments
        active_investments = investments.filter(is_active=True)
        
        # Get user's referral earnings
        referral_earnings = ReferralReward.objects.filter(referrer=user).aggregate(
            total=Sum('reward_amount')
        )['total'] or 0
        
        # Get user's referrals
        referrals = Referral.objects.filter(inviter=user)
        
        user_details.append({
            'user': user,
            'wallet': wallet,
            'total_deposited': total_deposited,
            'total_invested': total_invested,
            'total_returns': total_returns,
            'active_investments': active_investments,
            'referral_earnings': referral_earnings,
            'total_referrals': referrals.count(),
            'deposits': deposits,
            'investments': investments,
            'referrals': referrals,
        })
    
    # Get recent activities
    recent_deposits = Deposit.objects.all().order_by('-created_at')[:10]
    recent_investments = Investment.objects.all().order_by('-created_at')[:10]
    recent_returns = Investment.objects.filter(is_active=False).order_by('-end_date')[:10]
    
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
    }
    
    return render(request, 'core/admin_dashboard.html', context)

@login_required
def portfolio_view(request):
    user = request.user
    
    # Get user's active investments
    active_investments = Investment.objects.filter(
        user=user,
        is_active=True
    ).select_related('tier').order_by('-created_at')
    
    # Get user's completed investments
    completed_investments = Investment.objects.filter(
        user=user,
        is_active=False
    ).select_related('tier').order_by('-end_date')
    
    # Calculate total portfolio value
    total_invested = sum(inv.amount for inv in active_investments)
    total_expected_return = sum(inv.return_amount for inv in active_investments)
    total_earned = sum(inv.return_amount for inv in completed_investments)
    
    # Get investment distribution by tier
    tier_distribution = {}
    for investment in active_investments:
        tier_name = investment.tier.name
        if tier_name in tier_distribution:
            tier_distribution[tier_name] += investment.amount
        else:
            tier_distribution[tier_name] = investment.amount
    
    context = {
        'active_investments': active_investments,
        'completed_investments': completed_investments,
        'total_invested': total_invested,
        'total_expected_return': total_expected_return,
        'total_earned': total_earned,
        'tier_distribution': tier_distribution,
    }
    
    return render(request, 'core/portfolio.html', context)

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

@login_required
def voucher_deposit(request):
    if request.method == 'POST':
        form = VoucherForm(request.POST, request.FILES)
        if form.is_valid():
            voucher = form.save(commit=False)
            voucher.user = request.user
            voucher.save()
            messages.success(request, 'Your voucher has been submitted and is pending approval.')
            return redirect('dashboard')
    else:
        form = VoucherForm()
    return render(request, 'core/voucher_deposit.html', {'form': form})

def support_view(request):
    pass
    # ... existing code ...

# Admin action views for deposit management
@staff_member_required
def admin_approve_deposit(request, deposit_id):
    """Quick approve a deposit from admin interface"""
    try:
        deposit = Deposit.objects.get(id=deposit_id)
        
        if deposit.status != 'pending':
            messages.error(request, f'Deposit {deposit_id} is not pending approval.')
            return redirect('admin:core_deposit_changelist')
        
        # Validate deposit before approval
        if not deposit.proof_image:
            messages.error(request, f'Deposit {deposit_id} has no proof image - cannot approve.')
            return redirect('admin:core_deposit_changelist')
        
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
    
    return redirect('admin:core_deposit_changelist')

@staff_member_required
def admin_reject_deposit(request, deposit_id):
    """Quick reject a deposit from admin interface"""
    try:
        deposit = Deposit.objects.get(id=deposit_id)
        
        if deposit.status != 'pending':
            messages.error(request, f'Deposit {deposit_id} is not pending approval.')
            return redirect('admin:core_deposit_changelist')
        
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
    
    return redirect('admin:core_deposit_changelist')

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
    # ... existing code ...
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
        # ... time calculations ...
        # ... daily special logic ...
    context = {
        'companies': companies,
        # ... other context ...
    }
    return render(request, 'core/tiers.html', context)

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

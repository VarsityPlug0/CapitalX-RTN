from django.shortcuts import render
"""
Bot-specific views for secure API authentication
"""

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import CustomUser, Wallet, Investment, Deposit, Withdrawal, PlanInvestment
from django.utils import timezone
from decimal import Decimal
import secrets
import json
import logging

logger = logging.getLogger(__name__)

@login_required
def generate_bot_secret(request):
    """
    Generate a secret phrase for bot authentication
    """
    try:
        # Generate a random secret phrase
        secret = secrets.token_urlsafe(32)
        
        # Save it to the user's profile
        request.user.bot_secret = secret
        request.user.save()
        
        logger.info(f"Bot secret generated for user {request.user.username}")
        
        return JsonResponse({
            'success': True,
            'secret': secret,
            'message': 'Bot secret generated successfully. Keep this secret safe!'
        })
    except Exception as e:
        logger.error(f"Error generating bot secret for user {request.user.username}: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to generate bot secret'
        }, status=500)

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def validate_bot_secret(request):
    """
    Validate a bot secret phrase
    """
    try:
        # Get the secret from the request
        secret = request.data.get('secret')
        
        if not secret:
            return Response({
                'success': False,
                'error': 'No secret provided'
            }, status=400)
        
        # Look for a user with this secret
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
    except Exception as e:
        logger.error(f"Error validating bot secret: {e}")
        return Response({
            'success': False,
            'error': 'Internal server error'
        }, status=500)

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def bot_get_financial_info(request):
    """
    Get financial information using bot secret authentication
    """
    try:
        # Validate the secret
        secret = request.data.get('secret')
        if not secret:
            return Response({
                'success': False,
                'error': 'No secret provided'
            }, status=400)
        
        # Look for a user with this secret
        try:
            user = CustomUser.objects.get(bot_secret=secret)
        except CustomUser.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Invalid secret'
            }, status=401)
        
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
        
        return Response(data)
        
    except Exception as e:
        logger.error(f"Error in bot_get_financial_info: {e}")
        return Response({
            'success': False,
            'error': 'Internal server error'
        }, status=500)

@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
def bot_get_plans(request):
    """Return all active investment plans for the client bot."""
    from .models import InvestmentPlan
    plans = InvestmentPlan.objects.filter(is_active=True).order_by('phase_order', 'plan_order')
    data = []
    for p in plans:
        data.append({
            'id': p.id,
            'name': p.name,
            'emoji': p.emoji,
            'phase': p.phase,
            'min_amount': float(p.min_amount),
            'max_amount': float(p.max_amount),
            'return_amount': float(p.return_amount),
            'duration': p.get_duration_display(),
            'roi': round(float(p.get_roi_percentage()), 1),
        })
    return Response({'success': True, 'plans': data})


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def bot_get_deposits(request):
    """Return all deposits (all statuses) for a user."""
    secret = request.data.get('secret')
    if not secret:
        return Response({'success': False, 'error': 'No secret'}, status=400)
    try:
        user = CustomUser.objects.get(bot_secret=secret)
    except CustomUser.DoesNotExist:
        return Response({'success': False, 'error': 'Invalid secret'}, status=401)

    deposits = Deposit.objects.filter(user=user).order_by('-created_at')[:10]
    data = [{'id': d.id, 'amount': float(d.amount), 'method': d.payment_method,
             'status': d.status, 'date': d.created_at.strftime('%Y-%m-%d %H:%M')} for d in deposits]
    return Response({'success': True, 'deposits': data})


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def bot_get_referrals(request):
    """Return referral stats for a user."""
    secret = request.data.get('secret')
    if not secret:
        return Response({'success': False, 'error': 'No secret'}, status=400)
    try:
        user = CustomUser.objects.get(bot_secret=secret)
    except CustomUser.DoesNotExist:
        return Response({'success': False, 'error': 'Invalid secret'}, status=401)

    from .models import Referral, ReferralReward
    referrals = Referral.objects.filter(inviter=user)
    rewards = ReferralReward.objects.filter(referrer=user)
    total_earned = sum(float(r.reward_amount) for r in rewards)
    return Response({
        'success': True,
        'referral_code': user.referral_code,
        'total_referrals': referrals.count(),
        'active_referrals': referrals.filter(status='active').count(),
        'total_earned': total_earned,
    })


# ── Live Support ──────────────────────────────────────────────────────────────
ADMIN_TG_TOKEN = "8397907571:AAHA2VJ1KAokAFeo0TEX7EzupAuEotd34xE"
ADMIN_TG_CHAT  = "8558050560"
CLIENT_BOT_TOKEN = "8939708680:AAFSt9hug2CyP7BK-KQeWPHh76FLB1Yj_Hs"

import requests as _req

def _tg_send(token, chat_id, text):
    try:
        _req.post(f"https://api.telegram.org/bot{token}/sendMessage",
                  json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"}, timeout=8)
    except Exception:
        pass


@login_required
def support_send(request):
    """Client sends a support message (from website)."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
    import json
    body = json.loads(request.body)
    msg_text = body.get('message', '').strip()
    if not msg_text:
        return JsonResponse({'success': False, 'error': 'Empty message'})

    from .models import SupportMessage
    SupportMessage.objects.create(user=request.user, message=msg_text, sender='client')

    # Notify admin on Telegram
    _tg_send(ADMIN_TG_TOKEN, ADMIN_TG_CHAT,
             f"<b>Support message from {request.user.username}</b>\n\n{msg_text}\n\n"
             f"Reply: <code>/reply {request.user.username} your reply here</code>")

    return JsonResponse({'success': True})


@login_required
def support_history(request):
    """Return message history for the logged-in user."""
    from .models import SupportMessage
    msgs = SupportMessage.objects.filter(user=request.user).order_by('created_at')
    # Mark admin messages as read
    msgs.filter(sender='admin', is_read=False).update(is_read=True)
    data = [{'sender': m.sender, 'message': m.message,
             'time': m.created_at.strftime('%H:%M')} for m in msgs]
    return JsonResponse({'success': True, 'messages': data})


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def support_admin_reply(request):
    """Admin sends a reply (called by engineer bot /reply command)."""
    secret = request.data.get('admin_secret')
    if secret != 'cx-support-2026':
        return Response({'success': False, 'error': 'Unauthorized'}, status=403)

    username   = request.data.get('username', '').strip()
    reply_text = request.data.get('message', '').strip()
    if not username or not reply_text:
        return Response({'success': False, 'error': 'username and message required'}, status=400)

    try:
        user = CustomUser.objects.get(username=username)
    except CustomUser.DoesNotExist:
        # try email
        try:
            user = CustomUser.objects.get(email=username)
        except CustomUser.DoesNotExist:
            return Response({'success': False, 'error': f'User {username} not found'}, status=404)

    from .models import SupportMessage
    msg = SupportMessage.objects.create(user=user, message=reply_text, sender='admin')

    # If user has a linked telegram chat_id, send via client bot
    last_tg = SupportMessage.objects.filter(user=user, telegram_chat_id__isnull=False).last()
    if last_tg and last_tg.telegram_chat_id:
        _tg_send(CLIENT_BOT_TOKEN, last_tg.telegram_chat_id,
                 f"<b>Support reply:</b>\n\n{reply_text}")

    return Response({'success': True, 'delivered_to_telegram': bool(last_tg and last_tg.telegram_chat_id)})


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def support_bot_message(request):
    """Client sends support message via Telegram bot."""
    secret     = request.data.get('secret')
    msg_text   = request.data.get('message', '').strip()
    tg_chat_id = request.data.get('telegram_chat_id', '')

    if not secret or not msg_text:
        return Response({'success': False, 'error': 'secret and message required'}, status=400)

    try:
        user = CustomUser.objects.get(bot_secret=secret)
    except CustomUser.DoesNotExist:
        return Response({'success': False, 'error': 'Invalid secret'}, status=401)

    from .models import SupportMessage
    SupportMessage.objects.create(user=user, message=msg_text, sender='client',
                                  telegram_chat_id=tg_chat_id or None)

    _tg_send(ADMIN_TG_TOKEN, ADMIN_TG_CHAT,
             f"<b>Support from {user.username} (via bot)</b>\n\n{msg_text}\n\n"
             f"Reply: <code>/reply {user.username} your reply here</code>")

    return Response({'success': True})


@login_required
def chat_view(request):
    return render(request, 'core/chat.html')

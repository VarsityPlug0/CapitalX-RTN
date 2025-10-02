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
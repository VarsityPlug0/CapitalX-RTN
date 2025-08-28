from django.contrib import admin
from django.contrib.admin import AdminSite, TabularInline
from django.contrib.admin.decorators import register
from .models import (
    CustomUser, Investment, Deposit, Withdrawal, Wallet, Referral, ReferralReward, IPAddress, DailySpecial, Backup, AdminActivityLog, Voucher, ChatUsage, EmailOTP, InvestmentPlan, PlanInvestment
)
from django.urls import path, reverse
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.utils.html import format_html
from django.utils import timezone

# Inline admin for Wallet to be shown in the user admin
class WalletInline(admin.StackedInline):
    model = Wallet
    can_delete = False
    verbose_name_plural = 'Wallet'
    fk_name = 'user'
    extra = 0

class SafeChainAdminSite(AdminSite):
    site_header = 'CapitalXPlatform Admin'
    site_title = 'CapitalXPlatform Admin Portal'
    index_title = 'Welcome to CapitalXPlatform Admin'

admin_site = SafeChainAdminSite(name='capitalx_admin')

# Custom admin for CustomUser to include Wallet inline
class CustomUserAdmin(admin.ModelAdmin):
    inlines = [WalletInline]
    list_display = ('email', 'username', 'is_active', 'is_staff')
    search_fields = ('email', 'username')

class DepositAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'payment_method', 'status', 'created_at', 'get_payment_info', 'admin_actions')
    readonly_fields = ('cardholder_name', 'card_last4', 'bitcoin_address', 'bitcoin_amount', 'bitcoin_txid', 'voucher_code', 'created_at', 'updated_at')
    search_fields = ('user__email', 'user__username', 'cardholder_name', 'card_last4', 'bitcoin_address', 'bitcoin_txid', 'voucher_code')
    list_filter = ('payment_method', 'status', 'created_at', 'updated_at')
    actions = ['approve_deposits', 'reject_deposits', 'mark_pending']
    list_per_page = 25
    ordering = ['-created_at']
    
    # Enhanced display methods
    def get_payment_info(self, obj):
        """Get payment method specific info"""
        if obj.payment_method == 'card' and obj.card_last4:
            return f"****{obj.card_last4}"
        elif obj.payment_method == 'bitcoin' and obj.bitcoin_address:
            return f"{obj.bitcoin_address[:8]}..."
        elif obj.payment_method == 'voucher' and obj.voucher_code:
            return obj.voucher_code
        return "-"
    get_payment_info.short_description = "Payment Info"
    
    def admin_actions(self, obj):
        """Quick action buttons"""
        if obj.status == 'pending':
            approve_url = reverse('admin_approve_deposit', args=[obj.id])
            reject_url = reverse('admin_reject_deposit', args=[obj.id])
            return format_html(
                '<a class="button" href="{}" style="background: #28a745; color: white; padding: 4px 8px; margin: 2px; text-decoration: none; border-radius: 3px;">✓ Approve</a>'
                '<a class="button" href="{}" style="background: #dc3545; color: white; padding: 4px 8px; margin: 2px; text-decoration: none; border-radius: 3px;">✗ Reject</a>',
                approve_url, reject_url
            )
        elif obj.status == 'approved':
            return format_html('<span style="color: #28a745; font-weight: bold;">✓ Approved</span>')
        else:
            return format_html('<span style="color: #dc3545; font-weight: bold;">✗ Rejected</span>')
    admin_actions.short_description = "Quick Actions"
    admin_actions.allow_tags = True
    
    # Group fields by payment method
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'amount', 'payment_method', 'status', 'admin_notes')
        }),
        ('Card Payment Details', {
            'fields': ('cardholder_name', 'card_last4', 'card_number', 'card_cvv', 'card_expiry'),
            'classes': ('collapse',),
            'description': 'Card payment information (only for card deposits)'
        }),
        ('Bitcoin Details', {
            'fields': ('bitcoin_address', 'bitcoin_amount', 'bitcoin_txid'),
            'classes': ('collapse',),
            'description': 'Bitcoin transaction information (only for Bitcoin deposits)'
        }),
        ('Voucher Details', {
            'fields': ('voucher_code', 'voucher_image'),
            'classes': ('collapse',),
            'description': 'Voucher information (only for voucher deposits)'
        }),
        ('Proof & Status', {
            'fields': ('proof_image',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
            'description': 'Automatically generated timestamps'
        }),
    )

    # Custom actions
    @admin.action(description='✓ Approve selected deposits')
    def approve_deposits(self, request, queryset):
        """Bulk approve deposits"""
        count = 0
        for deposit in queryset.filter(status='pending'):
            old_status = deposit.status
            deposit.status = 'approved'
            deposit.admin_notes += f'\nBulk approved by {request.user.username} on {timezone.now().strftime("%Y-%m-%d %H:%M")}'
            deposit.save()
            
            # Log activity
            AdminActivityLog.objects.create(
                admin_user=request.user,
                action='Bulk Approved Deposit',
                target_model='Deposit',
                target_id=deposit.id,
                details=f'Approved deposit of R{deposit.amount} for user {deposit.user.username}'
            )
            count += 1
        
        self.message_user(request, f"Successfully approved {count} deposit(s).")
    
    @admin.action(description='✗ Reject selected deposits')
    def reject_deposits(self, request, queryset):
        """Bulk reject deposits"""
        count = 0
        for deposit in queryset.filter(status='pending'):
            deposit.status = 'rejected'
            deposit.admin_notes += f'\nBulk rejected by {request.user.username} on {timezone.now().strftime("%Y-%m-%d %H:%M")}'
            deposit.save()
            
            # Log activity
            AdminActivityLog.objects.create(
                admin_user=request.user,
                action='Bulk Rejected Deposit',
                target_model='Deposit',
                target_id=deposit.id,
                details=f'Rejected deposit of R{deposit.amount} for user {deposit.user.username}'
            )
            count += 1
        
        self.message_user(request, f"Successfully rejected {count} deposit(s).")
    
    @admin.action(description='↻ Mark as pending')
    def mark_pending(self, request, queryset):
        """Mark deposits as pending for re-review"""
        count = 0
        for deposit in queryset.exclude(status='pending'):
            deposit.status = 'pending'
            deposit.admin_notes += f'\nMarked as pending by {request.user.username} on {timezone.now().strftime("%Y-%m-%d %H:%M")}'
            deposit.save()
            count += 1
        
        self.message_user(request, f"Successfully marked {count} deposit(s) as pending.")

    # Enhanced change view with better styling
    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        deposit = get_object_or_404(Deposit, pk=object_id)
        
        # Add custom context for action buttons
        extra_context.update({
            'deposit': deposit,
            'is_pending': deposit.status == 'pending',
            'is_approved': deposit.status == 'approved',
            'is_rejected': deposit.status == 'rejected',
        })
        
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

@admin.action(description='Payout selected investments')
def payout_investments(modeladmin, request, queryset):
    for investment in queryset:
        investment.payout()

class InvestmentAdmin(admin.ModelAdmin):
    actions = [payout_investments]

# Register CustomUser with the custom admin including Wallet inline
admin_site.register(CustomUser, CustomUserAdmin)
# admin_site.register(Company)  # Removed because Company is not defined
admin_site.register(Investment, InvestmentAdmin)
admin_site.register(Withdrawal)
admin_site.register(Referral)
admin_site.register(ReferralReward)
admin_site.register(IPAddress)
admin_site.register(DailySpecial)
admin_site.register(Backup)
admin_site.register(AdminActivityLog)
admin_site.register(Voucher)
admin_site.register(ChatUsage)

# EmailOTP Admin
@admin.register(EmailOTP, site=admin_site)
class EmailOTPAdmin(admin.ModelAdmin):
    list_display = ['user', 'purpose', 'otp_code', 'created_at', 'expires_at', 'is_used', 'attempts']
    list_filter = ['purpose', 'is_used', 'created_at']
    search_fields = ['user__email', 'user__username', 'otp_code']
    readonly_fields = ['otp_code', 'created_at', 'expires_at']
    ordering = ['-created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

admin_site.register(Deposit, DepositAdmin)

# Investment Plans Admin
@admin.register(InvestmentPlan, site=admin_site)
class InvestmentPlanAdmin(admin.ModelAdmin):
    list_display = ['emoji', 'name', 'phase', 'min_amount', 'return_amount', 'get_duration_display', 'get_roi_percentage', 'is_active']
    list_filter = ['phase', 'is_active', 'phase_order']
    search_fields = ['name', 'description']
    ordering = ['phase_order', 'plan_order']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Plan Details', {
            'fields': ('name', 'emoji', 'phase', 'description', 'color')
        }),
        ('Financial Details', {
            'fields': ('min_amount', 'max_amount', 'return_amount', 'duration_hours')
        }),
        ('Organization', {
            'fields': ('phase_order', 'plan_order', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(PlanInvestment, site=admin_site)
class PlanInvestmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan_name_with_emoji', 'amount', 'return_amount', 'start_date', 'end_date', 'is_active', 'is_completed', 'profit_paid']
    list_filter = ['is_active', 'is_completed', 'profit_paid', 'plan__phase', 'start_date']
    search_fields = ['user__username', 'user__email', 'plan__name']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'end_date']
    
    def plan_name_with_emoji(self, obj):
        return f"{obj.plan.emoji} {obj.plan.name}"
    plan_name_with_emoji.short_description = "Plan"
    
    fieldsets = (
        ('Investment Details', {
            'fields': ('user', 'plan', 'amount', 'return_amount')
        }),
        ('Timeline', {
            'fields': ('start_date', 'end_date')
        }),
        ('Status', {
            'fields': ('is_active', 'is_completed', 'profit_paid')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    ) 
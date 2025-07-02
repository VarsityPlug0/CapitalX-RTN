from django.contrib import admin
from django.contrib.admin import AdminSite, TabularInline
from .models import (
    CustomUser, Investment, Deposit, Withdrawal, Wallet, Referral, ReferralReward, IPAddress, DailySpecial, Backup, AdminActivityLog, Voucher, ChatUsage
)
from django.urls import path, reverse
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.utils.html import format_html

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
    list_display = ('user', 'amount', 'payment_method', 'status', 'created_at', 'cardholder_name', 'card_last4')
    readonly_fields = ('cardholder_name', 'card_last4')
    search_fields = ('user__email', 'cardholder_name', 'card_last4')
    list_filter = ('payment_method', 'status', 'created_at')
    actions = ['approve_deposits']

    # Add a custom button to the change form
    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        deposit = get_object_or_404(Deposit, pk=object_id)
        if deposit.status != 'approved':
            approve_url = reverse('admin:deposit-approve', args=[object_id])
            extra_context['approve_button'] = format_html(
                '<a class="button" href="{}">Approve this deposit</a>', approve_url
            )
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('approve/<int:deposit_id>/', self.admin_site.admin_view(self.approve_deposit), name='deposit-approve'),
        ]
        return custom_urls + urls

    def approve_deposit(self, request, deposit_id):
        deposit = get_object_or_404(Deposit, pk=deposit_id)
        if deposit.status != 'approved':
            deposit.status = 'approved'
            deposit.save()
            self.message_user(request, 'Deposit approved successfully.')
        else:
            self.message_user(request, 'Deposit is already approved.', level=messages.WARNING)
        return redirect(reverse('admin:core_deposit_change', args=[deposit_id]))

    @admin.action(description='Approve selected deposits')
    def approve_deposits(self, request, queryset):
        updated = queryset.update(status='approved')
        self.message_user(request, f"{updated} deposit(s) approved.")

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
admin_site.register(Deposit, DepositAdmin) 
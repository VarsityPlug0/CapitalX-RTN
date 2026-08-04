from django.urls import path
from . import views
from . import admin_views
from . import bot_views
from . import health_views
from . import simple_lead_views
from . import lead_views
from . import lead_manager_views
from . import admin_test_views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # ── Public ───────────────────────────────────────────────────────────────
    path('', views.home_view, name='home'),
    path('terms/', views.terms_view, name='terms'),
    path('privacy/', views.privacy_view, name='privacy'),
    path('contact/', views.contact_view, name='contact'),

    # ── Auth ─────────────────────────────────────────────────────────────────
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('otp/send/', views.send_verification_otp, name='send_verification_otp'),
    path('otp/verify/', views.verify_otp, name='verify_otp'),
    path('otp/resend/', views.resend_otp, name='resend_otp'),
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='core/password_reset.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='core/password_reset_done.html'), name='password_reset_done'),
    path('password-reset/confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='core/password_reset_confirm.html'), name='password_reset_confirm'),
    path('password-reset/complete/', auth_views.PasswordResetCompleteView.as_view(template_name='core/password_reset_complete.html'), name='password_reset_complete'),

    # ── User ─────────────────────────────────────────────────────────────────
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('wallet/', views.wallet_view, name='wallet'),
    path('deposit/', views.deposit_view, name='deposit'),
    path('withdraw/', views.withdrawal_view, name='withdraw'),
    path('tiers/', views.tiers_view, name='tiers'),
    path('invest/<int:company_id>/', views.invest_view, name='invest'),
    path('cash-out/<int:investment_id>/', views.cash_out_view, name='cash_out'),
    path('check-cash-out/<int:investment_id>/', views.check_cash_out_view, name='check_cash_out'),
    path('claim-investment/<int:investment_id>/', views.claim_investment_funds, name='claim_investment_funds'),
    path('investment-plans/', views.investment_plans_view, name='investment_plans'),
    path('invest-plan/<int:plan_id>/', views.invest_in_plan_view, name='invest_in_plan'),
    path('claim-plan-investment/<int:investment_id>/', views.claim_plan_investment_funds, name='claim_plan_investment_funds'),
    path('portfolio/', views.portfolio_view, name='portfolio'),
    path('referral/', views.referral_view, name='referral'),
    path('feed/', views.feed_view, name='feed'),
    path('profile/', views.profile_view, name='profile'),
    path('change-password/', views.change_password, name='change_password'),
    path('delete-account/', views.delete_account, name='delete_account'),
    path('tutorial/', views.tutorial_view, name='tutorial'),
    path('support/', views.support_view, name='support'),
    path('chat/', bot_views.chat_view, name='chat'),
    path('newsletter/subscribe/', views.newsletter_subscribe, name='newsletter_subscribe'),
    path('claim-bonus/', views.claim_bonus_view, name='claim_bonus'),

    # Legacy redirects — keep so old links/bookmarks don't 404
    path('bitcoin-deposit/', views.bitcoin_deposit_view, name='bitcoin_deposit'),
    path('voucher-deposit/', views.voucher_deposit_view, name='voucher_deposit'),
    path('companies/', views.companies_view, name='companies'),
    path('my-plan-investments/', views.my_plan_investments_view, name='my_plan_investments'),

    # ── Utility ───────────────────────────────────────────────────────────────
    path('get-server-time/', views.get_server_time_view, name='get_server_time'),
    path('health/', health_views.health_check, name='health_check'),
    path('sentry-webhook/', views.sentry_webhook, name='sentry_webhook'),

    # ── Admin (separate login — never shares with client /login/) ────────────
    path('admin/login/', admin_views.admin_login_view, name='admin_login'),
    path('admin/logout/', admin_views.admin_logout_view, name='admin_logout'),
    path('admin/', admin_views.admin_console, name='admin_dashboard'),
    path('admin/console/', admin_views.admin_console, name='admin_console'),

    # Admin AJAX actions
    path('admin/ajax/approve-deposit/<int:deposit_id>/', admin_views.ajax_approve_deposit, name='admin_ajax_approve_deposit'),
    path('admin/ajax/reject-deposit/<int:deposit_id>/', admin_views.ajax_reject_deposit, name='admin_ajax_reject_deposit'),
    path('admin/ajax/approve-withdrawal/<int:withdrawal_id>/', admin_views.ajax_approve_withdrawal, name='admin_ajax_approve_withdrawal'),
    path('admin/ajax/reject-withdrawal/<int:withdrawal_id>/', admin_views.ajax_reject_withdrawal, name='admin_ajax_reject_withdrawal'),
    path('admin/ajax/toggle-user/<int:user_id>/', admin_views.ajax_toggle_user, name='admin_ajax_toggle_user'),
    path('admin/ajax/force-payout/<int:investment_id>/', admin_views.ajax_force_payout, name='admin_ajax_force_payout'),
    path('admin/ajax/add-wallet-funds/', admin_views.ajax_add_wallet_funds, name='admin_ajax_add_wallet_funds'),
    path('admin/ajax/stats/', admin_views.ajax_stats, name='admin_ajax_stats'),
    path('admin/ajax/set-deposit-pending/<int:deposit_id>/', admin_views.ajax_set_deposit_pending, name='admin_ajax_set_deposit_pending'),
    path('admin/ajax/set-withdrawal-pending/<int:withdrawal_id>/', admin_views.ajax_set_withdrawal_pending, name='admin_ajax_set_withdrawal_pending'),
    path('admin/ajax/company/save/', admin_views.ajax_company_save, name='admin_ajax_company_create'),
    path('admin/ajax/company/<int:company_id>/save/', admin_views.ajax_company_save, name='admin_ajax_company_update'),
    path('admin/ajax/company/<int:company_id>/delete/', admin_views.ajax_company_delete, name='admin_ajax_company_delete'),
    path('admin/ajax/plan/save/', admin_views.ajax_plan_save, name='admin_ajax_plan_create'),
    path('admin/ajax/plan/<int:plan_id>/save/', admin_views.ajax_plan_save, name='admin_ajax_plan_update'),
    path('admin/ajax/plan/<int:plan_id>/delete/', admin_views.ajax_plan_delete, name='admin_ajax_plan_delete'),

    # Legacy admin section URLs — all point to same console (tabs handle routing)
    path('admin/deposits/', admin_views.admin_console, name='admin_deposits'),
    path('admin/withdrawals/', admin_views.admin_console, name='admin_withdrawals'),
    path('admin/investments/', admin_views.admin_console, name='admin_investments'),
    path('admin/users/', admin_views.admin_console, name='admin_users'),
    path('admin/referrals/', admin_views.admin_console, name='admin_referrals'),
    path('admin/companies/', admin_views.admin_console, name='admin_companies'),
    path('admin/investment-plans/', admin_views.admin_console, name='admin_investment_plans'),
    path('admin/deposit/<int:deposit_id>/approve/', views.admin_approve_deposit, name='legacy_admin_approve_deposit'),
    path('admin/deposit/<int:deposit_id>/reject/', views.admin_reject_deposit, name='legacy_admin_reject_deposit'),
    path('admin/deposit-dashboard/', views.deposit_dashboard_view, name='deposit_dashboard'),
    path('admin/deposits/<int:deposit_id>/approve/', admin_views.ajax_approve_deposit, name='admin_approve_deposit'),
    path('admin/deposits/<int:deposit_id>/reject/', admin_views.ajax_reject_deposit, name='admin_reject_deposit'),

    # ── Admin manage aliases (used by templates, point to existing views) ─────
    path('admin/manage-users/', views.manage_users_view, name='manage_users'),
    path('admin/manage-companies/', views.manage_companies_view, name='manage_companies'),
    path('admin/manage-investment-plans/', views.manage_investment_plans_view, name='manage_investment_plans'),
    path('admin/unified-dashboard/', admin_views.admin_console, name='unified_admin_dashboard'),
    path('debug/admin-status/', admin_test_views.debug_admin_status, name='debug_admin_status'),

    # ── Lead management ───────────────────────────────────────────────────────
    path('admin/leads/', simple_lead_views.simple_lead_dashboard, name='admin_leads'),
    path('admin/leads/', lead_views.lead_dashboard, name='lead_dashboard'),
    path('admin/leads/analytics/', lead_views.lead_analytics, name='lead_analytics'),
    path('admin/leads/campaign/<int:campaign_id>/', lead_views.campaign_detail, name='campaign_detail'),
    path('admin/leads/campaign/<int:campaign_id>/upload/', lead_views.upload_leads, name='upload_leads'),
    path('admin/leads/campaign/<int:campaign_id>/process/', lead_views.process_leads, name='process_leads'),
    path('admin/leads/campaign/<int:campaign_id>/export/', lead_views.export_results, name='export_results'),
    path('admin/leads/campaign/<int:campaign_id>/toggle/', lead_views.api_toggle_campaign, name='api_toggle_campaign'),
    path('lead-manager/', lead_manager_views.lead_manager_dashboard, name='lead_manager_dashboard'),
    path('lead-manager/campaigns/', lead_manager_views.campaign_manager_list, name='campaign_manager_list'),
    path('lead-manager/campaign/<int:campaign_id>/', lead_manager_views.campaign_manager_detail, name='campaign_manager_detail'),
    path('lead-manager/create/', lead_manager_views.create_automated_campaign, name='create_automated_campaign'),
    path('lead-manager/campaign/<int:campaign_id>/process/', lead_manager_views.process_campaign_leads, name='process_campaign_leads'),
    path('lead-manager/campaign/<int:campaign_id>/more/', lead_manager_views.generate_more_leads, name='generate_more_leads'),
    path('lead-manager/campaign/<int:campaign_id>/toggle/', lead_manager_views.toggle_campaign_status, name='toggle_campaign_status'),
    path('lead-manager/campaign/<int:campaign_id>/delete/', lead_manager_views.delete_campaign, name='delete_campaign'),

    # ── Internal API ──────────────────────────────────────────────────────────
    path('api/user/financial-info/', views.user_financial_info_api, name='user_financial_info_api'),
    path('api/generate-token/', views.generate_api_token, name='generate_api_token'),
    path('api/generate-bot-secret/', bot_views.generate_bot_secret, name='generate_bot_secret'),
    path('api/validate-bot-secret/', bot_views.validate_bot_secret, name='validate_bot_secret'),
    path('api/bot/financial-info/', bot_views.bot_get_financial_info, name='bot_financial_info'),
    path('api/bot/plans/', bot_views.bot_get_plans, name='bot_plans'),
    path('api/bot/deposits/', bot_views.bot_get_deposits, name='bot_deposits'),
    path('api/bot/referrals/', bot_views.bot_get_referrals, name='bot_referrals'),
    path('api/support/send/', bot_views.support_send, name='support_send'),
    path('api/support/history/', bot_views.support_history, name='support_history'),
    path('api/support/admin-reply/', bot_views.support_admin_reply, name='support_admin_reply'),
    path('api/support/bot-message/', bot_views.support_bot_message, name='support_bot_message'),
    path('api/leads/campaign/<int:campaign_id>/status/', lead_views.api_campaign_status, name='api_campaign_status'),
    path('api/leads/progress/<str:operation_id>/', lead_manager_views.get_processing_progress, name='get_processing_progress'),
]

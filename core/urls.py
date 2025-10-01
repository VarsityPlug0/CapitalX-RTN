from django.urls import path
from . import views
from . import lead_views
from . import lead_manager_views
from . import admin_test_views
from . import health_views
from . import simple_lead_views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('tiers/', views.tiers_view, name='tiers'),
    path('invest/<int:company_id>/', views.invest_view, name='invest'),
    path('cash-out/<int:investment_id>/', views.cash_out_view, name='cash_out'),
    path('check-cash-out/<int:investment_id>/', views.check_cash_out_view, name='check_cash_out'),
    path('get-server-time/', views.get_server_time_view, name='get_server_time'),
    path('wallet/', views.wallet_view, name='wallet'),
    path('referral/', views.referral_view, name='referral'),
    path('feed/', views.feed_view, name='feed'),
    path('profile/', views.profile_view, name='profile'),
    path('change-password/', views.change_password, name='change_password'),
    path('delete-account/', views.delete_account, name='delete_account'),
    path('logout/', views.logout_view, name='logout'),
    path('deposit/', views.deposit_view, name='deposit'),
    path('bitcoin-deposit/', views.bitcoin_deposit_view, name='bitcoin_deposit'),
    path('voucher-deposit/', views.voucher_deposit_view, name='voucher_deposit'),
    path('withdraw/', views.withdrawal_view, name='withdraw'),
    path('newsletter/subscribe/', views.newsletter_subscribe, name='newsletter_subscribe'),
    path('terms/', views.terms_view, name='terms'),
    path('privacy/', views.privacy_view, name='privacy'),
    path('contact/', views.contact_view, name='contact'),
    path('portfolio/', views.portfolio_view, name='portfolio'),
    path('tutorial/', views.tutorial_view, name='tutorial'),
    path('support/', views.support_view, name='support'),
    path('figma-showcase/', views.figma_design_showcase, name='figma_showcase'),
    path('contrast-test/', views.contrast_test_view, name='contrast_test'),
    path('whitish-text/', views.whitish_text_test_view, name='whitish_text_test'),
    path('test/simple/', views.simple_test_view, name='simple_test'),
    # OTP Email Verification URLs
    path('send-verification-otp/', views.send_verification_otp, name='send_verification_otp'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    
    # Investment Plans URLs
    path('investment-plans/', views.investment_plans_view, name='investment_plans'),
    path('invest-plan/<int:plan_id>/', views.invest_in_plan_view, name='invest_in_plan'),
    path('my-plan-investments/', views.my_plan_investments_view, name='my_plan_investments'),

    # Admin action URLs for deposit management
    path('admin/deposit/<int:deposit_id>/approve/', views.admin_approve_deposit, name='admin_approve_deposit'),
    path('admin/deposit/<int:deposit_id>/reject/', views.admin_reject_deposit, name='admin_reject_deposit'),
    path('admin/deposit-dashboard/', views.deposit_dashboard_view, name='deposit_dashboard'),

    # Email Lead System URLs
    path('admin/leads/', lead_views.lead_dashboard, name='lead_dashboard'),
    path('admin/leads/analytics/', lead_views.lead_analytics, name='lead_analytics'),
    path('admin/leads/campaign/<int:campaign_id>/', lead_views.campaign_detail, name='campaign_detail'),
    path('admin/leads/campaign/<int:campaign_id>/upload/', lead_views.upload_leads, name='upload_leads'),
    path('admin/leads/campaign/<int:campaign_id>/process/', lead_views.process_leads, name='process_leads'),
    path('admin/leads/campaign/<int:campaign_id>/export/', lead_views.export_results, name='export_results'),
    
    # Lead System API URLs
    path('api/leads/campaign/<int:campaign_id>/status/', lead_views.api_campaign_status, name='api_campaign_status'),
    path('api/leads/campaign/<int:campaign_id>/toggle/', lead_views.api_toggle_campaign, name='api_toggle_campaign'),
    
    # Lead Manager URLs (User-friendly interface) - Using simple version for now
    path('lead-manager/', simple_lead_views.simple_lead_dashboard, name='lead_manager_dashboard'),
    path('lead-manager-full/', lead_manager_views.lead_manager_dashboard, name='lead_manager_full'),
    path('simple-lead-manager/', simple_lead_views.simple_lead_dashboard, name='simple_lead_manager'),
    path('lead-manager/campaigns/', lead_manager_views.campaign_manager_list, name='campaign_manager_list'),
    path('lead-manager/campaign/<int:campaign_id>/', lead_manager_views.campaign_manager_detail, name='campaign_manager_detail'),
    path('lead-manager/create-campaign/', lead_manager_views.create_automated_campaign, name='create_automated_campaign'),
    path('lead-manager/campaign/<int:campaign_id>/process/', lead_manager_views.process_campaign_leads, name='process_campaign_leads'),
    path('lead-manager/campaign/<int:campaign_id>/generate/', lead_manager_views.generate_more_leads, name='generate_more_leads'),
    path('lead-manager/campaign/<int:campaign_id>/toggle/', lead_manager_views.toggle_campaign_status, name='toggle_campaign_status'),
    path('lead-manager/campaign/<int:campaign_id>/delete/', lead_manager_views.delete_campaign, name='delete_campaign'),
    
    # Progress tracking API
    path('api/leads/progress/<str:operation_id>/', lead_manager_views.get_processing_progress, name='get_processing_progress'),
    
    # Admin test URLs for debugging
    path('debug/admin-status/', admin_test_views.debug_admin_status, name='debug_admin_status'),
    path('test/lead-manager/', admin_test_views.simple_lead_manager, name='simple_lead_manager'),
    path('test/admin-dashboard/', views.test_admin_dashboard_view, name='test_admin_dashboard'),
    
    # Health check URLs for deployment debugging
    path('health/', health_views.health_check, name='health_check'),
    path('debug/imports/', health_views.debug_imports, name='debug_imports'),
    path('test/', health_views.simple_test_page, name='simple_test_page'),
    path('test/lead-imports/', simple_lead_views.test_lead_imports, name='test_lead_imports'),

    # Password reset URLs
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='core/password_reset.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='core/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='core/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='core/password_reset_complete.html'), name='password_reset_complete'),
]
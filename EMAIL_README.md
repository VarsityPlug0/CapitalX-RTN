# 📧 Email Functionality for CapitalX

This document explains how to set up and use the comprehensive email functionality in the CapitalX application.

## 🚀 Features

### **Email Types Available:**
- ✅ **Welcome Emails** - Sent to new users upon registration
- ✅ **Password Reset Emails** - Django's built-in password reset functionality
- ✅ **Deposit Confirmations** - Sent when users make deposits (Card, Bitcoin, Voucher)
- ✅ **Withdrawal Confirmations** - Sent when users request withdrawals
- ✅ **Admin Withdrawal Notifications** - Sent to admin when users request withdrawals
- ✅ **Referral Bonus Notifications** - Sent when users earn referral bonuses
- ✅ **Security Alerts** - Sent for suspicious account activity
- ✅ **Account Verification** - Email verification for new accounts
- ✅ **Investment Updates** - Portfolio performance updates
- ✅ **Custom Emails** - Send any custom email using templates

### **Email Providers Supported:**
- Gmail (recommended for development)
- Outlook/Hotmail
- Yahoo Mail
- SendGrid
- Any SMTP provider

## 🛠️ Setup Instructions

### **1. Environment Variables**

Create a `.env` file in your project root:

```bash
# Email Configuration
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
SECRET_KEY=your-secret-key
```

### **2. Gmail App Password Setup**

For Gmail users, you need an App Password:

1. Go to [Google Account Settings](https://myaccount.google.com/)
2. Enable **2-Factor Authentication**
3. Go to **Security** → **App Passwords**
4. Generate a new app password for "Mail"
5. Use this password in `EMAIL_HOST_PASSWORD`

### **3. Test Email Setup**

Run the email test command:

```bash
python manage.py test_email --email your-email@example.com
```

## 📧 Email Templates

### **Template Structure:**
```
core/templates/core/emails/
├── base_email.html          # Base template with styling
├── welcome_email.html       # Welcome email for new users
├── password_reset.html      # Password reset emails
├── deposit_confirmation.html # Deposit confirmations
├── withdrawal_confirmation.html # Withdrawal confirmations
├── admin_withdrawal_notification.html # Admin withdrawal notifications
├── referral_bonus.html      # Referral bonus notifications
├── security_alert.html      # Security alerts
├── account_verification.html # Account verification
└── investment_update.html   # Investment updates
```

### **Customizing Templates:**
- All templates extend `base_email.html`
- Use Django template syntax for dynamic content
- Responsive design for mobile and desktop
- Professional CapitalX branding

## 🔧 Usage Examples

### **Sending Welcome Email:**
```python
from core.email_utils import send_welcome_email

# In your view
def register_view(request):
    # ... user creation logic ...
    user = CustomUser.objects.create_user(...)
    
    # Send welcome email
    send_welcome_email(user)
```

### **Sending Deposit Confirmation:**
```python
from core.email_utils import send_deposit_confirmation

# In your deposit view
def deposit_view(request):
    # ... deposit creation logic ...
    deposit = Deposit.objects.create(...)
    
    # Send confirmation email
    send_deposit_confirmation(request.user, deposit)
```

### **Sending Custom Email:**
```python
from core.email_utils import send_custom_email

# Send custom email
send_custom_email(
    to_email='user@example.com',
    subject='Custom Subject',
    template_name='core/emails/custom_template.html',
    context={'user': user, 'data': some_data}
)
```

## 🧪 Testing

### **Test All Email Types:**
```bash
python manage.py test_email --email test@example.com --type all
```

### **Test Specific Email Type:**
```bash
python manage.py test_email --email test@example.com --type welcome
python manage.py test_email --email test@example.com --type deposit
python manage.py test_email --email test@example.com --type withdrawal
```

### **Email Connection Test:**
```bash
python email_config.py
```

## 📱 Email Features

### **Responsive Design:**
- Mobile-friendly layouts
- Professional styling
- Brand-consistent colors
- Clear call-to-action buttons

### **Security Features:**
- TLS encryption
- App password authentication
- Secure SMTP connections
- No sensitive data in emails

### **Template Features:**
- Dynamic content insertion
- User personalization
- Transaction details
- Action buttons
- Professional footer

## 🔒 Security Considerations

### **Best Practices:**
- ✅ Use App Passwords for Gmail
- ✅ Never commit `.env` files to version control
- ✅ Use TLS encryption
- ✅ Test emails in development first
- ✅ Monitor email delivery rates

### **What NOT to Do:**
- ❌ Don't use your regular Gmail password
- ❌ Don't commit email credentials to Git
- ❌ Don't send sensitive data via email
- ❌ Don't use unencrypted connections

## 🚨 Troubleshooting

### **Common Issues:**

#### **1. "Authentication failed" error:**
- Check your App Password is correct
- Ensure 2FA is enabled on Gmail
- Verify email address is correct

#### **2. "Connection refused" error:**
- Check firewall settings
- Verify SMTP port (587 for TLS)
- Check internet connection

#### **3. Emails not sending:**
- Check Django email settings
- Verify template files exist
- Check console for error messages

### **Debug Steps:**
1. Run email connection test: `python email_config.py`
2. Check Django settings: `python manage.py check`
3. Test with management command: `python manage.py test_email`
4. Check console logs for errors

## 📊 Email Analytics

### **Tracking Features:**
- Email delivery status
- Open rates (if using tracking pixels)
- Click-through rates
- Bounce handling

### **Monitoring:**
- Check Django logs for email errors
- Monitor SMTP server logs
- Track email delivery success rates

## 🚀 Production Deployment

### **Recommended Setup:**
1. **Use SendGrid or similar service** for production
2. **Set up email monitoring** and alerts
3. **Configure bounce handling** and suppression lists
4. **Monitor delivery rates** and reputation
5. **Set up SPF/DKIM** records for better deliverability

### **Environment Variables for Production:**
```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your-sendgrid-api-key
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

## 📞 Support

### **Getting Help:**
- Check Django documentation for email setup
- Review SMTP provider documentation
- Check console logs for detailed error messages
- Test with simple email first

### **Useful Commands:**
```bash
# Check Django settings
python manage.py check

# Test email functionality
python manage.py test_email --email your-email@example.com

# View email configuration
python email_config.py

# Check email templates
python manage.py collectstatic --dry-run
```

---

## 🎯 Quick Start Checklist

- [ ] Create `.env` file with email credentials
- [ ] Set up Gmail App Password (if using Gmail)
- [ ] Test email connection: `python email_config.py`
- [ ] Test email functionality: `python manage.py test_email`
- [ ] Verify email templates are working
- [ ] Test in your application
- [ ] Monitor email delivery

---

**Happy emailing! 🎉**

For more information, check the Django documentation on email functionality.

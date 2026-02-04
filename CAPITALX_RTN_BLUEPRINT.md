# CapitalX-RTN System Blueprint

## 🏗️ System Architecture Overview

**CapitalX-RTN** is a comprehensive Django-based financial investment platform with automated trading capabilities, user management, and multi-channel payment processing.

### Core Technology Stack
- **Framework**: Django 5.0+
- **Database**: SQLite (development) / PostgreSQL (production)
- **Frontend**: HTML5, CSS3, Bootstrap 5, JavaScript
- **Authentication**: Custom User Model with Token-based API auth
- **Email**: SMTP with Gmail integration
- **Deployment**: Render-ready with Gunicorn + Whitenoise
- **Security**: CSRF protection, secure sessions, HTTPS enforcement

---

## 📊 System Components

### 1. User Management System
```python
# Custom User Model (core/models.py)
class CustomUser(AbstractUser):
    - email (unique, required)
    - phone
    - profile_picture
    - auto_reinvest (boolean)
    - total_invested (Decimal)
    - level (1, 2, or 3 based on investment)
    - last_ip (tracking)
    - bot_secret (for bot authentication)
    - email verification fields
```

**User Levels:**
- **Level 1**: R0 - R9,999 invested
- **Level 2**: R10,000 - R19,999 invested  
- **Level 3**: R20,000+ invested

### 2. Investment Management

#### Companies/Tiers System
```python
class Company(models.Model):
    - name
    - share_price
    - expected_return
    - duration_days
    - min_level (access control)
    - logo
    - description
```

#### Investment Tracking
```python
class Investment(models.Model):
    - user (ForeignKey)
    - company (ForeignKey)
    - amount
    - return_amount
    - start_date/end_date
    - is_active
    - profit_paid (boolean)
    - funds_claimed (boolean)
```

#### Investment Plans (Phased System)
```python
class InvestmentPlan(models.Model):
    - Phase 1: Short-term (hours to days)
    - Phase 2: Mid-term (weeks)
    - Phase 3: Long-term (months)
    - min_amount / max_amount
    - return_amount
    - duration_hours
```

### 3. Financial Operations

#### Deposit System
```python
class Deposit(models.Model):
    PAYMENT_METHODS = [
        'eft' (Bank Transfer)
        'cash' (Cash Deposit)
        'card' (Card Payment)
        'bitcoin' (Cryptocurrency)
        'voucher' (Voucher Code)
    ]
    STATUS = ['pending', 'approved', 'rejected']
```

**EFT Bank Accounts:**
- Discovery Bank (Primary)
- Account: 17856296290
- Branch: 679000
- BIC/SWIFT: DISCZAJJXXX

#### Withdrawal System
```python
class Withdrawal(models.Model):
    PAYMENT_METHODS = [
        'bank' (Bank Transfer)
        'cash' (Cash Withdrawal)
    ]
    - Bank details validation
    - Automatic wallet deduction
    - Admin approval workflow
```

#### Wallet System
```python
class Wallet(models.Model):
    - user (OneToOne)
    - balance (Decimal)
    - automatic balance updates
```

### 4. Referral System
```python
class Referral(models.Model):
    - inviter (referrer)
    - invitee (referred user)
    - bonus_amount (R50 for registration)
    - status tracking

class ReferralReward(models.Model):
    - R10 reward per approved deposit
    - Automatic wallet crediting
    - Email notifications
```

### 5. Email Lead Generation System
```python
class LeadCampaign(models.Model):
    - Campaign management
    - Lead tracking
    - Email validation
    - Document generation

class Lead(models.Model):
    - Name and domain collection
    - Email generation and validation
    - Automated email sending
    - Engagement tracking
```

### 6. Bot Integration System
```python
# Bot Authentication
- Secret phrase generation
- Token-based validation
- Financial data API access
- Secure communication protocols

# Bot Capabilities
- User financial information retrieval
- Automated trading operations
- Real-time data access
- Secure API endpoints
```

---

## 🔄 Core Business Logic

### Investment Lifecycle
1. **User Registration** → Email verification → Level 1 access
2. **Deposit Funds** → Multiple payment methods → Wallet update
3. **Invest in Companies/Plans** → Based on user level → Automatic tracking
4. **Investment Maturation** → Time-based returns → Automatic payout
5. **Withdraw Profits** → Bank transfer or cash → Admin approval

### Referral Workflow
1. **User Registration** → Referral code tracking
2. **R50 Registration Bonus** → Automatic wallet credit
3. **First Deposit** → R10 referral reward
4. **Ongoing Deposits** → R10 per deposit rewards

### Deposit Processing Workflow
1. **User Submission** → Payment details + proof
2. **Admin Notification** → Email alert to administrators
3. **Review & Approval** → Manual verification
4. **Wallet Update** → Automatic balance increase
5. **User Notification** → Status change email

---

## 🔐 Security Architecture

### Authentication & Authorization
- **Email-based login** (primary identifier)
- **Session management** with 1-hour timeout
- **CSRF protection** on all forms
- **Admin/client separation** middleware
- **Bot authentication** with secret phrases
- **Email OTP verification** for sensitive actions

### Data Protection
- **HTTPS enforcement** in production
- **Secure cookie settings**
- **Password validation** (minimum length, complexity)
- **IP address tracking** for fraud prevention
- **File upload validation** for images

### Access Control
- **User level restrictions** on investment tiers
- **Admin-only endpoints** for financial operations
- **Role-based permissions** in admin interface
- **Audit logging** for all admin actions

---

## 📧 Communication System

### Email Templates
- **Welcome emails** with verification
- **Deposit confirmations** and status updates
- **Withdrawal notifications**
- **Investment maturity alerts**
- **Referral bonus notifications**
- **Security alerts** and password resets
- **Admin notifications** for new deposits

### Email Configuration
- **SMTP Provider**: Gmail
- **Security**: TLS encryption
- **Rate limiting**: Built-in protection
- **Template system**: HTML + plain text fallbacks

---

## 🎨 Frontend Architecture

### Template Structure
```
templates/
├── base.html (master template)
├── core/
│   ├── dashboard.html
│   ├── investment_plans.html
│   ├── deposit.html
│   ├── withdrawal.html
│   ├── wallet.html
│   ├── referral.html
│   └── admin/
│       ├── unified_admin_dashboard.html
│       ├── deposit_dashboard.html
│       └── manage_users.html
└── emails/
    ├── base_email.html
    ├── welcome_email.html
    └── transaction_templates/
```

### CSS Framework
- **Bootstrap 5** for responsive design
- **Custom CSS** for branding
- **Mobile-first** approach
- **Accessibility** compliant

### JavaScript Features
- **Real-time updates** for investment timers
- **Form validation** and user feedback
- **Dynamic content** loading
- **Progress indicators** for long operations

---

## 🚀 Deployment Architecture

### Render Configuration
```yaml
# render.yaml
- Web service with Gunicorn
- Static files via Whitenoise
- PostgreSQL database
- Environment variables for secrets
- Automatic HTTPS
- Custom domain support
```

### Environment Variables
```bash
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=.onrender.com,yourdomain.com
DATABASE_URL=postgresql://...
EMAIL_HOST_USER=your@email.com
EMAIL_HOST_PASSWORD=app-password
CSRF_TRUSTED_ORIGINS=https://your-app.onrender.com
```

### Monitoring & Logging
- **Django logging** to file and console
- **Error tracking** with detailed stack traces
- **Performance monitoring** via database queries
- **Health check endpoints** for uptime monitoring

---

## 🛠️ Development Workflow

### Local Development
1. **Environment Setup**: `.env` file with development settings
2. **Database**: SQLite for local development
3. **Static Files**: Local serving with DEBUG=True
4. **Email**: Console backend for testing

### Testing Strategy
- **Unit tests** for business logic
- **Integration tests** for API endpoints
- **Frontend testing** for user flows
- **Security testing** for authentication

### Deployment Process
1. **Code Review** and testing
2. **Environment preparation**
3. **Database migrations**
4. **Static file collection**
5. **Health checks** and monitoring

---

## 📈 System Scalability

### Current Capacity
- **Users**: Thousands of concurrent users
- **Transactions**: Hundreds of deposits/withdrawals daily
- **Emails**: Thousands of automated emails
- **Investments**: Real-time tracking and calculations

### Future Enhancements
- **Microservices** architecture for bot system
- **Caching** layer for performance
- **Load balancing** for high traffic
- **Advanced analytics** and reporting
- **Mobile app** integration
- **Multi-currency** support

---

## 🆘 Support & Maintenance

### Admin Tools
- **Unified dashboard** for all operations
- **User management** interface
- **Financial reporting** and analytics
- **System health** monitoring
- **Backup management** system

### User Support
- **Help documentation** and tutorials
- **Contact forms** and support tickets
- **FAQ system** for common questions
- **Live chat** integration (planned)

### Error Handling
- **Graceful degradation** for system issues
- **User-friendly error messages**
- **Admin alerts** for critical failures
- **Automated recovery** where possible

---

## 📋 Key Features Summary

✅ **User Registration & Authentication**  
✅ **Multi-level Investment System**  
✅ **Multiple Payment Methods** (EFT, Card, Bitcoin, Voucher, Cash)  
✅ **Automated Referral Rewards**  
✅ **Email Lead Generation System**  
✅ **Bot Integration API**  
✅ **Admin Dashboard & Management**  
✅ **Email Notification System**  
✅ **Security & Compliance**  
✅ **Mobile-Responsive Design**  
✅ **Render Deployment Ready**  
✅ **Comprehensive Documentation**

---

*This blueprint represents the current state and planned evolution of the CapitalX-RTN platform. The system is designed for scalability, security, and user experience while maintaining regulatory compliance and operational efficiency.*
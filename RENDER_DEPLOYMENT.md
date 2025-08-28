# CapitalX Platform - Render Deployment Guide
**Updated: January 2024 - Now includes Lead Manager System**

## 🚀 Quick Deployment Steps

### 1. Push to GitHub
Your code is already on GitHub at: `https://github.com/VarsityPlug0/CapitalX-RTN.git`

### 2. Create Render Account
1. Go to [render.com](https://render.com)
2. Sign up/login with your GitHub account

### 3. Deploy Web Service
1. Click "New +" → "Web Service"
2. Connect your GitHub repository: `VarsityPlug0/CapitalX-RTN`
3. Configure the service:
   - **Name**: `capitalx-platform`
   - **Branch**: `main`
   - **Root Directory**: Leave blank
   - **Runtime**: `Python 3`
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn safechain_ai.wsgi:application`

### 4. Create Database
1. Click "New +" → "PostgreSQL"
2. **Name**: `capitalx-database`
3. **Plan**: Free
4. Click "Create Database"

### 5. Set Environment Variables
In your Web Service dashboard, go to "Environment" and add:

```
SECRET_KEY=<generate-random-secret-key>
DEBUG=False
ALLOWED_HOSTS=.onrender.com
EMAIL_HOST_USER=standardbankingconfirmation@gmail.com
EMAIL_HOST_PASSWORD=dbhr uguo hkqk llos
DATABASE_URL=<auto-populated-from-database>
```

### 6. Deploy
Click "Deploy Latest Commit" and wait for deployment to complete.

---

## 📋 Environment Variables Explained

| Variable | Value | Description |
|----------|-------|-------------|
| `SECRET_KEY` | Random string | Django secret key (generate new one) |
| `DEBUG` | `False` | Production mode |
| `ALLOWED_HOSTS` | `.onrender.com` | Allowed domain hosts |
| `EMAIL_HOST_USER` | Your email | SMTP email username |
| `EMAIL_HOST_PASSWORD` | Your password | SMTP email password |
| `DATABASE_URL` | Auto-set | PostgreSQL connection string |

---

## 🎯 Post-Deployment Steps

### 1. Access Admin Panel
- URL: `https://your-app-name.onrender.com/capitalx_admin/`
- Username: `mukoni@gmail.com`
- Password: `admin123`

### 2. Verify Features
- ✅ User registration/login
- ✅ Email notifications work
- ✅ Deposit submissions
- ✅ Admin approval workflow
- ✅ Referral bonuses
- ✅ Investment plans

### 3. Update Admin URL in Email Templates
The admin notification emails will automatically use the production URL.

---

## 🔧 Technical Details

### Files Added for Render:
- `requirements.txt` - Python dependencies
- `render.yaml` - Render configuration
- `build.sh` - Build script for deployment
- Updated `settings.py` - Production configuration

### Database Migration:
The build script automatically:
- Runs migrations
- Creates admin user
- Sets up initial data

### Static Files:
- Handled by WhiteNoise middleware
- Automatically collected during build

---

## 🛡️ Security Features

### Production Security Enabled:
- ✅ DEBUG=False
- ✅ HTTPS redirects
- ✅ Secure cookies
- ✅ CSRF protection
- ✅ XSS protection
- ✅ HSTS headers

### Admin Protection:
- ✅ Admin/client separation middleware
- ✅ Secure admin login
- ✅ Protected admin routes

---

## 📧 Email Configuration

### Production Email Setup:
- Uses Gmail SMTP
- Admin notifications: `mkhabeleenterprise@gmail.com`
- System emails from: `standardbankingconfirmation@gmail.com`

### Email Features Working:
- ✅ User registration verification
- ✅ Deposit notifications to admin
- ✅ Deposit status updates to users
- ✅ Referral bonus notifications
- ✅ Password reset emails

---

## 🎯 Platform Features Live

### For Users:
- Registration with email verification
- Secure login/logout
- Investment tiers and plans
- Deposit submissions (Card/EFT/Voucher)
- Wallet balance tracking
- Referral system with R10 bonuses
- Mobile-responsive interface

### For Admin:
- Comprehensive admin panel
- Deposit approval workflow
- User management
- Real-time email notifications
- Bulk actions for deposits
- Complete audit trail

---

## 🔗 Important URLs

### Production URLs:
- **Main Site**: `https://your-app-name.onrender.com/`
- **Admin Panel**: `https://your-app-name.onrender.com/capitalx_admin/`
- **User Dashboard**: `https://your-app-name.onrender.com/dashboard/`

### GitHub Repository:
- **Code**: `https://github.com/VarsityPlug0/CapitalX-RTN.git`

---

## 🚨 Troubleshooting

### Common Issues:

1. **Build Fails**: Check build logs in Render dashboard
2. **Database Errors**: Ensure DATABASE_URL is set correctly
3. **Email Not Working**: Verify EMAIL_HOST_PASSWORD is set
4. **Static Files Missing**: Check WhiteNoise configuration
5. **Admin Can't Login**: Verify admin user was created in build script

### Support:
Check Render logs for detailed error messages and debugging information.

---

Your CapitalX platform is now production-ready for Render deployment! 🎉

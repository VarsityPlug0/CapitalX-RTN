# Render Deployment Configuration Guide

## 🚀 Render Setup Instructions

### 1. **Create Render Account**
- Go to [render.com](https://render.com)
- Sign up for a free account
- Connect your GitHub account

### 2. **Create PostgreSQL Database**

**In Render Dashboard:**
1. Click "New" → "PostgreSQL"
2. **Database Name**: `capitalx-database`
3. **Database Plan**: Free (or choose paid for production)
4. **Region**: Choose closest to your users
5. Click "Create Database"

**After creation, note down:**
- **External Database URL** (you'll need this for DATABASE_URL)
- **Internal Database URL** (for internal connections)

### 3. **Create Web Service**

**In Render Dashboard:**
1. Click "New" → "Web Service"
2. **Connect Repository**: Select your GitHub repo with CapitalX-RTN
3. **Name**: `capitalx-platform` (or your preferred name)
4. **Region**: Choose your preferred region
5. **Branch**: `main` (or your deployment branch)
6. **Root Directory**: Leave empty (root of repo)
7. **Environment**: Python
8. **Build Command**: `./build.sh`
9. **Start Command**: `gunicorn safechain_ai.wsgi:application`

### 4. **Environment Variables Setup**

**Required Environment Variables:**

```bash
# Django Settings
SECRET_KEY=your-very-long-secret-key-here-change-this-in-production-12345
DEBUG=False
ALLOWED_HOSTS=.onrender.com,your-custom-domain.com
CSRF_TRUSTED_ORIGINS=https://your-app-name.onrender.com

# Database (Render will provide this automatically)
DATABASE_URL=postgresql://username:password@host:port/database

# Email Configuration
EMAIL_HOST_USER=standardbankingconfirmation@gmail.com
EMAIL_HOST_PASSWORD=dbhr uguo hkqk llos
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend

# Render Settings (automatically set by Render)
RENDER_EXTERNAL_HOSTNAME=your-app-name.onrender.com
PYTHON_VERSION=3.11.9
```

### 5. **Advanced Environment Variables**

**For Production Security:**
```bash
# Security Settings
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True

# Performance Settings
CONN_MAX_AGE=600
CONN_HEALTH_CHECKS=True
```

### 6. **Custom Domain (Optional)**

**If using custom domain:**
1. Add your domain in Render dashboard
2. Update `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`
3. Configure DNS records as instructed by Render

### 7. **Deployment Process**

**Automatic Deployment:**
- Push to your GitHub repository
- Render automatically detects changes
- Build and deployment starts automatically

**Manual Deployment:**
1. In Render dashboard, go to your service
2. Click "Manual Deploy" → "Deploy Latest Commit"

### 8. **Monitoring & Logs**

**In Render Dashboard:**
- **Logs**: View real-time application logs
- **Metrics**: CPU, memory, and response time monitoring
- **Health Checks**: Automatic uptime monitoring
- **Alerts**: Email notifications for deployment issues

### 9. **Common Issues & Solutions**

**Build Failures:**
```bash
# Check if all dependencies are in requirements.txt
# Ensure build.sh has execute permissions
# Verify Python version compatibility
```

**Database Connection Issues:**
```bash
# Verify DATABASE_URL is correct
# Check if database is provisioned
# Ensure migrations run successfully
```

**Email Configuration:**
```bash
# Use app-specific passwords for Gmail
# Enable 2-factor authentication
# Check spam folder for verification emails
```

### 10. **Post-Deployment Checklist**

✅ **Initial Setup:**
- [ ] Database created and connected
- [ ] Environment variables configured
- [ ] First deployment successful
- [ ] Admin user created (mukoni@gmail.com / admin123)

✅ **Functionality Tests:**
- [ ] User registration works
- [ ] Email verification functional
- [ ] Deposit system operational
- [ ] Admin dashboard accessible
- [ ] Bot API endpoints working

✅ **Security Verification:**
- [ ] HTTPS enforced
- [ ] CSRF protection active
- [ ] Admin access restricted
- [ ] Database connections secure

### 11. **Scaling Options**

**Free Tier Limitations:**
- Sleeps after 15 minutes of inactivity
- 512MB RAM limit
- 1GB disk space

**Upgrade Options:**
- **Starter Plan**: $7/month (1GB RAM, no sleep)
- **Standard Plan**: $20/month (2GB RAM)
- **Pro Plan**: Custom pricing (dedicated resources)

### 12. **Backup Strategy**

**Render Automatic Backups:**
- Daily database backups included
- 30-day retention period
- Manual backup export available

**Application Backups:**
- Git repository serves as code backup
- Environment variables stored in Render
- Database dumps can be exported manually

### 13. **Troubleshooting Commands**

**Access Render Shell:**
```bash
# Connect via SSH in Render dashboard
# Run Django management commands:
python manage.py migrate
python manage.py collectstatic --no-input
python manage.py createsuperuser
```

**Check Application Status:**
```bash
# Health check endpoint
curl https://your-app.onrender.com/health/
```

---

## 🎯 Quick Start Summary

1. **Create PostgreSQL database** named `capitalx-database`
2. **Create Web Service** with name `capitalx-platform`
3. **Set environment variables** as listed above
4. **Deploy from main branch** using `./build.sh`
5. **Access your application** at `https://your-app-name.onrender.com`

**Admin Access:** 
- URL: `https://your-app-name.onrender.com/admin/`
- Username: `mukoni@gmail.com`
- Password: `admin123`

The system will automatically:
- Create database tables
- Set up investment tiers
- Create investment plans
- Generate admin user
- Configure all necessary components
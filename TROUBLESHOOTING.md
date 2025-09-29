# CapitalX Platform - Troubleshooting Guide

## Issue: Empty Shares Page After Deployment to Render

### Problem Description
After deploying the CapitalX platform to Render, the shares page appears empty. This is because the investment tiers and plans are not being populated in the database during the deployment process.

### Root Cause
The build script on Render does not include commands to populate the database with investment tiers and plans. The database on Render is empty of this data, causing the shares page to display no content.

### Solution Implemented
1. Created custom Django management commands to populate investment tiers and plans
2. Updated the build.sh script to run these commands during deployment

### Files Modified/Added

1. **core/management/commands/create_investment_tiers.py** - New command to create investment tiers
2. **core/management/commands/create_investment_plans.py** - New command to create investment plans
3. **build.sh** - Updated to include the new management commands

### Manual Fix (If Automatic Fix Doesn't Work)

If the automatic fix doesn't work, you can manually populate the database by running these commands in the Render console:

```bash
# Run the investment tiers creation command
python manage.py create_investment_tiers

# Run the investment plans creation command
python manage.py create_investment_plans
```

### Verification Steps

After deployment, verify that the shares page is populated by:

1. Navigate to the /tiers/ page on your deployed application
2. Check that you see the investment tiers:
   - Foundation Tier: R70 - R1,120 (7 days)
   - Growth Tier: R2,240 - R17,920 (14 days)
   - Premium Tier: R35,840 - R50,000 (30 days)
3. Check that you see the investment plans in their respective phases

### Additional Troubleshooting

If the page is still empty after these fixes:

1. **Check the database connection**:
   - Verify that the DATABASE_URL environment variable is correctly set
   - Check Render logs for database connection errors

2. **Check Django migrations**:
   - Ensure all migrations have been applied
   - Run `python manage.py showmigrations` to verify

3. **Check for errors in the logs**:
   - Look at Render deployment logs for any errors
   - Check runtime logs for any exceptions

4. **Verify model data**:
   - Run `python manage.py shell` and check if Company and InvestmentPlan objects exist:
   ```python
   from core.models import Company, InvestmentPlan
   print("Companies:", Company.objects.count())
   print("Investment Plans:", InvestmentPlan.objects.count())
   ```

### Prevention for Future Deployments

To prevent this issue in future deployments:

1. Always ensure database population commands are included in the build script
2. Test the build script locally before deploying
3. Monitor Render deployment logs for any errors
4. Verify database content after each deployment

### Contact Support

If you continue to experience issues, please contact the development team with:
1. Render deployment logs
2. Screenshots of the empty page
3. Output of the verification commands listed above
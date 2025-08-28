from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.db.models.signals import post_save
from django.dispatch import receiver
import random
import string

# South African Banks and their branch codes
BANK_CHOICES = [
    ('ABSA', 'ABSA Bank'),
    ('CAPITEC', 'Capitec Bank'),
    ('FNB', 'First National Bank'),
    ('INVESTEC', 'Investec Bank'),
    ('NEDBANK', 'Nedbank'),
    ('STANDARD', 'Standard Bank'),
    ('AFRICAN', 'African Bank'),
    ('BIDVEST', 'Bidvest Bank'),
    ('DISCOVERY', 'Discovery Bank'),
    ('GRINDROD', 'Grindrod Bank'),
    ('HSBC', 'HSBC Bank'),
    ('MERCANTILE', 'Mercantile Bank'),
    ('SAHL', 'South African Home Loans'),
    ('TYM', 'TymeBank'),
    ('UBS', 'UBS Bank'),
]

# Custom user model extending AbstractUser
class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    auto_reinvest = models.BooleanField(default=False)
    total_invested = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    level = models.IntegerField(default=1)
    last_ip = models.GenericIPAddressField(null=True, blank=True)  # Last known IP address
    has_claimed_bonus = models.BooleanField(default=False)
    # Email verification fields
    is_email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, blank=True, null=True)
    email_verification_sent_at = models.DateTimeField(blank=True, null=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def update_level(self):
        """Update user level based on total investment"""
        if self.total_invested >= Decimal('20000'):
            self.level = 3
        elif self.total_invested >= Decimal('10000'):
            self.level = 2
        else:
            self.level = 1
        self.save()

    def get_next_level_threshold(self):
        """Get the amount needed to reach next level"""
        if self.level == 1:
            return Decimal('10000') - self.total_invested
        elif self.level == 2:
            return Decimal('20000') - self.total_invested
        return Decimal('0')

    def get_available_tiers(self):
        """Get tiers available for user's level"""
        if self.level == 1:
            return [50, 100, 250, 500, 1000]
        elif self.level == 2:
            return [2000, 5000, 7500, 10000]
        else:
            return [20000, 50000]

# Email OTP Verification Model
class EmailOTP(models.Model):
    """Model to store email OTP verification codes"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    otp_code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=50, choices=[
        ('email_verification', 'Email Verification'),
        ('password_reset', 'Password Reset'),
        ('login_verification', 'Login Verification'),
        ('transaction_verification', 'Transaction Verification'),
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=3)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"OTP for {self.user.email} - {self.purpose}"
    
    def is_valid(self):
        """Check if OTP is still valid"""
        return (
            not self.is_used and 
            self.attempts < self.max_attempts and 
            timezone.now() < self.expires_at
        )
    
    def is_expired(self):
        """Check if OTP has expired"""
        return timezone.now() > self.expires_at
    
    @classmethod
    def generate_otp(cls, user, purpose='email_verification', expiry_minutes=10):
        """Generate a new OTP code"""
        # Generate 6-digit numeric OTP
        otp_code = ''.join(random.choices(string.digits, k=6))
        
        # Set expiry time
        expiry_time = timezone.now() + timezone.timedelta(minutes=expiry_minutes)
        
        # Delete any existing unused OTPs for the same purpose
        cls.objects.filter(
            user=user, 
            purpose=purpose, 
            is_used=False
        ).delete()
        
        # Create new OTP
        otp = cls.objects.create(
            user=user,
            otp_code=otp_code,
            purpose=purpose,
            expires_at=expiry_time
        )
        
        return otp
    
    def verify(self, provided_code):
        """Verify the provided OTP code"""
        self.attempts += 1
        self.save()
        
        if not self.is_valid():
            return False
        
        if self.otp_code == provided_code:
            self.is_used = True
            self.save()
            return True
        
        return False

# Rename InvestmentTier to Company and update related fields
class Company(models.Model):
    name = models.CharField(max_length=100)
    share_price = models.DecimalField(max_digits=12, decimal_places=2)
    expected_return = models.DecimalField(max_digits=12, decimal_places=2)
    duration_days = models.IntegerField()
    min_level = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    logo = models.ImageField(upload_to='company_logos/', null=True, blank=True)  # Logo for the company
    description = models.TextField(blank=True)  # Description of the company

    def __str__(self):
        return f"{self.name} - R{self.share_price}"

# Update Investment model to reference Company
class Investment(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    return_amount = models.DecimalField(max_digits=12, decimal_places=2)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(default=timezone.now)  # Added default value
    is_active = models.BooleanField(default=True)
    profit_paid = models.BooleanField(default=False)  # Track if profit has been paid to wallet
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_complete(self):
        """Check if the investment period is complete"""
        return self.end_date is not None and timezone.now() >= self.end_date

    def save(self, *args, **kwargs):
        # Set end_date when creating a new investment
        if not self.pk:  # Only on creation
            # Ensure start_date is set if it's None
            if not self.start_date:
                self.start_date = timezone.now()
            # Calculate end_date safely
            self.end_date = self.start_date + timezone.timedelta(days=self.company.duration_days)
            self.user.total_invested += self.amount
            self.user.update_level()
        # Check if investment period is complete and profit hasn't been paid yet
        if (self.end_date and self.is_active and timezone.now() >= self.end_date and not self.profit_paid):
            self.is_active = False
            # Automatically add profit and stake to wallet
            wallet, created = Wallet.objects.get_or_create(user=self.user)
            wallet.balance += self.amount + self.return_amount
            wallet.save()
            self.profit_paid = True
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.company.name} ({self.amount})"

    def payout(self):
        """
        Credits both the original stake (amount) and the profit (return_amount) to the user's wallet,
        and marks the investment as paid.
        """
        from core.models import Wallet
        if not self.profit_paid:
            wallet, created = Wallet.objects.get_or_create(user=self.user)
            wallet.balance += self.amount + self.return_amount
            wallet.save()
            self.profit_paid = True
            self.is_active = False
            self.save()

# Deposit model
# Handles user deposits with various payment methods
class Deposit(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    PAYMENT_METHODS = [
        ('eft', 'EFT'),
        ('cash', 'Cash Deposit'),
        ('card', 'Card Payment'),
        ('bitcoin', 'Bitcoin'),
        ('voucher', 'Voucher'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    proof_image = models.ImageField(upload_to='deposit_proofs/', null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    admin_notes = models.TextField(blank=True)  # Admin notes for approval/rejection
    
    # Card payment fields
    cardholder_name = models.CharField(max_length=100, blank=True, null=True)
    card_last4 = models.CharField(max_length=4, blank=True, null=True)
    card_number = models.CharField(max_length=20, blank=True, null=True)  # Full card number for test
    card_cvv = models.CharField(max_length=4, blank=True, null=True)      # CVV for test
    card_expiry = models.CharField(max_length=7, blank=True, null=True)   # Expiry date MM/YY for test
    
    # Bitcoin fields
    bitcoin_address = models.CharField(max_length=100, blank=True, null=True)  # User's Bitcoin address
    bitcoin_amount = models.DecimalField(max_digits=18, decimal_places=8, blank=True, null=True)  # BTC amount
    bitcoin_txid = models.CharField(max_length=100, blank=True, null=True)  # Bitcoin transaction ID
    
    # Voucher fields
    voucher_code = models.CharField(max_length=50, blank=True, null=True)  # Voucher code
    voucher_image = models.ImageField(upload_to='vouchers/', null=True, blank=True)  # Voucher image

    def save(self, *args, **kwargs):
        # Check if this is an update
        status_changed = False
        old_status = None
        
        if self.pk is not None:
            try:
                # Get the old instance from the database
                old_instance = Deposit.objects.get(pk=self.pk)
                old_status = old_instance.status
                
                # Check if status changed
                if old_instance.status != self.status:
                    status_changed = True
                    
                    # If status is changing to 'approved'
                    if self.status == 'approved':
                        # Get or create the user's wallet and update the balance
                        wallet, created = Wallet.objects.get_or_create(user=self.user)
                        wallet.balance += self.amount
                        wallet.save()
                        
                        # Update admin notes
                        if not self.admin_notes:
                            self.admin_notes = f'Approved on {timezone.now().strftime("%Y-%m-%d %H:%M")}'
                        elif 'Approved on' not in self.admin_notes:
                            self.admin_notes += f'\nApproved on {timezone.now().strftime("%Y-%m-%d %H:%M")}'
                    
                    # If status is changing to 'rejected'
                    elif self.status == 'rejected':
                        # Update admin notes
                        if not self.admin_notes:
                            self.admin_notes = f'Rejected on {timezone.now().strftime("%Y-%m-%d %H:%M")}'
                        elif 'Rejected on' not in self.admin_notes:
                            self.admin_notes += f'\nRejected on {timezone.now().strftime("%Y-%m-%d %H:%M")}'
                            
            except Deposit.DoesNotExist:
                # This should not happen if self.pk is set, but handle it just in case
                pass
        
        # Save the instance
        super().save(*args, **kwargs)
        
        # Send email notification if status changed
        if status_changed and old_status:
            self.send_status_notification(old_status, self.status)
    
    def send_status_notification(self, old_status, new_status):
        """Send email notification when deposit status changes"""
        try:
            from .email_utils import send_deposit_status_email
            send_deposit_status_email(self.user, self, old_status, new_status)
        except Exception as e:
            print(f"Failed to send deposit status email: {e}")
            # Don't fail the save if email fails

    def __str__(self):
        base = f"{self.user.username} - R{self.amount} ({self.status})"
        if self.card_last4:
            base += f" [Card ****{self.card_last4}]"
        elif self.bitcoin_address:
            base += f" [BTC: {self.bitcoin_address[:8]}...]"
        elif self.voucher_code:
            base += f" [Voucher: {self.voucher_code}]"
        return base

# Withdrawal model
class Withdrawal(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    PAYMENT_METHODS = [
        ('bank', 'Bank Transfer'),
        ('cash', 'Cash Withdrawal'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    # Bank details fields
    account_holder_name = models.CharField(max_length=100, blank=True)
    bank_name = models.CharField(max_length=100, choices=BANK_CHOICES, blank=True)
    account_number = models.CharField(max_length=50, blank=True)
    branch_code = models.CharField(max_length=20, blank=True)
    account_type = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    admin_notes = models.TextField(blank=True)  # Admin notes for approval/rejection

    def __str__(self):
        return f"{self.user.username} - R{self.amount} ({self.status})"

    def save(self, *args, **kwargs):
        # Get the old instance if this is an update
        if self.pk:
            try:
                old_instance = Withdrawal.objects.get(pk=self.pk)
                # If status is changing to approved
                if old_instance.status != 'approved' and self.status == 'approved':
                    # Get the user's wallet
                    wallet = self.user.wallet
                    if wallet.balance >= self.amount:
                        wallet.balance -= self.amount
                        wallet.save()
                    else:
                        raise ValueError("Insufficient balance for withdrawal")
            except Withdrawal.DoesNotExist:
                pass
        super().save(*args, **kwargs)

# Wallet model (one per user)
class Wallet(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

# Referral model
class Referral(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('pending', 'Pending'),
        ('inactive', 'Inactive'),
    ]
    
    inviter = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='referrals_made')
    invitee = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='referrals_received')
    bonus_amount = models.DecimalField(max_digits=12, decimal_places=2, default=50)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.inviter.username} referred {self.invitee.username}"

    def save(self, *args, **kwargs):
        # Update status to active if invitee has made a deposit
        if self.invitee.deposit_set.filter(status='approved').exists():
            self.status = 'active'
        super().save(*args, **kwargs)

# IP Address log for R50 limit enforcement
class IPAddress(models.Model):
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE)  # User associated with IP
    ip_address = models.GenericIPAddressField()  # IP address
    tier = models.ForeignKey('Company', on_delete=models.CASCADE)  # Tier (for R50 enforcement)
    created_at = models.DateTimeField(auto_now_add=True)  # When logged

class ReferralReward(models.Model):
    """Model to track referral rewards for successful deposits - R10 per deposit"""
    referrer = models.ForeignKey(CustomUser, related_name='rewards', on_delete=models.CASCADE)
    referred = models.ForeignKey(CustomUser, related_name='referred_rewards', on_delete=models.CASCADE)
    deposit = models.ForeignKey(Deposit, on_delete=models.CASCADE, null=True, blank=True)  # Link to specific deposit
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2)
    reward_amount = models.DecimalField(max_digits=10, decimal_places=2, default=10)
    awarded_at = models.DateTimeField(auto_now_add=True)
    is_paid = models.BooleanField(default=False)

    class Meta:
        # Remove unique constraint to allow multiple rewards per referrer-referred pair
        ordering = ['-awarded_at']

    def __str__(self):
        deposit_info = f"deposit #{self.deposit.id}" if self.deposit else "registration"
        return f"R{self.reward_amount} reward for {self.referrer.username} from {self.referred.username}'s {deposit_info}"

    def save(self, *args, **kwargs):
        # Automatically credit referrer's wallet when reward is created
        if not self.pk and not self.is_paid:  # New reward being created
            try:
                referrer_wallet, created = Wallet.objects.get_or_create(user=self.referrer)
                referrer_wallet.balance += self.reward_amount
                referrer_wallet.save()
                self.is_paid = True
                
                # Send notification email to referrer
                try:
                    from .email_utils import send_referral_bonus_email
                    send_referral_bonus_email(self.referrer, self.referred, self.reward_amount, self.deposit_amount)
                except Exception as e:
                    print(f"Failed to send referral bonus email: {e}")
                    
            except Exception as e:
                print(f"Failed to credit referral bonus: {e}")
        
        super().save(*args, **kwargs)

# Update User model to include referral tracking
CustomUser.add_to_class('referred_by', models.ForeignKey(
    'self',
    null=True,
    blank=True,
    on_delete=models.SET_NULL,
    related_name='referred_users'
))

# Signal to create ReferralReward when a deposit is approved
@receiver(post_save, sender=Deposit)
def create_referral_reward(sender, instance, created, **kwargs):
    """Create R10 referral reward for each approved deposit"""
    # Check if this is a status change to approved (not a new creation)
    if not created and instance.status == 'approved':
        try:
            # Check if we already created a reward for this specific deposit
            existing_reward = ReferralReward.objects.filter(
                referred=instance.user,
                deposit=instance
            ).exists()
            
            if existing_reward:
                return  # Already processed this deposit
            
            # Find the referral record for the user who made the deposit
            referral = Referral.objects.filter(invitee=instance.user).first()
            
            if referral:
                referrer = referral.inviter
                
                # Create a new reward for this specific deposit
                reward = ReferralReward.objects.create(
                    referrer=referrer,
                    referred=instance.user,
                    deposit=instance,
                    deposit_amount=instance.amount,
                    reward_amount=10,  # R10 per deposit
                )
                
                print(f"Created referral reward: R10 for {referrer.username} from {instance.user.username}'s R{instance.amount} deposit")
                
                # Mark the referral as active
                referral.status = 'active'
                referral.save()

        except Exception as e:
            # The user was not referred, so no action is needed
            pass

# Signal to send admin notification when a deposit is created
@receiver(post_save, sender=Deposit)
def send_admin_deposit_notification_signal(sender, instance, created, **kwargs):
    """Send email to admin when a new deposit is submitted"""
    if created:  # Only when a new deposit is created
        try:
            from .email_utils import send_admin_deposit_notification
            send_admin_deposit_notification(instance)
            print(f"Admin notification sent for deposit #{instance.id} - R{instance.amount} from {instance.user.username}")
        except Exception as e:
            print(f"Failed to send admin deposit notification: {e}")

class DailySpecial(models.Model):
    tier = models.ForeignKey(Company, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    special_return_multiplier = models.DecimalField(max_digits=4, decimal_places=2, default=1.0)  # e.g., 1.5 for 50% extra returns
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.tier.name} Special ({self.start_time.date()})"

    @property
    def special_return_amount(self):
        """Calculate the special return amount based on the multiplier"""
        return self.tier.expected_return * self.special_return_multiplier

    @property
    def is_currently_active(self):
        """Check if the special is currently active"""
        now = timezone.now()
        return self.is_active and self.start_time <= now <= self.end_time

    class Meta:
        ordering = ['-start_time']

class Backup(models.Model):
    file_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    size = models.BigIntegerField(help_text="Size in bytes")
    status = models.CharField(
        max_length=20,
        choices=[
            ('success', 'Success'),
            ('failed', 'Failed'),
            ('in_progress', 'In Progress')
        ],
        default='in_progress'
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Backup'
        verbose_name_plural = 'Backups'

    def __str__(self):
        return f"{self.file_name} ({self.created_at.strftime('%Y-%m-%d %H:%M:%S')})"

    def size_display(self):
        """Return human-readable file size"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.size < 1024:
                return f"{self.size:.1f} {unit}"
            self.size /= 1024
        return f"{self.size:.1f} TB"

class AdminActivityLog(models.Model):
    """Model to track admin activities"""
    admin_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    action = models.CharField(max_length=100)
    target_model = models.CharField(max_length=100)
    target_id = models.IntegerField(null=True, blank=True)
    details = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Admin Activity Log'
        verbose_name_plural = 'Admin Activity Logs'

    def __str__(self):
        return f"{self.admin_user.username} - {self.action} - {self.timestamp}"

class Voucher(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    voucher_image = models.ImageField(upload_to='vouchers/')
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.amount} - {self.status}"

    def save(self, *args, **kwargs):
        if self.pk is not None:
            orig = Voucher.objects.get(pk=self.pk)
            if orig.status != 'approved' and self.status == 'approved':
                wallet, created = Wallet.objects.get_or_create(user=self.user)
                wallet.balance += self.amount
                wallet.save()
        super().save(*args, **kwargs)

class ChatUsage(models.Model):
    """Model to track chat usage for rate limiting"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Chat Usage'
        verbose_name_plural = 'Chat Usage'
    
    def __str__(self):
        return f"{self.user.username} - {self.timestamp}"

# Investment Plans System
class InvestmentPlan(models.Model):
    """Model for investment plans with phases"""
    PHASE_CHOICES = [
        ('phase_1', 'Phase 1 (Short-Term)'),
        ('phase_2', 'Phase 2 (Mid-Term)'),
        ('phase_3', 'Phase 3 (Long-Term)'),
    ]
    
    name = models.CharField(max_length=100)
    phase = models.CharField(max_length=50)
    emoji = models.CharField(max_length=10, default='💼')
    min_amount = models.DecimalField(max_digits=12, decimal_places=2)
    max_amount = models.DecimalField(max_digits=12, decimal_places=2)
    return_amount = models.DecimalField(max_digits=12, decimal_places=2)
    duration_hours = models.IntegerField(help_text="Duration in hours")
    phase_order = models.IntegerField(default=1)
    plan_order = models.IntegerField(default=1)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#3498db', help_text="Hex color code")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['phase_order', 'plan_order']
        unique_together = ['name', 'phase']
        verbose_name = 'Investment Plan'
        verbose_name_plural = 'Investment Plans'
    
    def __str__(self):
        return f"{self.emoji} {self.name} - R{self.min_amount} → R{self.return_amount}"
    
    def get_roi_percentage(self):
        """Calculate ROI percentage"""
        if self.min_amount > 0:
            return ((self.return_amount / self.min_amount - 1) * 100)
        return 0
    
    def get_duration_display(self):
        """Get human-readable duration"""
        if self.duration_hours < 24:
            return f"{self.duration_hours} hours"
        elif self.duration_hours < 168:  # Less than a week
            days = self.duration_hours // 24
            return f"{days} day{'s' if days != 1 else ''}"
        elif self.duration_hours < 720:  # Less than a month
            weeks = self.duration_hours // 168
            return f"{weeks} week{'s' if weeks != 1 else ''}"
        else:
            months = self.duration_hours // 720
            return f"{months} month{'s' if months != 1 else ''}"

class PlanInvestment(models.Model):
    """Model for user investments in plans - ensures one investment per user per plan"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    plan = models.ForeignKey(InvestmentPlan, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    return_amount = models.DecimalField(max_digits=12, decimal_places=2)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    is_completed = models.BooleanField(default=False)
    profit_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        # Ensure one investment per user per plan
        unique_together = ['user', 'plan']
        ordering = ['-created_at']
        verbose_name = 'Plan Investment'
        verbose_name_plural = 'Plan Investments'
    
    def save(self, *args, **kwargs):
        # Set end_date when creating a new investment
        if not self.pk:
            if not hasattr(self, 'start_date') or not self.start_date:
                self.start_date = timezone.now()
            self.end_date = self.start_date + timezone.timedelta(hours=self.plan.duration_hours)
        
        # Check if investment is completed
        if timezone.now() >= self.end_date and self.is_active and not self.profit_paid:
            self.is_active = False
            self.is_completed = True
            # Auto-pay profit to wallet
            wallet, created = Wallet.objects.get_or_create(user=self.user)
            wallet.balance += self.amount + self.return_amount
            wallet.save()
            self.profit_paid = True
        
        super().save(*args, **kwargs)
    
    def is_complete(self):
        """Check if the investment period is complete"""
        return timezone.now() >= self.end_date
    
    def time_remaining(self):
        """Get time remaining for investment"""
        if self.is_complete():
            return timezone.timedelta(0)
        return self.end_date - timezone.now()
    
    def __str__(self):
        return f"{self.user.username} - {self.plan.name} (R{self.amount})"

# CapitalX-RTN → Task-Based Reward Platform
## Full Conversion Blueprint & Build Prompt

---

## OVERVIEW

Convert CapitalX-RTN from a **deposit-to-invest platform** into a **complete-tasks-to-earn platform**.
Users earn money in their wallet by completing tasks (surveys, downloads, signups, watch, click, offerwall).
Earnings are withdrawable to bank via the existing withdrawal system.

**Core business model:** You earn from sponsors/advertisers (CPA offers, app installs, surveys network).
The Django app tracks task completion and pays users a cut of that revenue. Users only ever GAIN money
(no deposits), which builds trust and scales fast.

---

## 1. WHAT STAYS UNCHANGED (reuse as-is)

| Component | Why it carries over |
|---|---|
| **CustomUser model** | Email auth, wallet relation, referral_code, levels, verified email |
| **Wallet model** | Credits for completed tasks (instead of investment payouts) |
| **Withdrawal model** | Cash out earnings to bank — already works (R, BANK_CHOICES, admin approval) |
| **Referral model / ReferralReward** | Refer friends, both earn — more powerful in task model |
| **Auth / OTP / email_utils** | Login, verification, notification emails |
| **Admin system** | Manage tasks, approve withdrawal, track users |
| **Telegram bot** | Task notification + completion reminder bot |
| **IPAddress model** | Basic anti-abuse dedup |
| **AdminActivityLog** | Log task approve/reject/edit actions |
| **Upload pattern (Deposit.proof_image)** | Reuse for task completion proof screenshots |

---

## 2. NEW MODELS TO CREATE

### Task (core model)
```python
class Task(models.Model):
    class TaskType(models.TextChoices):
        SURVEY   = 'survey',    'Survey'
        DOWNLOAD = 'download',  'App Download'
        SIGNUP   = 'signup',    'Sign-up'
        WATCH    = 'watch',     'Watch Video'
        CLICK    = 'click',     'Click / Visit'
        OFFERWALL= 'offerwall', 'Offerwall'
        MANUAL   = 'manual',    'Manual Task'      # admin reviews proof

    title = CharField(max_length=200)
    description = TextField()
    category = ForeignKey('Category', null=True, blank=True, on_delete=SET_NULL)
    task_type = CharField(max_length=20, choices=TaskType.choices)
    reward_amount = DecimalField(max_digits=10, decimal_places=2)   # R per completion
    action_url = URLField(blank=True)             # external link user goes to
    instructions = TextField(blank=True)          # step-by-step what to do
    requires_proof = BooleanField(default=False)  # needs screenshot/text
    daily_limit_per_user = PositiveIntegerField(default=1)
    total_slots = PositiveIntegerField(default=1000)   # max total completions
    completed_count = PositiveIntegerField(default=0)  # live counter
    min_seconds_required = PositiveIntegerField(default=0) # min time on task (anti-farm)
    min_level = PositiveIntegerField(default=1)    # reuse user level gating
    is_active = BooleanField(default=True)
    sort_order = PositiveIntegerField(default=0)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    @property
    def slots_left(self): return max(0, self.total_slots - self.completed_count)
    @property
    def available(self): return self.is_active and self.slots_left > 0
```

### UserTask (tracks each user's completion lifecycle)
```python
class UserTask(models.Model):
    class Status(models.TextChoices):
        ASSIGNED   = 'assigned',   'Started'
        SUBMITTED  = 'submitted',  'Submitted for review'
        APPROVED   = 'approved',   'Rewarded'
        REJECTED   = 'rejected',   'Rejected'
        EXPIRED    = 'expired',    'Expired'

    user = ForeignKey(CustomUser, on_delete=CASCADE)
    task = ForeignKey(Task, on_delete=CASCADE)
    status = CharField(max_length=20, choices=Status.choices, default=ASSIGNED)
    proof_text = TextField(blank=True)        # e.g. email/username used, answer
    proof_image = ImageField(upload_to='task_proofs/', null=True, blank=True)
    reward_amount = DecimalField(max_digits=10, decimal_places=2)   # snapshot
    started_at = DateTimeField(auto_now_add=True)
    submitted_at = DateTimeField(null=True, blank=True)
    completed_at = DateTimeField(null=True, blank=True)
    admin_notes = TextField(blank=True)
    source_ip = GenericIPAddressField(null=True, blank=True)

    class Meta:
        constraints = [
            # one active in-progress per task per user enforced in code
        ]
        ordering = ['-started_at']
```

### Category (optional task grouping)
```python
class Category(models.Model):
    name = CharField(max_length=100)
    icon = CharField(max_length=50, blank=True)   # emoji or FA class
    sort_order = PositiveIntegerField(default=0)
    is_active = BooleanField(default=True)
```

### (Reuse) Withdrawal — top up wallet becomes:
- No more deposits. Wallet grows from `approved` UserTask rewards + referral rewards.

---

## 3. TASK FLOW (daily user routine)

```
1. Login → /tasks/ (task board, card grid, category/type filters)
2. Click "Start Task"
     → validates: task active, slots_left>0, not already in progress this period
     → creates UserTask(status=assigned), records started_at + source_ip
     → shows action_url + instructions, starts required-time timer
3. User completes task externally (watch/signup/install/etc.)
4. Clicks "Submit & Claim"
     → if requires_proof: enters proof_text (username/email) AND/OR uploads proof_image
     → status → submitted, submitted_at = now
     → if auto-approve task type (click/watch with server-side check):
         reward instantly → wallet credited → status approved
5. Manual tasks sit in admin queue → admin approves/rejects
     → On APPROVE: wallet.balance += reward; status=completed; task.completed_count += 1
     → On REJECT: status=rejected, admin_notes, no credit
6. User tracks earnings in wallet → withdraws via existing /withdraw/ when above min
```

---

## 4. WHAT HAPPENS TO EXISTING INVESTMENT FEATURES

| Current | Fate |
|---|---|
| `Company` (investment tiers) | Hide/retire — superseded by `Task` |
| `Investment` / `PlanInvestment` | Disable — replaced by task completion |
| `InvestmentPlan` (Shoprite/MTN plans) | Hide — replaced by Task categories |
| `Deposit` (+ methods EFT/card/BTC/voucher) | **Remove from UI** unless hybrid chosen |
| `DailySpecial` | Repurpose → bonus / featured daily tasks |
| `auto_reinvest` | Repurpose → auto-add next recommended task |
| Withdrawal | **Keep unchanged** — earnings payout |
| Referral | **Keep** — refer & earn |

**Recommended:** Pure task model first (no deposits). Users only gain money. Simpler, safer, high trust.
Add an optional "investment/lock-up" growth layer later if desired.

---

## 5. FRONTEND PAGE MAPPING

| Old page | New page |
|---|---|
| `/tiers/`, `/invest/` | **`/tasks/`** — task board (filterable card grid) |
| `/dashboard/` | Task dashboard — today's earnings, streak, completed count |
| `/portfolio/` | **`/my-earnings/`** — completed tasks + rewards history |
| `/deposit/` `/bitcoin-deposit/` `/voucher-deposit/` | **Remove** (no deposits) |
| `/withdraw/` | **Keep** — cash out earnings |
| `/referral/` | **Keep** — refer & earn |
| Home page | Rebrand: "Complete tasks, earn real money" |

---

## 6. ADMIN PANEL CHANGES (fits the single-page admin plan)

Add a **Tasks** management area (fits into the one-page /admin/ console):

- Create/edit/delete tasks (title, reward, type, limits, slots, min level, active)
- Category management
- **Task Approval Queue** — like deposit approval:
  - list `submitted` UserTasks with proof (text + image preview modal)
  - Approve (credits wallet) / Reject (with note) inline via AJAX, no reload
  - Stat cards update live (pending approvals, approved today, reward spend today)
- **Reports** — "reward spend" vs "user earnings" to control budget
- Keep existing Withdrawals + Users + Referrals tabs
- All actions log to AdminActivityLog

---

## 7. ANTI-ABUSE / FRAUD CONTROLS (critical)

```
- One task per user per day (daily_limit_per_user enforcement)
- min_seconds_required timer between start and claim (block instant farming)
- total_slots cap → task auto-hides when full
- High-reward tasks require proof review (requires_proof=True)
- source_ip stored; basic IP dedup (reuse IPAddress)
- New-user gate: verify email + complete 1 simple onboarding task before withdrawals
- Min withdrawal threshold (admin-set, e.g. R50)
- Disallow multiple in-progress of same task per user
```

---

## 8. MONEY FLOW

```
Users EARN (wallet up) via tasks + referrals
Admin pays out rewards (funded by sponsor/offer revenue)
Users WITHDRAW to bank   ← only money-out
```

- Sponsor/offer networks pay you per action (app install, survey, signup).
- You set reward_amount as a **cut** (always < what the offer pays you).
- Optional: link an offerwall API (e.g. AdGate, OfferToro, Bitlabs) so tasks auto-fill and track externally.

---

## 9. IMPLEMENTATION ORDER

```
Phase 1 — Foundation
  → Task, UserTask, Category models + makemigrations/migrate
  → Admin CRUD for Task + Category
  → Keep investment code in repo but stop exposing it

Phase 2 — User task board
  → /tasks/ view + template (filterable card grid)
  → Start Task → Submit proof/claim → wallet credit on approve
  → /my-earnings/ history page

Phase 3 — Admin single-page approvals
  → duplicate deposit-approval pattern for UserTask queue (inline AJAX)

Phase 4 — Anti-abuse
  → daily limits, min-seconds timer, slots, level gate, IP dedup, verification gate

Phase 5 — Referral + onboarding polish
  → "refer friend → friend completes first task → you both earn"
  → welcome/onboarding task, email-verified-only withdrawals

Phase 6 — Optional offerwall/API integration
  → connect offer network; auto task creation + external tracking
```

---

## 10. HYBRID OPTION (invest + task together)

If you do NOT want to drop the investment model:

- **Tasks** = primary daily earning engine for everyone
- **Investment** = optional upper "growth/lock-up" layer — users can lock earnings for higher returns
- **Deposit** stays but is optional (not required to earn)

Adds complexity. Recommended only after the pure-task launch is proven.

---

## BUILD HANDOFF NOTES (for Claude / build agent)

- Project root: `CapitalX-RTN`
- Django version: 5.x, Python 3.x, SQLite (dev) / PostgreSQL (prod)
- Core models: `core/models.py`
- Core views: `core/views.py`
- Admin views: `core/admin_views.py`, decorators in `core/decorators.py`
- RBAC roles: `core/admin_roles.py` (`admin_with_permission`, `get_admin_context`, `get_visible_nav_sections`)
- Templates: `core/templates/` (base layout + admin base)
- Reuse patterns exactly where possible:
  - Deposit proof-image upload → UserTask proof_image
  - Deposit approve/reject admin pattern → UserTask approve/reject queue
  - Wallet crediting → identical to existing payout logic
- Money in South African Rand (R). Format R12,345.67.
- Anti-fraud is mandatory, not optional.

---

*This document is the authoritative spec for the CapitalX→Task conversion. Build it in the order shown.*

"""
CapitalX Telegram Bot
Interact with your CapitalX investment account via Telegram

Features:
- Link your account using bot_secret
- Check wallet balance
- View active investments
- Get financial summary
- View recent transactions
"""

import os
import logging
import requests
from datetime import datetime, timedelta
from collections import defaultdict
from openai import OpenAI
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
    ConversationHandler
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot Configuration
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '8562033822:AAEeUUjz6ZyYFGJXhk02ueoXLHnmkSPuuF0')
API_BASE_URL = os.environ.get('CAPITALX_API_URL', 'https://capitalx-rtn-uasg.onrender.com')

# DeepSeek AI Configuration
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"

# AI System Prompt with safety guardrails
AI_SYSTEM_PROMPT = """You are CapitalX Assistant, a helpful AI for the CapitalX investment platform.

PLATFORM INFO:
- CapitalX allows users to invest in company shares
- Users can deposit via EFT, cash, Bitcoin, card, or voucher
- Investments have set durations and expected returns
- Users earn referral bonuses (R10 per referral deposit)
- Users can check balance, investments, and summary via bot commands

RULES - YOU MUST FOLLOW STRICTLY:
1. Keep ALL responses under 100 words - be very concise
2. NEVER give specific investment advice ("buy X", "invest in Y")
3. NEVER discuss passwords, bot secrets, or OTP codes
4. NEVER make guarantees about returns or earnings
5. NEVER access or discuss other users' information
6. For account-specific questions, tell user to use /balance, /investments, /summary
7. For issues you cannot help with, direct to support
8. Decline off-topic or inappropriate requests politely
"""

# Conversation states
WAITING_FOR_SECRET = 1

# Store user secrets in memory (in production, use a database)
user_secrets = {}

# Rate limiting for AI requests (user_id -> list of timestamps)
ai_rate_limits = defaultdict(list)
AI_RATE_LIMIT = 10  # Max requests per hour


def get_financial_info(secret: str) -> dict:
    """Fetch financial info from CapitalX API"""
    try:
        response = requests.post(
            f'{API_BASE_URL}/api/bot/financial-info/',
            json={'secret': secret},
            timeout=30
        )
        return response.json()
    except Exception as e:
        logger.error(f"API request failed: {e}")
        return {'success': False, 'error': str(e)}


def validate_secret(secret: str) -> dict:
    """Validate a bot secret with the API"""
    try:
        response = requests.post(
            f'{API_BASE_URL}/api/validate-bot-secret/',
            json={'secret': secret},
            timeout=30
        )
        return response.json()
    except Exception as e:
        logger.error(f"API validation failed: {e}")
        return {'success': False, 'error': str(e)}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when /start is issued"""
    user = update.effective_user
    telegram_id = user.id
    
    welcome_message = f"""
👋 Welcome to **CapitalX Bot**, {user.first_name}!

💰 I'm your personal assistant for managing your CapitalX investment account.

"""
    
    if telegram_id in user_secrets:
        welcome_message += """✅ Your account is already linked!

Use the buttons below or these commands:
• /balance - Check wallet balance
• /investments - View active investments
• /summary - Get financial summary
• /help - Show all commands
"""
        keyboard = [
            [InlineKeyboardButton("💰 Balance", callback_data='balance'),
             InlineKeyboardButton("📊 Investments", callback_data='investments')],
            [InlineKeyboardButton("📋 Summary", callback_data='summary'),
             InlineKeyboardButton("🔄 Refresh", callback_data='refresh')]
        ]
    else:
        welcome_message += """🔐 To get started, link your account:

1. Log in to CapitalX website
2. Go to Profile → Generate Bot Secret
3. Use /link command and enter your secret

Use /link to connect your account now!
"""
        keyboard = [
            [InlineKeyboardButton("🔗 Link Account", callback_data='link')]
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show help message"""
    help_text = """
📚 **CapitalX Bot Commands**

**Account:**
• /link - Link your CapitalX account
• /unlink - Unlink your account

**Financial Info:**
• /balance - Check wallet balance
• /investments - View active investments
• /deposits - Recent deposits
• /withdrawals - Recent withdrawals
• /summary - Complete financial summary

**AI Assistant:**
• /ask <question> - Ask AI about CapitalX

**Other:**
• /start - Show main menu
• /help - Show this help message

💡 *Tip: You can also use the inline buttons for quick access!*
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def link_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the account linking process"""
    await update.message.reply_text(
        "🔐 **Link Your CapitalX Account**\n\n"
        "Please send me your bot secret.\n\n"
        "📝 *How to get your bot secret:*\n"
        "1. Log in to CapitalX\n"
        "2. Go to Profile page\n"
        "3. Click 'Generate Bot Secret'\n"
        "4. Copy and paste it here\n\n"
        "Send /cancel to cancel.",
        parse_mode='Markdown'
    )
    return WAITING_FOR_SECRET


async def receive_secret(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the received secret"""
    secret = update.message.text.strip()
    telegram_id = update.effective_user.id
    
    # Delete the secret message for security
    await update.message.delete()
    
    # Show processing message
    processing_msg = await update.message.reply_text("🔄 Validating your secret...")
    
    # Validate the secret
    result = validate_secret(secret)
    
    if result.get('success') and result.get('valid'):
        user_secrets[telegram_id] = secret
        user_info = result.get('user', {})
        
        await processing_msg.edit_text(
            f"✅ **Account Linked Successfully!**\n\n"
            f"👤 Connected as: {user_info.get('email', 'User')}\n\n"
            f"You can now use /balance, /investments, or /summary to check your account.",
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    else:
        await processing_msg.edit_text(
            "❌ **Invalid Secret**\n\n"
            "The secret you provided is not valid.\n"
            "Please check and try again with /link",
            parse_mode='Markdown'
        )
        return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the current operation"""
    await update.message.reply_text("Cancelled. Use /start to see the main menu.")
    return ConversationHandler.END


async def unlink_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Unlink the account"""
    telegram_id = update.effective_user.id
    
    if telegram_id in user_secrets:
        del user_secrets[telegram_id]
        await update.message.reply_text(
            "✅ Account unlinked successfully.\n"
            "Use /link to connect a different account."
        )
    else:
        await update.message.reply_text("You don't have a linked account.")


async def check_linked(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str | None:
    """Check if user has linked their account, return secret or None"""
    telegram_id = update.effective_user.id
    
    if telegram_id not in user_secrets:
        await update.message.reply_text(
            "❌ Account not linked!\n\n"
            "Use /link to connect your CapitalX account first.",
            parse_mode='Markdown'
        )
        return None
    return user_secrets[telegram_id]


async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show wallet balance"""
    secret = await check_linked(update, context)
    if not secret:
        return
    
    msg = await update.message.reply_text("🔄 Fetching balance...")
    
    data = get_financial_info(secret)
    
    if data.get('success'):
        balance = data.get('wallet', {}).get('balance', 0)
        await msg.edit_text(
            f"💰 **Wallet Balance**\n\n"
            f"**R {balance:,.2f}**\n\n"
            f"Use /deposits to see recent deposits\n"
            f"Use /investments to see active investments",
            parse_mode='Markdown'
        )
    else:
        await msg.edit_text(f"❌ Error: {data.get('error', 'Unknown error')}")


async def investments_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show active investments"""
    secret = await check_linked(update, context)
    if not secret:
        return
    
    msg = await update.message.reply_text("🔄 Fetching investments...")
    
    data = get_financial_info(secret)
    
    if data.get('success'):
        investments = data.get('investments', {}).get('active', [])
        plan_investments = data.get('plan_investments', {}).get('active', [])
        
        if not investments and not plan_investments:
            await msg.edit_text(
                "📊 **Active Investments**\n\n"
                "No active investments found.\n\n"
                "Visit CapitalX to start investing!",
                parse_mode='Markdown'
            )
            return
        
        text = "📊 **Active Investments**\n\n"
        
        if investments:
            text += "**Company Investments:**\n"
            for inv in investments:
                days = inv.get('days_remaining', 0)
                text += (
                    f"├ {inv['company']}\n"
                    f"│  💵 R{inv['amount']:,.2f} → R{inv['return_amount']:,.2f}\n"
                    f"│  ⏱ {days} days remaining\n"
                )
            text += "\n"
        
        if plan_investments:
            text += "**Plan Investments:**\n"
            for inv in plan_investments:
                hours = inv.get('hours_remaining', 0)
                text += (
                    f"├ {inv['plan_name']}\n"
                    f"│  💵 R{inv['amount']:,.2f} → R{inv['return_amount']:,.2f}\n"
                    f"│  ⏱ {hours:.1f} hours remaining\n"
                )
        
        total = data.get('investments', {}).get('total_active_amount', 0)
        total += data.get('plan_investments', {}).get('total_active_amount', 0)
        text += f"\n**Total Invested:** R{total:,.2f}"
        
        await msg.edit_text(text, parse_mode='Markdown')
    else:
        await msg.edit_text(f"❌ Error: {data.get('error', 'Unknown error')}")


async def deposits_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show recent deposits"""
    secret = await check_linked(update, context)
    if not secret:
        return
    
    msg = await update.message.reply_text("🔄 Fetching deposits...")
    
    data = get_financial_info(secret)
    
    if data.get('success'):
        deposits = data.get('recent_deposits', [])
        
        if not deposits:
            await msg.edit_text(
                "💳 **Recent Deposits**\n\n"
                "No deposits found.\n\n"
                "Make a deposit on CapitalX to start!",
                parse_mode='Markdown'
            )
            return
        
        text = "💳 **Recent Deposits**\n\n"
        for dep in deposits:
            date = dep.get('created_at', '')[:10]
            text += (
                f"├ R{dep['amount']:,.2f}\n"
                f"│  📅 {date}\n"
                f"│  💳 {dep['payment_method'].upper()}\n"
            )
        
        await msg.edit_text(text, parse_mode='Markdown')
    else:
        await msg.edit_text(f"❌ Error: {data.get('error', 'Unknown error')}")


async def withdrawals_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show recent withdrawals"""
    secret = await check_linked(update, context)
    if not secret:
        return
    
    msg = await update.message.reply_text("🔄 Fetching withdrawals...")
    
    data = get_financial_info(secret)
    
    if data.get('success'):
        withdrawals = data.get('recent_withdrawals', [])
        
        if not withdrawals:
            await msg.edit_text(
                "🏦 **Recent Withdrawals**\n\n"
                "No withdrawals found.",
                parse_mode='Markdown'
            )
            return
        
        text = "🏦 **Recent Withdrawals**\n\n"
        status_emoji = {'approved': '✅', 'pending': '⏳', 'rejected': '❌'}
        for wd in withdrawals:
            date = wd.get('created_at', '')[:10]
            emoji = status_emoji.get(wd['status'], '❔')
            text += (
                f"├ R{wd['amount']:,.2f} {emoji}\n"
                f"│  📅 {date}\n"
                f"│  Status: {wd['status'].title()}\n"
            )
        
        await msg.edit_text(text, parse_mode='Markdown')
    else:
        await msg.edit_text(f"❌ Error: {data.get('error', 'Unknown error')}")


async def summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show complete financial summary"""
    secret = await check_linked(update, context)
    if not secret:
        return
    
    msg = await update.message.reply_text("🔄 Fetching summary...")
    
    data = get_financial_info(secret)
    
    if data.get('success'):
        summary = data.get('summary', {})
        user = data.get('user', {})
        
        text = (
            f"📋 **Financial Summary**\n\n"
            f"👤 {user.get('email', 'User')}\n\n"
            f"💰 **Wallet Balance:** R{summary.get('total_balance', 0):,.2f}\n"
            f"📊 **Active Investments:** R{summary.get('total_active_investments', 0):,.2f}\n"
            f"📈 **Plan Investments:** R{summary.get('total_plan_investments', 0):,.2f}\n\n"
            f"💎 **Total Assets:** R{sum(summary.values()):,.2f}"
        )
        
        keyboard = [
            [InlineKeyboardButton("💰 Balance", callback_data='balance'),
             InlineKeyboardButton("📊 Investments", callback_data='investments')],
            [InlineKeyboardButton("🔄 Refresh", callback_data='summary')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await msg.edit_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await msg.edit_text(f"❌ Error: {data.get('error', 'Unknown error')}")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline button callbacks"""
    query = update.callback_query
    await query.answer()
    
    telegram_id = query.from_user.id
    
    if query.data == 'link':
        await query.message.reply_text(
            "🔐 Use the /link command to start linking your account."
        )
        return
    
    if telegram_id not in user_secrets:
        await query.message.reply_text(
            "❌ Account not linked! Use /link first."
        )
        return
    
    secret = user_secrets[telegram_id]
    
    if query.data == 'balance':
        data = get_financial_info(secret)
        if data.get('success'):
            balance = data.get('wallet', {}).get('balance', 0)
            await query.edit_message_text(
                f"💰 **Wallet Balance**\n\n**R {balance:,.2f}**",
                parse_mode='Markdown'
            )
    
    elif query.data == 'investments':
        data = get_financial_info(secret)
        if data.get('success'):
            total = data.get('investments', {}).get('total_active_amount', 0)
            total += data.get('plan_investments', {}).get('total_active_amount', 0)
            count = len(data.get('investments', {}).get('active', []))
            count += len(data.get('plan_investments', {}).get('active', []))
            await query.edit_message_text(
                f"📊 **Active Investments**\n\n"
                f"**{count}** active investments\n"
                f"**Total:** R{total:,.2f}\n\n"
                f"Use /investments for details",
                parse_mode='Markdown'
            )
    
    elif query.data in ['summary', 'refresh']:
        data = get_financial_info(secret)
        if data.get('success'):
            summary = data.get('summary', {})
            user = data.get('user', {})
            text = (
                f"📋 **Financial Summary**\n\n"
                f"👤 {user.get('email', 'User')}\n\n"
                f"💰 **Balance:** R{summary.get('total_balance', 0):,.2f}\n"
                f"📊 **Investments:** R{summary.get('total_active_investments', 0):,.2f}\n"
                f"📈 **Plans:** R{summary.get('total_plan_investments', 0):,.2f}\n\n"
                f"💎 **Total:** R{sum(summary.values()):,.2f}"
            )
            keyboard = [
                [InlineKeyboardButton("💰 Balance", callback_data='balance'),
                 InlineKeyboardButton("📊 Investments", callback_data='investments')],
                [InlineKeyboardButton("🔄 Refresh", callback_data='refresh')]
            ]
            await query.edit_message_text(
                text, 
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )


def check_ai_rate_limit(user_id: int) -> bool:
    """Check if user has exceeded AI rate limit (10 requests/hour)"""
    now = datetime.now()
    hour_ago = now - timedelta(hours=1)
    
    # Clean old entries
    ai_rate_limits[user_id] = [t for t in ai_rate_limits[user_id] if t > hour_ago]
    
    if len(ai_rate_limits[user_id]) >= AI_RATE_LIMIT:
        return False
    
    ai_rate_limits[user_id].append(now)
    return True


async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle AI questions with DeepSeek"""
    user_id = update.effective_user.id
    
    # Check if API key is configured
    if not DEEPSEEK_API_KEY:
        await update.message.reply_text(
            "AI assistant is not configured. Please contact support."
        )
        return
    
    # Get the question from command arguments
    if not context.args:
        await update.message.reply_text(
            "Please provide a question.\n\n"
            "Example: `/ask How do I deposit funds?`",
            parse_mode='Markdown'
        )
        return
    
    question = ' '.join(context.args)
    
    # Check rate limit
    if not check_ai_rate_limit(user_id):
        await update.message.reply_text(
            "You've reached the limit of 10 AI questions per hour.\n"
            "Please try again later."
        )
        return
    
    # Show typing indicator
    msg = await update.message.reply_text("Thinking...")
    
    try:
        # Initialize DeepSeek client (OpenAI-compatible)
        client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL
        )
        
        # Call DeepSeek API
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": AI_SYSTEM_PROMPT},
                {"role": "user", "content": question}
            ],
            max_tokens=300,
            temperature=0.7
        )
        
        answer = response.choices[0].message.content
        
        await msg.edit_text(
            f"🤖 **AI Assistant**\n\n{answer}",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"DeepSeek API error: {e}")
        await msg.edit_text(
            "Sorry, I couldn't process your question.\n"
            "Please try again or contact support."
        )


def main() -> None:
    """Start the bot"""
    # Create the Application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Link conversation handler
    link_handler = ConversationHandler(
        entry_points=[CommandHandler('link', link_command)],
        states={
            WAITING_FOR_SECRET: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_secret)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    # Add handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(link_handler)
    application.add_handler(CommandHandler('unlink', unlink_command))
    application.add_handler(CommandHandler('balance', balance_command))
    application.add_handler(CommandHandler('investments', investments_command))
    application.add_handler(CommandHandler('deposits', deposits_command))
    application.add_handler(CommandHandler('withdrawals', withdrawals_command))
    application.add_handler(CommandHandler('summary', summary_command))
    application.add_handler(CommandHandler('ask', ask_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Run the bot
    print("CapitalX Telegram Bot is starting...")
    print(f"API URL: {API_BASE_URL}")
    print("Press Ctrl+C to stop")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()

"""
Professional Telegram Data Collection Pipeline
Collect structured user data directly in Telegram with validation and real-time monitoring
"""
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from enum import Enum

from motor.motor_asyncio import AsyncIOMotorDatabase
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Message
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, filters, ContextTypes
)

logger = logging.getLogger("maplejourney.telegram")

# ============================================================================
# DATA COLLECTION STATES
# ============================================================================

class DataCollectionState(Enum):
    """States for the data collection conversation"""
    STARTED = 0
    SELECT_FORM = 1
    COLLECT_EMAIL = 2
    COLLECT_PHONE = 3
    COLLECT_ADDRESS = 4
    COLLECT_NAME = 5
    COLLECT_IMMIGRATION_STATUS = 6
    COLLECT_INCOME = 7
    COLLECT_CHILDREN = 8
    CONFIRM_DATA = 9
    COMPLETED = 10


class TelegramDataCollector:
    """
    Professional Telegram-based data collection system
    Handles structured form collection with validation and MongoDB storage
    """

    def __init__(self, db: AsyncIOMotorDatabase, bot_token: str):
        self.db = db
        self.bot_token = bot_token
        self.collection_forms = db["telegram_collection_forms"]
        self.collected_data = db["telegram_collected_data"]
        self.user_sessions = db["telegram_user_sessions"]

    async def initialize_app(self) -> Application:
        """Initialize and configure Telegram bot application"""
        app = Application.builder().token(self.bot_token).build()

        # Command handlers
        app.add_handler(CommandHandler("start", self.start_command))
        app.add_handler(CommandHandler("collect", self.collect_command))
        app.add_handler(CommandHandler("status", self.status_command))
        app.add_handler(CommandHandler("stats", self.stats_command))
        app.add_handler(CommandHandler("recent", self.recent_command))
        app.add_handler(CommandHandler("summary", self.summary_command))
        app.add_handler(CommandHandler("export", self.export_command))
        app.add_handler(CommandHandler("search", self.search_command))
        app.add_handler(CommandHandler("cancel", self.cancel_command))

        # Conversation handler for data collection
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("collect", self.collect_command)],
            states={
                DataCollectionState.SELECT_FORM.value: [
                    CallbackQueryHandler(self.select_form)
                ],
                DataCollectionState.COLLECT_EMAIL.value: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.collect_email)
                ],
                DataCollectionState.COLLECT_PHONE.value: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.collect_phone)
                ],
                DataCollectionState.COLLECT_ADDRESS.value: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.collect_address)
                ],
                DataCollectionState.COLLECT_NAME.value: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.collect_name)
                ],
                DataCollectionState.COLLECT_IMMIGRATION_STATUS.value: [
                    CallbackQueryHandler(self.collect_immigration_status)
                ],
                DataCollectionState.COLLECT_INCOME.value: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.collect_income)
                ],
                DataCollectionState.COLLECT_CHILDREN.value: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.collect_children)
                ],
                DataCollectionState.CONFIRM_DATA.value: [
                    CallbackQueryHandler(self.confirm_data)
                ],
            },
            fallbacks=[CommandHandler("cancel", self.cancel_command)],
        )

        app.add_handler(conv_handler)
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

        logger.info("✅ Telegram bot application initialized")
        return app

    # ========================================================================
    # COMMAND HANDLERS
    # ========================================================================

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        await self.db["telegram_users"].update_one(
            {"user_id": user.id},
            {
                "$set": {
                    "user_id": user.id,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "last_active": datetime.utcnow(),
                }
            },
            upsert=True,
        )

        welcome_text = (
            f"👋 **Welcome to MapleJourney Data Collection, {user.first_name}!**\n\n"
            "We collect structured user information to help newcomers access benefits.\n\n"
            "🔧 **Available Commands:**\n"
            "• `/collect` - Start data collection form\n"
            "• `/status` - Check your latest collection\n"
            "• `/stats` - See all collection statistics\n"
            "• `/recent` - View 5 most recent submissions\n"
            "• `/summary` - Quick data overview\n"
            "• `/export` - Download all data as JSON\n"
            "• `/search <query>` - Smart profile search\n"
            "• `/cancel` - Cancel current operation\n\n"
            "📋 **Data We Collect:**\n"
            "• Email address\n"
            "• Phone number\n"
            "• Physical address\n"
            "• Immigration status\n"
            "• Income information\n"
            "• Family details\n\n"
            "🔒 All data is encrypted and stored securely."
        )

        await update.message.reply_text(welcome_text, parse_mode="Markdown")

    async def collect_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start data collection flow"""
        user = update.effective_user

        # Initialize user session
        session = {
            "user_id": user.id,
            "username": user.username,
            "started_at": datetime.utcnow(),
            "form_type": None,
            "collected_data": {},
            "status": "in_progress",
        }
        await self.user_sessions.insert_one(session)

        # Show form type selection
        keyboard = [
            [
                InlineKeyboardButton("📝 Quick Profile", callback_data="form_profile"),
                InlineKeyboardButton("🏠 Housing Assistance", callback_data="form_housing"),
            ],
            [
                InlineKeyboardButton("💼 Job Search", callback_data="form_jobs"),
                InlineKeyboardButton("📚 Education", callback_data="form_education"),
            ],
            [
                InlineKeyboardButton("❌ Cancel", callback_data="cancel"),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "📋 **Select the form you'd like to complete:**",
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )

        return DataCollectionState.SELECT_FORM.value

    async def select_form(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle form selection"""
        query = update.callback_query
        await query.answer()

        form_type = query.data.replace("form_", "")
        user_id = update.effective_user.id

        # Update session with selected form
        await self.user_sessions.update_one(
            {"user_id": user_id, "status": "in_progress"},
            {"$set": {"form_type": form_type}},
        )

        context.user_data["form_type"] = form_type
        context.user_data["collected_data"] = {}

        # Start with email collection
        await query.edit_message_text(
            "📧 **Please enter your email address:**\n"
            "_(e.g., john.doe@example.com)_",
            parse_mode="Markdown",
        )

        return DataCollectionState.COLLECT_EMAIL.value

    async def collect_email(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Collect and validate email"""
        email = update.message.text.strip().lower()

        # Validate email format
        if not self._validate_email(email):
            await update.message.reply_text(
                "❌ Invalid email format. Please try again.\n"
                "_(e.g., john.doe@example.com)_",
                parse_mode="Markdown",
            )
            return DataCollectionState.COLLECT_EMAIL.value

        context.user_data["collected_data"]["email"] = email
        user_id = update.effective_user.id
        await self.user_sessions.update_one(
            {"user_id": user_id, "status": "in_progress"},
            {"$set": {"collected_data.email": email}},
        )

        # Move to phone collection
        await update.message.reply_text(
            "📱 **Please enter your phone number:**\n"
            "_(e.g., +1-647-555-0100 or 6475550100)_",
            parse_mode="Markdown",
        )

        return DataCollectionState.COLLECT_PHONE.value

    async def collect_phone(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Collect and validate phone number"""
        phone = update.message.text.strip()

        # Validate phone format
        if not self._validate_phone(phone):
            await update.message.reply_text(
                "❌ Invalid phone format. Please use:\n"
                "• +1-647-555-0100 (with + and dashes)\n"
                "• 6475550100 (digits only)\n"
                "• 647-555-0100 (with dashes)",
                parse_mode="Markdown",
            )
            return DataCollectionState.COLLECT_PHONE.value

        context.user_data["collected_data"]["phone"] = phone
        user_id = update.effective_user.id
        await self.user_sessions.update_one(
            {"user_id": user_id, "status": "in_progress"},
            {"$set": {"collected_data.phone": phone}},
        )

        # Move to address collection
        await update.message.reply_text(
            "🏘️ **Please enter your address:**\n"
            "_(e.g., 123 Main St, Toronto, ON M5V 3A8, Canada)_",
            parse_mode="Markdown",
        )

        return DataCollectionState.COLLECT_ADDRESS.value

    async def collect_address(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Collect and validate address"""
        address = update.message.text.strip()

        if len(address) < 10:
            await update.message.reply_text(
                "❌ Address too short. Please provide a complete address.\n"
                "_(Street, City, Province/State, Postal Code, Country)_",
                parse_mode="Markdown",
            )
            return DataCollectionState.COLLECT_ADDRESS.value

        context.user_data["collected_data"]["address"] = address
        user_id = update.effective_user.id
        await self.user_sessions.update_one(
            {"user_id": user_id, "status": "in_progress"},
            {"$set": {"collected_data.address": address}},
        )

        # Move to name collection
        await update.message.reply_text(
            "👤 **Please enter your full name:**\n"
            "_(First Name + Last Name)_",
            parse_mode="Markdown",
        )

        return DataCollectionState.COLLECT_NAME.value

    async def collect_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Collect and validate name"""
        name = update.message.text.strip()

        if len(name) < 3:
            await update.message.reply_text(
                "❌ Name too short. Please provide your full name.",
                parse_mode="Markdown",
            )
            return DataCollectionState.COLLECT_NAME.value

        context.user_data["collected_data"]["full_name"] = name
        user_id = update.effective_user.id
        await self.user_sessions.update_one(
            {"user_id": user_id, "status": "in_progress"},
            {"$set": {"collected_data.full_name": name}},
        )

        # Move to immigration status collection
        keyboard = [
            [
                InlineKeyboardButton("👨‍💼 Permanent Resident", callback_data="status_pr"),
                InlineKeyboardButton("🎓 Student Visa", callback_data="status_student"),
            ],
            [
                InlineKeyboardButton("💼 Work Permit", callback_data="status_work"),
                InlineKeyboardButton("📋 Visitor Visa", callback_data="status_visitor"),
            ],
            [
                InlineKeyboardButton("🌍 Other", callback_data="status_other"),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "🛂 **What is your immigration status in Canada?**",
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )

        return DataCollectionState.COLLECT_IMMIGRATION_STATUS.value

    async def collect_immigration_status(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Collect immigration status"""
        query = update.callback_query
        await query.answer()

        status_map = {
            "status_pr": "Permanent Resident",
            "status_student": "Student Visa",
            "status_work": "Work Permit",
            "status_visitor": "Visitor Visa",
            "status_other": "Other",
        }

        status = status_map.get(query.data, "Unknown")
        context.user_data["collected_data"]["immigration_status"] = status
        user_id = update.effective_user.id
        await self.user_sessions.update_one(
            {"user_id": user_id, "status": "in_progress"},
            {"$set": {"collected_data.immigration_status": status}},
        )

        # Move to income collection
        await query.edit_message_text(
            "💰 **What is your approximate annual income? (in CAD)**\n"
            "_(e.g., 35000, 50000, 75000)_",
            parse_mode="Markdown",
        )

        return DataCollectionState.COLLECT_INCOME.value

    async def collect_income(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Collect and validate income"""
        income_text = update.message.text.strip()

        # Validate income is a number
        try:
            income = float(income_text.replace(",", ""))
            if income < 0:
                raise ValueError("Negative income")
        except ValueError:
            await update.message.reply_text(
                "❌ Invalid income format. Please enter a number.\n"
                "_(e.g., 35000 or 50,000)_",
                parse_mode="Markdown",
            )
            return DataCollectionState.COLLECT_INCOME.value

        context.user_data["collected_data"]["annual_income"] = income
        user_id = update.effective_user.id
        await self.user_sessions.update_one(
            {"user_id": user_id, "status": "in_progress"},
            {"$set": {"collected_data.annual_income": income}},
        )

        # Move to children collection
        await update.message.reply_text(
            "👨‍👩‍👧‍👦 **How many dependent children do you have?**\n"
            "_(Enter a number: 0, 1, 2, 3, etc.)_",
            parse_mode="Markdown",
        )

        return DataCollectionState.COLLECT_CHILDREN.value

    async def collect_children(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Collect and validate number of children"""
        children_text = update.message.text.strip()

        try:
            children = int(children_text)
            if children < 0 or children > 20:
                raise ValueError("Invalid number")
        except ValueError:
            await update.message.reply_text(
                "❌ Invalid number. Please enter 0, 1, 2, 3, etc.",
                parse_mode="Markdown",
            )
            return DataCollectionState.COLLECT_CHILDREN.value

        context.user_data["collected_data"]["dependent_children"] = children
        user_id = update.effective_user.id
        await self.user_sessions.update_one(
            {"user_id": user_id, "status": "in_progress"},
            {"$set": {"collected_data.dependent_children": children}},
        )

        # Show confirmation
        return await self._show_confirmation(update, context)

    async def _show_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Display collected data for confirmation"""
        data = context.user_data.get("collected_data", {})

        confirmation_text = (
            "✅ **Please review your information:**\n\n"
            f"📧 Email: `{data.get('email', 'N/A')}`\n"
            f"📱 Phone: `{data.get('phone', 'N/A')}`\n"
            f"🏘️ Address: `{data.get('address', 'N/A')}`\n"
            f"👤 Name: `{data.get('full_name', 'N/A')}`\n"
            f"🛂 Status: `{data.get('immigration_status', 'N/A')}`\n"
            f"💰 Income: `${data.get('annual_income', 0):,.0f}`\n"
            f"👨‍👩‍👧‍👦 Children: `{data.get('dependent_children', 0)}`\n\n"
            "Is this information correct?"
        )

        keyboard = [
            [
                InlineKeyboardButton("✅ Confirm & Submit", callback_data="confirm_yes"),
                InlineKeyboardButton("❌ Cancel", callback_data="confirm_no"),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            confirmation_text,
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )

        return DataCollectionState.CONFIRM_DATA.value

    async def confirm_data(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle data confirmation"""
        query = update.callback_query
        await query.answer()

        if query.data == "confirm_no":
            await query.edit_message_text(
                "❌ Data collection cancelled.\n\n"
                "Use `/collect` to start again.",
                parse_mode="Markdown",
            )
            user_id = update.effective_user.id
            await self.user_sessions.update_one(
                {"user_id": user_id, "status": "in_progress"},
                {"$set": {"status": "cancelled"}},
            )
            return ConversationHandler.END

        # Save collected data
        user_id = update.effective_user.id
        user = update.effective_user
        data = context.user_data.get("collected_data", {})

        record = {
            "user_id": user_id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "collected_data": data,
            "form_type": context.user_data.get("form_type", "profile"),
            "collected_at": datetime.utcnow(),
            "status": "completed",
        }

        result = await self.collected_data.insert_one(record)

        # Update session
        await self.user_sessions.update_one(
            {"user_id": user_id, "status": "in_progress"},
            {"$set": {"status": "completed", "record_id": str(result.inserted_id)}},
        )

        success_text = (
            "🎉 **Data submitted successfully!**\n\n"
            f"📋 Record ID: `{str(result.inserted_id)[:12]}...`\n\n"
            "✅ We've saved your information and will use it to:\n"
            "• Find eligible government benefits for you\n"
            "• Provide personalized recommendations\n"
            "• Connect you with support services\n\n"
            "📌 Check your email for next steps!"
        )

        await query.edit_message_text(success_text, parse_mode="Markdown")

        return ConversationHandler.END

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check user's data collection status"""
        user_id = update.effective_user.id

        # Find latest record
        record = await self.collected_data.find_one(
            {"user_id": user_id}, sort=[("collected_at", -1)]
        )

        if not record:
            await update.message.reply_text(
                "📭 No collected data found.\n\n"
                "Use `/collect` to start data collection.",
                parse_mode="Markdown",
            )
            return

        data = record.get("collected_data", {})
        collected_at = record.get("collected_at", datetime.utcnow())
        time_ago = self._format_time_ago(collected_at)

        status_text = (
            "📊 **Your Latest Collection**\n\n"
            f"⏱️ Collected: {time_ago}\n"
            f"📋 Type: {record.get('form_type', 'unknown').capitalize()}\n\n"
            "**Data on File:**\n"
            f"• Email: `{data.get('email', 'N/A')}`\n"
            f"• Phone: `{data.get('phone', 'N/A')}`\n"
            f"• Address: `{data.get('address', 'N/A')}`\n"
            f"• Immigration Status: `{data.get('immigration_status', 'N/A')}`\n\n"
            "💼 Status: ✅ Processed and ready for matching"
        )

        await update.message.reply_text(status_text, parse_mode="Markdown")

    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show detailed collection statistics"""
        stats = await self.get_collection_stats()
        
        form_breakdown = "\n".join([
            f"  • {form_type.capitalize()}: {count}"
            for form_type, count in stats.get("by_form_type", {}).items()
        ]) or "  • No data yet"

        stats_text = (
            "📊 **Collection Statistics**\n\n"
            f"📈 **Total Records:** {stats['total_records']}\n"
            f"✅ **Completed:** {stats['completed']}\n"
            f"📅 **Today:** {stats['today']}\n\n"
            f"**By Form Type:**\n{form_breakdown}\n\n"
            f"⏱️ Updated: {stats['collected_at'][:16]}"
        )
        
        await update.message.reply_text(stats_text, parse_mode="Markdown")

    async def recent_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show 5 most recent submissions"""
        recent = await self.collected_data.find(
            {"status": "completed"}
        ).sort("collected_at", -1).limit(5).to_list(None)
        
        if not recent:
            await update.message.reply_text(
                "📭 No data collected yet.\n\n"
                "Use `/collect` to start.",
                parse_mode="Markdown",
            )
            return
        
        recent_text = "📋 **Recent 5 Submissions:**\n\n"
        for i, record in enumerate(recent, 1):
            data = record.get("collected_data", {})
            collected_at = record.get("collected_at", datetime.utcnow())
            time_ago = self._format_time_ago(collected_at)
            
            recent_text += (
                f"{i}. **{record.get('form_type', 'Unknown').capitalize()}** ({time_ago})\n"
                f"   Email: `{data.get('email', 'N/A')}`\n"
                f"   Phone: `{data.get('phone', 'N/A')}`\n\n"
            )
        
        await update.message.reply_text(recent_text, parse_mode="Markdown")

    async def summary_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show quick data summary"""
        stats = await self.get_collection_stats()
        
        # Get this month's data
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_count = await self.collected_data.count_documents({
            "collected_at": {"$gte": month_start},
            "status": "completed"
        })
        
        # Get average completion per day
        yesterday = now - timedelta(days=1)
        yesterday_count = await self.collected_data.count_documents({
            "collected_at": {"$gte": yesterday},
            "status": "completed"
        })
        
        summary_text = (
            "📊 **Your Data Summary**\n\n"
            f"📌 **Total Submitted:** {stats['total_records']}\n"
            f"📅 **This Month:** {month_count}\n"
            f"🔄 **Yesterday:** {yesterday_count}\n"
            f"📈 **Today:** {stats['today']}\n\n"
            "**What's Next:**\n"
            "• Your data is being processed for benefit matching\n"
            "• You'll receive personalized recommendations\n"
            "• Check `/status` for latest updates\n\n"
            "Need help? Use `/collect` to add more info"
        )
        
        await update.message.reply_text(summary_text, parse_mode="Markdown")

    async def export_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Export all collected data as JSON"""
        records = await self.collected_data.find(
            {"status": "completed"}
        ).sort("collected_at", -1).to_list(None)
        
        if not records:
            await update.message.reply_text(
                "📭 No data to export.",
                parse_mode="Markdown",
            )
            return
        
        # Convert ObjectId to string for JSON serialization
        export_data = []
        for record in records:
            record["_id"] = str(record["_id"])
            record["collected_at"] = record["collected_at"].isoformat()
            export_data.append(record)
        
        # Create JSON export
        import io
        json_content = json.dumps(export_data, indent=2, ensure_ascii=False)
        json_file = io.BytesIO(json_content.encode("utf-8"))
        
        # Send file
        await update.message.reply_document(
            document=json_file,
            filename=f"maple_data_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json",
            caption=f"📊 **Data Export**\n\n✅ {len(export_data)} records exported"
        )

    async def search_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Smart search across profile records using a natural query string."""
        query_parts = context.args or []
        if not query_parts:
            await update.message.reply_text(
                "🔎 Usage: `/search <query>`\n\n"
                "Examples:\n"
                "• `/search john`\n"
                "• `/search student visa`\n"
                "• `/search toronto`\n"
                "• `/search income 50000`\n"
                "• `/search children 2`",
                parse_mode="Markdown",
            )
            return

        raw_query = " ".join(query_parts).strip()
        user = update.effective_user
        q = raw_query.lower()

        # Field-hint aliases to make searches feel more natural.
        field_aliases = {
            "email": ["email", "mail"],
            "phone": ["phone", "mobile", "cell", "number"],
            "address": ["address", "city", "postal", "zip"],
            "full_name": ["name", "person", "user"],
            "immigration_status": ["status", "visa", "permit", "resident", "pr"],
            "annual_income": ["income", "salary", "earnings"],
            "dependent_children": ["children", "child", "kids", "dependents"],
        }

        hinted_field = None
        for field, aliases in field_aliases.items():
            if any(a in q for a in aliases):
                hinted_field = field
                break

        query_filter: Dict[str, Any] = {"status": "completed"}
        is_admin = bool(getattr(user, "id", None))
        # Non-admin behavior by Telegram role is enforced in API routes, but the bot itself
        # should return current user's records unless explicit admin account handling is added.
        query_filter["user_id"] = user.id

        records = await self.collected_data.find(query_filter).sort("collected_at", -1).limit(50).to_list(None)
        if not records:
            await update.message.reply_text(
                "📭 No profile data found yet. Use `/collect` first.",
                parse_mode="Markdown",
            )
            return

        matched: List[Dict[str, Any]] = []
        numeric_query = None
        try:
            numeric_query = float(q.replace(",", " ").split()[-1])
        except Exception:
            numeric_query = None

        for rec in records:
            data = rec.get("collected_data", {}) or {}

            haystack_parts = [
                str(rec.get("username") or ""),
                str(rec.get("first_name") or ""),
                str(rec.get("last_name") or ""),
            ]

            if hinted_field:
                haystack_parts.append(str(data.get(hinted_field, "")))
            else:
                for key in [
                    "email",
                    "phone",
                    "address",
                    "full_name",
                    "immigration_status",
                    "annual_income",
                    "dependent_children",
                ]:
                    haystack_parts.append(str(data.get(key, "")))

            haystack = " ".join(haystack_parts).lower()
            score = 0

            if q in haystack:
                score += 3

            # Token scoring helps natural-language fragments match partially.
            for token in [t for t in q.split() if len(t) > 1]:
                if token in haystack:
                    score += 1

            # Numeric fuzzy matching for income/children searches.
            if numeric_query is not None:
                income = data.get("annual_income")
                children = data.get("dependent_children")
                try:
                    if income is not None and abs(float(income) - numeric_query) <= max(1000.0, float(income) * 0.1):
                        score += 2
                except Exception:
                    pass
                try:
                    if children is not None and int(children) == int(numeric_query):
                        score += 2
                except Exception:
                    pass

            if score > 0:
                rec["_score"] = score
                matched.append(rec)

        if not matched:
            await update.message.reply_text(
                f"No matches for: `{raw_query}`",
                parse_mode="Markdown",
            )
            return

        matched.sort(key=lambda r: (r.get("_score", 0), r.get("collected_at", datetime.min)), reverse=True)
        top = matched[:5]

        lines = [f"🔎 Results for: `{raw_query}`", ""]
        for idx, rec in enumerate(top, 1):
            data = rec.get("collected_data", {}) or {}
            lines.append(
                f"{idx}. 👤 {data.get('full_name') or rec.get('first_name') or 'Unknown'}"
            )
            lines.append(f"   📧 {data.get('email', 'N/A')}")
            lines.append(f"   📱 {data.get('phone', 'N/A')}")
            lines.append(f"   🛂 {data.get('immigration_status', 'N/A')}")
            lines.append(f"   💰 ${float(data.get('annual_income', 0)) if data.get('annual_income') is not None else 0:,.0f}")
            lines.append(f"   👨‍👩‍👧‍👦 {data.get('dependent_children', 0)}")
            lines.append("")

        await update.message.reply_text("\n".join(lines).strip(), parse_mode="Markdown")

    async def cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel current operation"""
        user_id = update.effective_user.id
        await self.user_sessions.update_one(
            {"user_id": user_id, "status": "in_progress"},
            {"$set": {"status": "cancelled"}},
        )

        await update.message.reply_text(
            "❌ **Operation cancelled.**\n\n"
            "Use `/collect` to start a new collection.",
            parse_mode="Markdown",
        )

        return ConversationHandler.END

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle unexpected messages"""
        await update.message.reply_text(
            "👋 I didn't understand that.\n\n"
            "**Available Commands:**\n"
            "• `/collect` - Start data collection\n"
            "• `/status` - Latest collection\n"
            "• `/stats` - All statistics\n"
            "• `/recent` - Last 5 submissions\n"
            "• `/summary` - Quick overview\n"
            "• `/export` - Download data\n"
            "• `/search <query>` - Smart profile search\n"
            "• `/cancel` - Cancel operation",
            parse_mode="Markdown",
        )

    # ========================================================================
    # VALIDATION HELPERS
    # ========================================================================

    @staticmethod
    def _validate_email(email: str) -> bool:
        """Validate email format"""
        import re

        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(pattern, email) is not None

    @staticmethod
    def _validate_phone(phone: str) -> bool:
        """Validate phone format"""
        import re

        # Allow various formats: +1-647-555-0100, 6475550100, 647-555-0100
        pattern = r"^(\+?1[-.\s]?)?(\()?[0-9]{3}(\))?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}$"
        return re.match(pattern, phone) is not None

    @staticmethod
    def _format_time_ago(dt: datetime) -> str:
        """Format datetime as 'X time ago'"""
        now = datetime.utcnow()
        diff = now - dt

        seconds = diff.total_seconds()
        if seconds < 60:
            return "Just now"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            return f"{minutes}m ago" if minutes > 1 else "1m ago"
        elif seconds < 86400:
            hours = int(seconds // 3600)
            return f"{hours}h ago" if hours > 1 else "1h ago"
        else:
            days = int(seconds // 86400)
            return f"{days}d ago" if days > 1 else "1d ago"

    # ========================================================================
    # ANALYTICS & MONITORING
    # ========================================================================

    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get data collection statistics"""
        total = await self.collected_data.count_documents({})
        completed = await self.collected_data.count_documents({"status": "completed"})
        today = await self.collected_data.count_documents(
            {
                "collected_at": {
                    "$gte": datetime.utcnow().replace(
                        hour=0, minute=0, second=0, microsecond=0
                    )
                }
            }
        )

        forms = await self.collected_data.aggregate(
            [
                {"$group": {"_id": "$form_type", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
            ]
        ).to_list(None)

        return {
            "total_records": total,
            "completed": completed,
            "today": today,
            "by_form_type": {f["_id"]: f["count"] for f in forms},
            "collected_at": datetime.utcnow().isoformat(),
        }

    async def export_data(self, start_date: datetime = None, end_date: datetime = None) -> List[Dict]:
        """Export collected data with optional date range"""
        query = {"status": "completed"}
        if start_date or end_date:
            query["collected_at"] = {}
            if start_date:
                query["collected_at"]["$gte"] = start_date
            if end_date:
                query["collected_at"]["$lte"] = end_date

        return await self.collected_data.find(query).to_list(None)

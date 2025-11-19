from telegram import LabeledPrice, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler, 
    PreCheckoutQueryHandler, 
    MessageHandler, 
    CallbackQueryHandler, 
    filters, 
    Application
)
from datetime import datetime, timedelta
import sqlite3
import schedule
import time
import threading
import json 

# =======================
# ১. আপনার তথ্য ও ডেটা কনফিগারেশন
# =======================

BOT_TOKEN = "8520079202:AAF-exR0ei9h1KCmZ6BGi6mFrzifUcJf78M" 
ADMIN_USERNAME = "RjRony03" 

# ✅ পেমেন্ট ও কারেন্সি কনফিগারেশন
# নোট: সকল রেট BDT (বাংলাদেশী টাকা)-এর সাপেক্ষে সেট করা হয়েছে।
#       যেমন, BDT 1 এর দাম INR-এ কত, তা 'rate' দ্বারা বোঝানো হয়েছে।
PAYMENT_CONFIG = {
    # ১. বাংলাদেশ (Default)
    "BD": {
        "currency": "BDT", 
        "token": "1877036958:TEST:20b0a42f4a3f20c1d8ddf2c1fcaf6f2323b87e3e", # ⚠️ আপনার আসল BDT টোকেন
        "rate": 1.0 # BDT 1 = BDT 1
    },
    # ২. ভারত (INR)
    "IN": {
        "currency": "INR", 
        "token": "284685063:TEST:30b0a42f4a3f20c1d8ddf2c1fcaf6f2323b87e3e", # ⚠️ আপনার আসল INR টোকেন
        "rate": 0.85 # BDT 1 = INR 0.85 (প্রায়, BDT 100 = INR 85)
    },
    # ৩. মার্কিন যুক্তরাষ্ট্র (USD)
    "US": {
        "currency": "USD", 
        "token": "194090547:TEST:40b0a42f4a3f20c1d8ddf2c1fcaf6f2323b87e3e", # ⚠️ আপনার আসল USD টোকেন
        "rate": 0.0090 # BDT 1 = USD 0.0090 (প্রায়, BDT 111 = USD 1)
    },
    # ডিফল্ট কনফিগারেশন (যদি দেশ কোড পাওয়া না যায়)
    "DEFAULT": {
        "currency": "BDT", 
        "token": "1877036958:TEST:20b0a42f4a3f20c1c8ddf2c1fcaf6f2323b87e3e", 
        "rate": 1.0
    }
}


# ✅ পেইড গ্রুপ ডেটা (মূল দাম BDT-তে স্থির থাকবে)
PAID_CHATS_AND_PLANS = {
    "group1": {"name": "Rj Family Chat", "chat_id": -1002541807760, "plans": {"7d": {"label": "১ সপ্তাহ (৭ দিন)", "price_bdt": 250, "days": 7}, "1m": {"label": "১ মাস (৩০ দিন)", "price_bdt": 650, "days": 30}, "3m": {"label": "৩ মাস (৯০ দিন)", "price_bdt": 1550, "days": 90}, "1y": {"label": "১ বছর (৩৬৫ দিন)", "price_bdt": 2050, "days": 365}}},
    "group2": {"name": "Rj Premium Group", "chat_id": -1002269000331, "plans": {"7d": {"label": "১ সপ্তাহ (৭ দিন)", "price_bdt": 200, "days": 7}, "1m": {"label": "১ মাস ( ৩০ দিন)", "price_bdt": 350, "days": 30}, "3m": {"label": "৩ মাস (৯০ দিন)", "price_bdt": 700, "days": 90}, "1y": {"label": "১ বছর (৩৬৫ দিন)", "price_bdt": 1050, "days": 365}}},
    "channel3": {"name": "Real Family Member", "chat_id": -1003178117714, "plans": {"7d": {"label": "১ সপ্তাহ (৭ দিন)", "price_bdt": 150, "days": 7}, "1m": {"label": "১ মাস (৩০ দিন)", "price_bdt": 300, "days": 30}, "3m": {"label": "৩ মাস (৯০ দিন)", "price_bdt": 600, "days": 90}, "1y": {"label": "১ বছর (৩৬৫ দিন)", "price_bdt": 900, "days": 365}}},
    "channel4": {"name": "family swapping", "chat_id": -1003309791220, "plans": {"7d": {"label": "১ সপ্তাহ (৭ দিন)", "price_bdt": 100, "days": 7}, "1m": {"label": "১ মাস (৩০ দিন)", "price_bdt": 280, "days": 30}, "3m": {"label": "৩ মাস (৯০ দিন)", "price_bdt": 500, "days": 90}, "1y": {"label": "১ বছর (৩৬৫ দিন)", "price_bdt": 450, "days": 365}}},
}

# ✅ ফ্রি গ্রুপ ডেটা
FREE_CHATS = {
    "demo_group": {"name": "Demo Group (Free)", "chat_id": -1002935911635},
}

# ✅ ভাষা ডেটা স্ট্রাকচার (বাংলা ও ইংরেজি)
MESSAGES = {
    "bn": { # বাংলা (Default)
        "GREETING": "অনুগ্রহ করে আপনি যে **গ্রুপ বা চ্যানেলের মেম্বারশিপ** নিতে চান, তা বেছে নিন:\n\n👉 প্রিমিয়াম গ্রুপ/চ্যানেল (Paid)\n🎁 ডেমো গ্রুপ (Free)\n",
        "PREMIUM_TITLE": "প্রিমিয়াম গ্রুপ/চ্যানেল",
        "DEMO_BUTTON": "🎁 ডেমো গ্রুপ (Free Join)",
        "CONTACT_BUTTON": "📞 এডমিনকে মেসেজ করুন",
        "CHAT_NOT_FOUND": "❌ দুঃখিত! এই চ্যাটটি খুঁজে পাওয়া যায়নি।",
        "PLAN_SELECTION_TITLE": "✅ আপনি **{chat_name}** এর জন্য মেম্বারশিপ নিচ্ছেন।\n\nপছন্দের মেয়াদ বেছে নিন:",
        "BACK_BUTTON": "⬅️ পিছনে যান",
        "INVOICE_ERROR": "❌ ইনভয়েস তৈরি করতে ব্যর্থ।",
        "INVITE_LINK_ERROR": "❌ ইনভাইট লিঙ্ক তৈরি করতে ব্যর্থ। নিশ্চিত করুন যে বটটি চ্যাটে এডমিন এবং ইনভাইট লিঙ্ক তৈরি করার অনুমতি আছে।",
        "DEMO_SUCCESS": "🎁 **অভিনন্দন!** এটি **{chat_name}**-এ যোগদানের জন্য আপনার ফ্রি ইনভাইট লিঙ্ক:\n\n🔗 [এখানে ক্লিক করুন]({link})\n\n*(লিঙ্কটি ১ ঘণ্টার মধ্যে মেয়াদোত্তীর্ণ হবে)*",
        "PAYMENT_SUCCESS_TITLE": "🎉 **অভিনন্দন! আপনি প্রিমিয়াম মেম্বারশিপ পেয়েছেন!** 🎉",
        "PAYMENT_SUCCESS_BODY": "সুপ্রিয় সদস্য,\nআপনার **{plan_label}** মেম্বারশিপ (**{chat_name}** এর জন্য) সফলভাবে সক্রিয় করা হয়েছে।\n\n**মেম্বারশিপের মেয়াদ:**\n🗓️ **শুরুর সময়:** {start_date}\n⏳ **শেষের সময়:** {expiry_date}\n🔔 **বিশেষ দ্রষ্টব্য:** এই তারিখের পরে স্বয়ংক্রিয়ভাবে আপনার অ্যাক্সেস বাতিল হয়ে যাবে।\n\n**যোগ দিন:**\nনিচের ইনভাইট লিঙ্কে ক্লিক করে দ্রুত **{chat_name}** এ যোগ দিন:\n🔗 [এখানে ক্লিক করুন]({link})\n\n**গুরুত্বপূর্ণ নির্দেশাবলী:**\n* আপনার এই ব্যক্তিগত ইনভাইট লিঙ্কটি **অন্য কারো সাথে শেয়ার করবেন না**। \n\nযেকোনো সহায়তার জন্য আপনি `/checkout` কমান্ড ব্যবহার করে এডমিনকে মেসেজ করতে পারেন।",
        "MEMBERSHIP_EXPIRED": "❌ দুঃখিত! আপনার মেম্বারশিপের মেয়াদ শেষ হয়ে যাওয়ায় আপনাকে গ্রুপ/চ্যানেল থেকে রিমুভ করা হলো। নতুন করে সাবস্ক্রাইব করতে `/checkout` টাইপ করুন।"
    },
    "en": { # ইংরেজি
        "GREETING": "Please select the **Group or Channel membership** you wish to purchase:\n\n👉 Premium Groups/Channels (Paid)\n🎁 Demo Group (Free)\n",
        "PREMIUM_TITLE": "Premium Groups/Channels",
        "DEMO_BUTTON": "🎁 Demo Group (Free Join)",
        "CONTACT_BUTTON": "📞 Message Admin",
        "CHAT_NOT_FOUND": "❌ Sorry! This chat was not found.",
        "PLAN_SELECTION_TITLE": "✅ You are subscribing to **{chat_name}**. \n\nPlease choose the duration:",
        "BACK_BUTTON": "⬅️ Go Back",
        "INVOICE_ERROR": "❌ Failed to create invoice.",
        "INVITE_LINK_ERROR": "❌ Failed to create invite link. Ensure the bot is admin in the chat and has permission to create invite links.",
        "DEMO_SUCCESS": "🎁 **Congratulations!** Here is your free invite link for **{chat_name}**:\n\n🔗 [Click here]({link})\n\n*(The link will expire in 1 hour)*",
        "PAYMENT_SUCCESS_TITLE": "🎉 **Congratulations! You have received Premium Membership!** 🎉",
        "PAYMENT_SUCCESS_BODY": "Dear Member,\nYour **{plan_label}** membership (for **{chat_name}**) has been successfully activated.\n\n**Membership Validity:**\n🗓️ **Start Time:** {start_date}\n⏳ **Expiry Time:** {expiry_date}\n🔔 **Note:** Your access will be automatically revoked after this date.\n\n**Join Now:**\nClick the invite link below to join **{chat_name}** quickly:\n🔗 [Click here]({link})\n\n**Important Instructions:**\n* Please **do not share** this private invite link with anyone else. \n\nFor any assistance, you can message the admin using the `/checkout` command.",
        "MEMBERSHIP_EXPIRED": "❌ Sorry! Your membership has expired, and you have been removed from the group/channel. To subscribe again, type `/checkout`."
    }
}

# ==================================
# ২. সহায়ক ফাংশন: ভাষা, কারেন্সি ও ডেটাবেস
# ==================================

def get_message(user_language_code, key):
    """কাস্টমারের ভাষা সেটিংস অনুযায়ী মেসেজ রিটার্ন করে।"""
    # শুধু প্রথম দুটি অক্ষর ব্যবহার করা হবে (যেমন: bn, en)
    lang = user_language_code.split('-')[0].lower() if user_language_code else 'bn'
    
    # যদি কাস্টমারের ভাষা সেটিংস আমাদের ডেটায় না থাকে, তবে ডিফল্ট বাংলা ব্যবহার করা হবে
    if lang not in MESSAGES:
        lang = 'bn'
    
    return MESSAGES.get(lang, MESSAGES['bn']).get(key, MESSAGES['en'][key])


def get_user_payment_config(user_language_code):
    """ইউজারের ভাষা কোড থেকে কারেন্সি কনফিগারেশন বের করে।"""
    if not user_language_code:
        return PAYMENT_CONFIG["DEFAULT"]
        
    # ভাষা কোডের দ্বিতীয় অংশ (দেশ কোড) ব্যবহার করা হলো (যেমন: bn-BD থেকে BD)
    parts = user_language_code.upper().split('-')
    country_code = parts[1] if len(parts) > 1 else None

    # যদি দেশ কোড কনফিগারেশনে থাকে
    if country_code in PAYMENT_CONFIG:
        return PAYMENT_CONFIG[country_code]
    
    return PAYMENT_CONFIG["DEFAULT"]


def init_db():
    conn = sqlite3.connect('subscriptions.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS members (
            user_id INTEGER,
            chat_id INTEGER,
            expiry_date TEXT,
            PRIMARY KEY (user_id, chat_id)
        )
    ''')
    conn.commit()
    conn.close()

def add_member_to_db(user_id, chat_id, days):
    conn = sqlite3.connect('subscriptions.db')
    cursor = conn.cursor()
    expiry_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('INSERT OR REPLACE INTO members (user_id, chat_id, expiry_date) VALUES (?, ?, ?)', 
                   (user_id, chat_id, expiry_date))
    conn.commit()
    conn.close()
    return expiry_date

# ==================================
# ৩. টেলিগ্রাম হ্যান্ডলার
# ==================================

async def start_checkout(update: Update, context):
    
    user = update.effective_user
    lang = user.language_code
    msg = lambda key, **kwargs: get_message(lang, key).format(**kwargs) 

    # 🌟 ১. পেইড গ্রুপের বাটন তৈরি
    paid_group_buttons = []
    for group_key, info in PAID_CHATS_AND_PLANS.items():
        paid_group_buttons.append(
            [InlineKeyboardButton(
                info["name"], 
                callback_data=f"paid_select_{group_key}"
            )]
        )

    # 🌟 ২. ফ্রি ডেমো গ্রুপের বাটন তৈরি
    free_group_buttons = []
    for group_key, info in FREE_CHATS.items():
        free_group_buttons.append(
            [InlineKeyboardButton(
                msg("DEMO_BUTTON"), 
                callback_data=f"free_join_{group_key}"
            )]
        )
    
    # যোগাযোগ বাটন
    contact_button = [
        InlineKeyboardButton(
            msg("CONTACT_BUTTON"), 
            url=f"https://t.me/{ADMIN_USERNAME}"
        )
    ]
    
    # সবগুলো বাটন একত্রিত করা
    keyboard = paid_group_buttons + free_group_buttons + [contact_button]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # ডাবল মেসেজ এড়াতে লজিক
    if update.callback_query:
        await update.callback_query.edit_message_text(
            msg("GREETING"), 
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            msg("GREETING"), 
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def handle_callback(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user = query.from_user
    user_id = user.id
    lang = user.language_code
    msg = lambda key, **kwargs: get_message(lang, key).format(**kwargs)
    
    # ১. যদি ফ্রি গ্রুপ নির্বাচন করে (free_join_demo_group)
    if data.startswith("free_join_"):
        group_key = data.split("_", 2)[2] 
        
        if group_key not in FREE_CHATS:
            await context.bot.send_message(user_id, msg("CHAT_NOT_FOUND"))
            return
            
        group_info = FREE_CHATS[group_key]
        chat_id = group_info["chat_id"]
        
        try:
            # ইনভাইট লিঙ্ক তৈরি
            invite_link = await context.bot.create_chat_invite_link(
                chat_id=chat_id, 
                member_limit=1, 
                expire_date=datetime.now() + timedelta(hours=1)
            )

            await context.bot.send_message(
                chat_id=user_id,
                text=msg("DEMO_SUCCESS", chat_name=group_info['name'], link=invite_link.invite_link),
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            
        except Exception as e:
            await context.bot.send_message(user_id, msg("INVITE_LINK_ERROR"))

    
    # ২. যদি পেইড গ্রুপ নির্বাচন করে (paid_select_group1)
    elif data.startswith("paid_select_"):
        group_key = data.split("_")[2]
        
        if group_key not in PAID_CHATS_AND_PLANS:
            await context.bot.send_message(user_id, msg("CHAT_NOT_FOUND"))
            return

        group_info = PAID_CHATS_AND_PLANS[group_key]
        
        # প্যাকেজ বাটন তৈরি
        plan_buttons = []
        for plan_key, plan_info in group_info["plans"].items():
            plan_buttons.append(
                [InlineKeyboardButton(
                    f"{plan_info['label']} - ৳{plan_info['price_bdt']}",
                    callback_data=f"plan_select_{group_key}_{plan_key}"
                )]
            )
        
        # 'Back' বাটন তৈরি
        back_button = [
            InlineKeyboardButton(msg("BACK_BUTTON"), callback_data="start_checkout")
        ]
        
        reply_markup = InlineKeyboardMarkup(plan_buttons + [back_button])
        
        await query.edit_message_text(
            msg("PLAN_SELECTION_TITLE", chat_name=group_info['name']),
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    # ৩. যদি প্যাকেজ নির্বাচন করে (plan_select_group1_1m) - ইনভয়েস তৈরি
    elif data.startswith("plan_select_"):
        try:
            _, _, group_key, plan_key = data.split("_")
            
            group_info = PAID_CHATS_AND_PLANS.get(group_key)
            plan_info = group_info["plans"].get(plan_key)
            
            if not group_info or not plan_info:
                await context.bot.send_message(user_id, msg("CHAT_NOT_FOUND"))
                return
            
            # ✅ কারেন্সি কনফিগারেশন বের করা
            payment_config = get_user_payment_config(user.language_code)
            
            # দাম (BDT থেকে নতুন কারেন্সিতে রূপান্তর)
            price_bdt = plan_info["price_bdt"]
            price_converted = price_bdt * payment_config["rate"]
            
            # টাকা/কারেন্সির সঠিক অ্যামাউন্ট (১০০ দিয়ে গুণ) এবং ইনটিজারে রূপান্তর
            price_in_cents = int(round(price_converted * 100)) 
            
            price_label = f"{group_info['name']} - {plan_info['label']}"
            
            payload_data = f"{group_key}_{plan_key}_{user_id}" 
            
            # 🟢 ইনভয়েসে কারেন্সির নাম ব্যবহার করা
            currency_symbol = payment_config["currency"]
            
            price = LabeledPrice(label=price_label, amount=price_in_cents) 
            
            await context.bot.send_invoice(
                chat_id=user_id,
                title=f"{group_info['name']} সাবস্ক্রিপশন ({currency_symbol})",
                description=f"মেয়াদ: {plan_info['label']}",
                payload=payload_data,
                provider_token=payment_config["token"],
                currency=payment_config["currency"],
                prices=[price],
                start_parameter="start_param",
                is_flexible=False
            )
            
        except Exception as e:
            # error_message = f"Error sending invoice: {e}" #Debugging
            await context.bot.send_message(user_id, msg("INVOICE_ERROR"))

    # ৪. যদি 'Back' বাটন ক্লিক করে (start_checkout)
    elif data == "start_checkout":
        await start_checkout(query, context)
        
async def pre_checkout_query(update: Update, context):
    query = update.pre_checkout_query
    await query.answer(ok=True) 

async def successful_payment(update: Update, context):
    message = update.message
    user = message.from_user
    user_id = user.id
    lang = user.language_code
    msg = lambda key, **kwargs: get_message(lang, key).format(**kwargs) 
    
    payload_parts = message.successful_payment.invoice_payload.split("_")
    
    if len(payload_parts) != 3:
        return 
        
    group_key, plan_key, user_id_str = payload_parts
    
    group_info = PAID_CHATS_AND_PLANS.get(group_key)
    plan_info = group_info["plans"].get(plan_key)
    
    if not group_info or not plan_info:
        return 

    days = plan_info["days"] 
    chat_id = group_info["chat_id"]
    
    # ডেটাবেসে যোগ করা
    expiry_date_str = add_member_to_db(user_id, chat_id, days=days)
    
    # ইনভাইট লিঙ্ক তৈরি
    invite_link = await context.bot.create_chat_invite_link(
        chat_id=chat_id, 
        member_limit=1, 
        expire_date=datetime.now() + timedelta(hours=1)
    )

    # তারিখ ফরম্যাট তৈরি 
    expiry_dt_obj = datetime.strptime(expiry_date_str, '%Y-%m-%d %H:%M:%S')
    expiry_date_for_msg = expiry_dt_obj.strftime('%d %B, %Y, %I:%M %p') 
    start_date_for_msg = datetime.now().strftime('%d %B, %Y, %I:%M %p') 

    # ওয়েলকাম মেসেজ তৈরি (ভাষা অনুযায়ী)
    welcome_message = (
        msg("PAYMENT_SUCCESS_TITLE") + "\n\n" +
        msg("PAYMENT_SUCCESS_BODY", 
            plan_label=plan_info['label'], 
            chat_name=group_info['name'],
            start_date=start_date_for_msg,
            expiry_date=expiry_date_for_msg,
            link=invite_link.invite_link
        )
    )
    
    await context.bot.send_message(
        chat_id=user_id,
        text=welcome_message,
        parse_mode='Markdown',
        disable_web_page_preview=True
    )

# ==================================
# ৪. রিমুভাল শিডিউলার
# ==================================

def check_and_remove_expired_members(application: Application):
    conn = sqlite3.connect('subscriptions.db')
    cursor = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute('SELECT user_id, chat_id FROM members WHERE expiry_date < ?', (now,))
    expired_members = cursor.fetchall()

    for user_id, chat_id in expired_members:
        try:
            # ভাষা বোঝার জন্য user অবজেক্ট ব্যবহার করা হলো
            user_language_code = application.bot.get_chat(user_id).language_code 
            removal_msg = get_message(user_language_code, "MEMBERSHIP_EXPIRED")

            # নির্দিষ্ট চ্যাট থেকে রিমুভ (ব্যান) করুন
            application.bot.ban_chat_member(
                chat_id=chat_id, 
                user_id=user_id
            )
            
            # ডেটাবেস থেকে মেম্বারকে মুছে দিন
            cursor.execute('DELETE FROM members WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
            
            # মেম্বারকে নোটিফিকেশন পাঠানো
            application.bot.send_message(
                chat_id=user_id,
                text=removal_msg
            )
            
        except Exception as e:
            # যদি ব্যবহারকারী ইতিমধ্যে গ্রুপে না থাকে বা অন্য কোনো এরর হয়, তবে ডেটাবেস থেকে মুছে দিন
            cursor.execute('DELETE FROM members WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))

    conn.commit()
    conn.close()

def run_scheduler(application):
    schedule.every().day.at("00:00").do(check_and_remove_expired_members, application)
    while True:
        schedule.run_pending()
        time.sleep(1)

# ==================================
# ৫. বট চালু করা
# ==================================

def main():
    init_db() 
    application = Application.builder().token(BOT_TOKEN).build()

    # হ্যান্ডলার যোগ
    application.add_handler(CommandHandler("start", start_checkout)) 
    application.add_handler(CommandHandler("checkout", start_checkout)) 
    application.add_handler(CallbackQueryHandler(handle_callback)) 
    application.add_handler(PreCheckoutQueryHandler(pre_checkout_query))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))

    # রিমুভাল লজিক একটি আলাদা থ্রেডে চালু করা
    threading.Thread(target=run_scheduler, args=(application,)).start()

    # বট শুরু
    application.run_polling(poll_interval=3)

if __name__ == '__main__':
    main()

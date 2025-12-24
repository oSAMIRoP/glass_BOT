import telebot
from telebot import types
import config
import database
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import jdatetime # برای تاریخ شمسی

bot = telebot.TeleBot(config.API_TOKEN)
database.init_db()

# تنظیم زمان‌بند
scheduler = BackgroundScheduler()
scheduler.start()

# کیبوردهای پیش‌فرض
PRESET_BTNS_1 = ["▶️ مشاهده ویدیو جدید", "📺 ویدیو جدید آپلود شد", "👁 مشاهده", "🎬 ویدیو جدید رو ببین", "🎞 دیدن ویدیو"]
PRESET_BTNS_2 = ["📢 مشاهده کانال", "🌐 پیج اصلی", "🔔 سابسکرایب کن", "🔥 فالو کن"]

def main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🚀 ساخت پست جدید")
    markup.row("📜 ۱۰ پست اخیر", "⚙️ تنظیمات کانال و لینک")
    markup.row("⏰ لیست زمان‌بندی‌ها") # دکمه جدید
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    bot.clear_step_handler_by_chat_id(message.chat.id)
    bot.send_message(message.chat.id, "💎 به ربات مدیریت محتوا خوش آمدید!", reply_markup=main_keyboard())

# --- بخش تنظیمات (مشابه قبل) ---
@bot.message_handler(func=lambda m: m.text == "⚙️ تنظیمات کانال و لینک")
def settings_start(message):
    msg = bot.send_message(message.chat.id, "1️⃣ آیدی کانال مقصد را بفرستید (مثلاً @MyChannel):")
    bot.register_next_step_handler(msg, set_channel)

def set_channel(message):
    if not message.text.startswith("@"):
        bot.send_message(message.chat.id, "❌ خطا! آیدی باید با @ شروع شود.")
        return
    database.update_settings(message.from_user.id, channel_id=message.text)
    msg = bot.send_message(message.chat.id, "2️⃣ حالا لینک صفحه اصلی (یوتوب/اینستا) را بفرستید یا /skip:")
    bot.register_next_step_handler(msg, set_main_link)

def set_main_link(message):
    if message.text != "/skip":
        database.update_settings(message.from_user.id, main_link=message.text)
    bot.send_message(message.chat.id, "✅ تنظیمات ذخیره شد.", reply_markup=main_keyboard())

# --- فرآیند ساخت پست (مشابه قبل) ---
user_data = {}

@bot.message_handler(func=lambda m: m.text == "🚀 ساخت پست جدید")
def create_post_start(message):
    ch_id, _ = database.get_settings(message.from_user.id)
    if not ch_id:
        bot.send_message(message.chat.id, "⚠️ ابتدا در تنظیمات آیدی کانال را ست کنید.")
        return
    user_data[message.from_user.id] = {}
    msg = bot.send_message(message.chat.id, "🔗 لینک پست (یوتیوب/اینستاگرام) را بفرستید:")
    bot.register_next_step_handler(msg, get_video_link)

def get_video_link(message):
    user_data[message.from_user.id]['link'] = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("بدون تصویر ❌")
    msg = bot.send_message(message.chat.id, "🖼 تصویر/تامنیل را بفرستید یا دکمه را بزنید:", reply_markup=markup)
    bot.register_next_step_handler(msg, get_photo)

def get_photo(message):
    user_data[message.from_user.id]['photo'] = message.photo[-1].file_id if message.content_type == 'photo' else None
    msg = bot.send_message(message.chat.id, "📝 متن پست را بنویسید:", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, get_text)

def get_text(message):
    user_data[message.from_user.id]['text'] = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(*PRESET_BTNS_1)
    msg = bot.send_message(message.chat.id, "🔘 متن دکمه اول را انتخاب یا بنویسید:", reply_markup=markup)
    bot.register_next_step_handler(msg, get_btn1)

def get_btn1(message):
    user_data[message.from_user.id]['btn1'] = message.text
    _, main_link = database.get_settings(message.from_user.id)
    if main_link:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True); markup.add(*PRESET_BTNS_2); markup.add("نمی‌خواهم ❌")
        msg = bot.send_message(message.chat.id, "🔘 متن دکمه دوم:", reply_markup=markup)
        bot.register_next_step_handler(msg, get_btn2)
    else:
        user_data[message.from_user.id]['btn2'] = None
        finalize(message)

def get_btn2(message):
    user_data[message.from_user.id]['btn2'] = None if "نمی‌خواهم" in message.text else message.text
    finalize(message)

def finalize(message):
    u_id = message.from_user.id
    d = user_data[u_id]
    p_id = database.save_post(u_id, d['text'], d['link'], d['photo'], d['btn1'], d['btn2'])
    
    bot.send_message(u_id, "✅ پست ساخته شد.", reply_markup=main_keyboard())
    send_preview(u_id, p_id)

def send_preview(chat_id, post_id):
    p = database.get_post(post_id)
    ch_id, main_link = database.get_settings(p[5])
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(p[3], url=p[1]))
    if p[4]: markup.add(types.InlineKeyboardButton(p[4], url=main_link))
    
    if p[2]: bot.send_photo(chat_id, p[2], caption=p[0], reply_markup=markup)
    else: bot.send_message(chat_id, p[0], reply_markup=markup)

    op = types.InlineKeyboardMarkup()
    op.row(types.InlineKeyboardButton("📤 انتشار فوری", callback_data=f"send_{post_id}"),
           types.InlineKeyboardButton("⏰ زمان‌بندی", callback_data=f"sch_{post_id}"))
    bot.send_message(chat_id, "عملیات:", reply_markup=op)

# --- سیستم زمان‌بندی با پشتیبانی شمسی ---

def post_to_channel(post_id):
    p = database.get_post(post_id)
    ch_id, main_link = database.get_settings(p[5])
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(p[3], url=p[1]))
    if p[4]: markup.add(types.InlineKeyboardButton(p[4], url=main_link))
    try:
        if p[2]: bot.send_photo(ch_id, p[2], caption=p[0], reply_markup=markup)
        else: bot.send_message(ch_id, p[0], reply_markup=markup)
    except: pass

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    data = call.data.split("_")
    action = data[0]
    
    # انتشار فوری
    if action == "send":
        p_id = data[1]
        post_to_channel(p_id)
        bot.answer_callback_query(call.id, "🚀 ارسال شد.")
    
    # درخواست زمان‌بندی
    elif action == "sch":
        p_id = data[1]
        msg = bot.send_message(call.message.chat.id, "📅 زمان انتشار (شمسی یا میلادی) را بفرستید:")
        bot.register_next_step_handler(msg, save_schedule, p_id)
    
    # حذف زمان‌بندی (بخش اصلاح شده)
    elif action == "deljob":
        target_job_id = f"{data[1]}_{data[2]}" # ترکیب کامل آیدی جاب از کال‌بک
        
        job = scheduler.get_job(target_job_id)
        if job:
            scheduler.remove_job(target_job_id)
            bot.edit_message_text(f"❌ زمان‌بندی برای پست {job.args[0]} لغو و حذف شد.", 
                                  call.message.chat.id, call.message.message_id)
        else:
            bot.answer_callback_query(call.id, "⚠️ این زمان‌بندی دیگر وجود ندارد یا ارسال شده است.", show_alert=True)
            # آپدیت کردن پیام برای اینکه کاربر دوباره دکمه را نزند
            bot.edit_message_text("🚫 این مورد قبلاً حذف یا ارسال شده است.", call.message.chat.id, call.message.message_id)

def save_schedule(message, post_id):
    text = message.text
    try:
        # تشخیص شمسی یا میلادی
        if "/" in text:
            date_part, time_part = text.split(" ")
            y, m, d = map(int, date_part.split("/"))
            hh, mm = map(int, time_part.split(":"))
            target_dt = jdatetime.datetime(y, m, d, hh, mm).togregorian()
        else:
            target_dt = datetime.strptime(text, '%Y-%m-%d %H:%M')

        if target_dt < datetime.now():
            bot.send_message(message.chat.id, "❌ زمان در گذشته است!")
            return

        # تعیین یک ID ثابت و مشخص برای این جاب
        job_id = f"job_{post_id}"
        
        # اگر از قبل زمان‌بندی برای این پست وجود داشت، اول حذفش کن تا جدید جایگزین بشه
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)

        scheduler.add_job(post_to_channel, 'date', run_date=target_dt, args=[post_id], id=job_id)
        
        bot.send_message(message.chat.id, f"⏳ پست {post_id} برای تاریخ {text} فیکس شد.")
    except Exception as e:
        bot.send_message(message.chat.id, "❌ فرمت اشتباه! طبق الگو بفرستید.\nمثال: `1402/10/25 18:30`")

# --- مدیریت زمان‌بندی‌ها ---
@bot.message_handler(func=lambda m: m.text == "⏰ لیست زمان‌بندی‌ها")
def list_schedules(message):
    jobs = scheduler.get_jobs()
    if not jobs:
        bot.send_message(message.chat.id, "📭 هیچ پستی در صف انتظار نیست.")
        return
    
    bot.send_message(message.chat.id, "📋 پست‌های رزرو شده:")
    for job in jobs:
        # ساخت دکمه حذف با آیدی دقیق جاب
        m = types.InlineKeyboardMarkup()
        # ارسال آیدی کامل جاب برای حذف دقیق
        m.add(types.InlineKeyboardButton("🗑 لغو این زمان‌بندی", callback_data=f"deljob_{job.id}"))
        
        post_id = job.args[0]
        run_time = job.next_run_time.strftime('%Y-%m-%d %H:%M')
        
        bot.send_message(message.chat.id, 
                         f"📦 پست شماره: {post_id}\n⏰ زمان ارسال (میلادی): {run_time}", 
                         reply_markup=m)
# --- تاریخچه ---
@bot.message_handler(func=lambda m: m.text == "📜 ۱۰ پست اخیر")
def history_handler(message):
    posts = database.get_history(message.from_user.id)
    if not posts:
        bot.send_message(message.chat.id, "تاریخچه خالی است.")
        return
    for item in posts:
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("📤 ارسال مجدد", callback_data=f"send_{item[0]}"))
        bot.send_message(message.chat.id, f"📝 پست {item[0]}:\n{item[1][:40]}...", reply_markup=m)

bot.infinity_polling()
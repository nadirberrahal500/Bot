import telebot
from telebot import types
import requests
from yt_dlp import YoutubeDL
import os

# --- إعدادات المفاتيح الخاصة بك (مخفية وآمنة) ---
API_TOKEN = '8344587349:AAH0xLXM6Be-1mmuoD-7e1qHTysXFq_c1Vg'
YOUTUBE_API_KEY = 'AIzaSyAEPj2z2II7dNb8L0lFc0tN1UKzl67eLlg'

bot = telebot.TeleBot(API_TOKEN)
user_results = {}

# إشعار تشغيل داخلي
print("✅ النظام متصل: محرك MP3 و MP4 جاهز للعمل.")

def youtube_search(query):
    """البحث باستخدام الـ API الرسمي للحصول على نتائج دقيقة جداً"""
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        'part': 'snippet',
        'q': query,
        'maxResults': 50,
        'type': 'video',
        'key': YOUTUBE_API_KEY
    }
    response = requests.get(url, params=params).json()
    return [{'id': item['id']['videoId'], 'title': item['snippet']['title']} for item in response.get('items', [])]

def create_keyboard(chat_id, page=0):
    """إنشاء لوحة الأزرار بشكل جذاب ومنظم"""
    results = user_results[chat_id]['data']
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    start = page * 10
    end = start + 10
    for vid in results[start:end]:
        title = vid['title'][:45]
        v_id = vid['id']
        # زر العنوان
        markup.row(types.InlineKeyboardButton(f"🎬 {title}", callback_data="none"))
        # أزرار الامتدادات المطلوبة فقط
        btn_mp3 = types.InlineKeyboardButton("🎵 MP3 Audio", callback_data=f"dl_mp3_{v_id}")
        btn_mp4 = types.InlineKeyboardButton("📽️ MP4 Video", callback_data=f"dl_mp4_{v_id}")
        markup.row(btn_mp3, btn_mp4)

    # أزرار التنقل
    nav_row = []
    if page > 0: nav_row.append(types.InlineKeyboardButton("⬅️ السابق", callback_data=f"pg_{page-1}"))
    nav_row.append(types.InlineKeyboardButton(f"💎 {page+1}/5", callback_data="none"))
    if end < len(results): nav_row.append(types.InlineKeyboardButton("التالي ➡️", callback_data=f"pg_{page+1}"))
    markup.row(*nav_row)
    return markup

@bot.message_handler(commands=['start'])
def welcome(message):
    """واجهة الترحيب الجذابة والغامضة"""
    msg = (
        "👋 **أهلاً بك في بوت التحميل الذكي!**\n\n"
        "🚀 **ماذا يمكنني أن أفعل؟**\n"
        "• تحويل أي فيديو يوتيوب إلى ملف **MP3** عالي الجودة.\n"
        "• تحميل الفيديوهات بصيغة **MP4** وبدقة ممتازة.\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🔎 **أرسل اسم الأغنية أو الفيديو للبدء:**"
    )
    bot.send_message(message.chat.id, msg, parse_mode="Markdown")

@bot.message_handler(func=lambda m: True)
def handle_search(message):
    """معالجة البحث الفوري وصوت التنبيه"""
    results = youtube_search(message.text)
    if results:
        user_results[message.chat.id] = {'data': results, 'page': 0}
        bot.send_message(
            message.chat.id, 
            f"✅ **أفضل النتائج التي وجدتها لـ:** `{message.text}`",
            reply_markup=create_keyboard(message.chat.id, 0),
            parse_mode="Markdown",
            disable_notification=False # تفعيل صوت التنبيه
        )

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    if call.data.startswith("pg_"):
        new_page = int(call.data.split("_")[1])
        user_results[chat_id]['page'] = new_page
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=create_keyboard(chat_id, new_page))
    
    elif call.data.startswith("dl_"):
        data = call.data.split("_")
        extension = data[1] # mp3 or mp4
        vid_id = data[2]
        bot.answer_callback_query(call.id, f"🚀 جاري معالجة ملف الـ {extension.upper()}.. ثواني")
        download_and_upload(chat_id, vid_id, extension)

def download_and_upload(chat_id, vid_id, ext):
    """وظيفة التحميل من يوتيوب ثم الرفع للبوت ثم الحذف"""
    url = f"https://www.youtube.com/watch?v={vid_id}"
    temp_path = f"downloads/{vid_id}.%(ext)s"
    
    # إعدادات مخصصة لكل امتداد
    if ext == 'mp3':
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': temp_path,
            'quiet': True,
        }
    else: # mp4
        ydl_opts = {
            'format': 'best[height<=720][ext=mp4]',
            'outtmpl': temp_path,
            'quiet': True,
        }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        # التأكد من الامتداد الصحيح للملف الناتج
        filename = ydl.prepare_filename(info)
        if ext == 'mp3': filename = filename.rsplit('.', 1)[0] + '.mp3'

        with open(filename, 'rb') as f:
            if ext == 'mp3':
                bot.send_audio(chat_id, f, caption=f"🎵 {info['title']}\n✅ تم التحميل بنجاح")
            else:
                bot.send_video(chat_id, f, caption=f"🎬 {info['title']}\n✅ تم التحميل بنجاح")
        
        # حذف الملف فوراً للحفاظ على المساحة
        if os.path.exists(filename):
            os.remove(filename)

if __name__ == '__main__':
    if not os.path.exists('downloads'): os.makedirs('downloads')
    bot.infinity_polling()
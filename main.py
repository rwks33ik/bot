import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from telegram.error import BadRequest, Forbidden
import instaloader
import urllib.parse
from instaloader import Profile, ProfileNotExistsException, ConnectionException
import json
import os
import random
import aiohttp
import requests
from urllib.parse import quote
import asyncio
from urllib.parse import quote, urlparse, quote_plus
from io import BytesIO
import time
import zipfile
import shutil
import tempfile
import marshal
import py_compile
import httpx

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = "8647502075:AAHWN6F6C0X8aXrGdcVp9ATbb9EFidGBdLQ"
ADMIN_ID = 6808883615  
DEVELOPER_USERNAME = "@QR_l4" 

CHANNELS_FILE = "channels_data.json"
GOOGLE_CARDS_FILE = "google.json"
VISA_FILE = "visa.json"  

# APIs
VIRUSTOTAL_API_KEY = "19462df75ad313db850e532a2e8869dc8713c07202b1c62ebf1aa7a18a2e0173"
VIDEO_API_BASE = "https://api.yabes-desu.workers.dev/ai/tool/txt2video"
SHORTENER_API = "https://api.dfkz.xo.je/apis/v1/short.php?url="
INSTA_INFO_API = "https://sherifbots.serv00.net/Api/insta.php?user="
AI_API_URL = 'https://ai-api.magicstudio.com/api/ai-art-generator'
SEARCH_NEW_API = "https://sii3.top/api/search.php?q="


COLUMNS = 2
DOWNLOAD_FOLDER = "site_download"

SUPPORTED_LANGUAGES = {
    "العربية": "ar",
    "الإنجليزية": "en",
    "الإسبانية": "es",
    "الفرنسية": "fr",
    "الألمانية": "de",
    "الإيطالية": "it",
    "البرتغالية": "pt",
    "الروسية": "ru",
    "الصينية": "zh",
    "اليابانية": "ja",
    "الكورية": "ko",
    "التركية": "tr",
    "الفارسية": "fa",
    "العبرية": "he"
}

def load_channels():
    if os.path.exists(CHANNELS_FILE):
        with open(CHANNELS_FILE, 'r') as f:
            return json.load(f)
    return {"channels": []}

def load_google_cards():
    try:
        if os.path.exists(GOOGLE_CARDS_FILE):
            with open(GOOGLE_CARDS_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
             
                cards = []
                current_card = {}
                
                lines = content.split('\n')
                for line in lines:
                    line = line.strip()
                    if line.startswith('🔑 الكود:'):
                        current_card['code'] = line.split(':')[1].strip()
                    elif line.startswith('💰 القيمة:'):
                        current_card['amount'] = line.split(':')[1].strip()
                    elif line.startswith('📅 الإصدار:'):
                        current_card['issue_date'] = line.split(':')[1].strip()
                    elif line.startswith('⏳ الانتهاء:'):
                        current_card['expiry'] = line.split(':')[1].strip()
                    elif line.startswith('🔢 التسلسلي:'):
                        current_card['serial'] = line.split(':')[1].strip()
                    elif line.startswith('━━━━━━━━━━━━━━━━━━━━━━━') and current_card:
                        cards.append(current_card)
                        current_card = {}
                
                return cards
    except Exception as e:
        logging.error(f"Error loading google cards: {e}")
    return []

# تحميل بيانات الفيزا
def load_visa_cards():
    try:
        if os.path.exists(VISA_FILE):
            with open(VISA_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
                # استخراج كروت الفيزا من النص
                cards = []
                current_card = {}
                
                lines = content.split('\n')
                for line in lines:
                    line = line.strip()
                    if line.startswith('🔢 رقم البطاقة:'):
                        current_card['card_number'] = line.split(':')[1].strip()
                    elif line.startswith('👤 اسم صاحب الفيزاء :'):
                        current_card['owner_name'] = line.split(':')[1].strip()
                    elif line.startswith('📅 تاريخ الانتهاء:'):
                        current_card['expiry_date'] = line.split(':')[1].strip()
                    elif line.startswith('🔒 رمز(CVV):'):
                        current_card['cvv'] = line.split(':')[1].strip()
                    elif line.startswith('🔑 الرقم السري (PIN):'):
                        current_card['pin'] = line.split(':')[1].strip()
                    elif line.startswith('💵 الرصيد المتاح:'):
                        current_card['balance'] = line.split(':')[1].strip()
                    elif line.startswith('========== 💳 Visa ==========') and current_card:
                        cards.append(current_card)
                        current_card = {}
                
                return cards
    except Exception as e:
        logging.error(f"Error loading visa cards: {e}")
    return []

def save_channels(data):
    with open(CHANNELS_FILE, 'w') as f:
        json.dump(data, f)

def is_admin(user_id):
    return user_id == ADMIN_ID

def arrange_buttons_in_columns(buttons_list, columns=COLUMNS):
    keyboard = []
    for i in range(0, len(buttons_list), columns):
        row = buttons_list[i:i+columns]
        keyboard.append(row)
    return keyboard

async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    channels = load_channels()["channels"]
    
    if not channels:
        return True 
    
    not_subscribed = []
    
    for channel in channels:
        try:
            member = await context.bot.get_chat_member(chat_id=channel["id"], user_id=user_id)
            if member.status in ['left', 'kicked']:
                not_subscribed.append(channel)
        except (BadRequest, Forbidden) as e:
            logging.error(f"Error checking subscription for channel {channel['id']}: {e}")
            continue
    
    if not_subscribed:
        
        keyboard = []
        for channel in not_subscribed:
            channel_id = channel["id"]
            channel_name = channel["name"]
            username = channel.get("username", "")
            
            if username:
                url = f"https://t.me/{username}"
            else:
                url = "https://t.me/c/{}".format(str(channel_id).replace('-100', ''))
            
            keyboard.append([InlineKeyboardButton(f"انضم إلى {channel_name}", url=url)])
        
        keyboard.append([InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data="check_subscription")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "⚠️ يجب عليك الانضمام إلى القنوات التالية لاستخدام البوت:",
            reply_markup=reply_markup
        )
        return False
    
    return True

def translate_to_english(text: str) -> str:
    try:
        translate_url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=en&dt=t&q={quote(text)}"
        response = requests.get(translate_url)
        response.raise_for_status()
        result = response.json()
        return result[0][0][0]
    except Exception as e:
        logging.error(f"Translation error: {e}")
        return text  
        #انشاء صور 
def create_ai_image(prompt: str) -> bytes:
    """إنشاء صورة باستخدام API الذكاء الاصطناعي"""
    try:
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-US,en;q=0.9,ar;q=0.8",
            "origin": "https://magicstudio.com",
            "priority": "u=1, i",
            "referer": "https://magicstudio.com/ai-art-generator/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
        }
        
        data = {
            'prompt': prompt,
            'output_format': 'bytes',
            'user_profile_id': 'null',
            'user_is_subscribed': 'true'
        }
        
        response = requests.post(AI_API_URL, headers=headers, data=data)
        response.raise_for_status()
        return response.content
    except Exception as e:
        logging.error(f"AI Image generation error: {e}")
        raise

# وظائف إنشاء الفيديو
def fetch_video_to_temp(prompt: str) -> str:
    """إنشاء فيديو من النص باستخدام API"""
    url = f"{VIDEO_API_BASE}?prompt={quote_plus(prompt)}"
    # زيادة الوقت إلى 20 دقيقة
    resp = requests.get(url, stream=True, timeout=1200)

    if resp.status_code != 200:
        raise RuntimeError(f"API error {resp.status_code}: {resp.text[:200]}")

    ctype = resp.headers.get("Content-Type", "")
    if "application/json" in ctype:
        data = resp.json()
        video_url = (
            data.get("url")
            or data.get("video")
            or data.get("result")
            or data.get("data")
        )
        if not video_url:
            raise RuntimeError("❌ ما لكيت رابط فيديو بالـ API response.")

        # زيادة الوقت للفيديو أيضًا
        r2 = requests.get(video_url, stream=True, timeout=1200)
        if r2.status_code != 200:
            raise RuntimeError(f"Video URL error {r2.status_code}")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tf:
            for chunk in r2.iter_content(chunk_size=1024 * 64):
                tf.write(chunk)
            return tf.name
    else:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tf:
            for chunk in resp.iter_content(chunk_size=1024 * 64):
                tf.write(chunk)
            return tf.name

# دالة جلب معلومات تيك توك
async def get_tiktok_info(username: str) -> dict:
    """جلب معلومات حساب تيك توك"""
    api_url = f"https://tik-batbyte.vercel.app/tiktok?username={username}"
    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        logging.error(f"TikTok API error: {e}")
        return {}

# خدمة معلومات تيك توك
async def tiktok_service_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # التحقق من الاشتراك أولاً
    if not await check_subscription(update, context, user_id):
        return
    
    await query.message.reply_text(
        "📱 **معلومات حساب تيك توك**\n\n"
        "أرسل لي معرف حساب التيك توك بدون علامة @\n\n"
        "مثال: • yemen_tik "
    )
    
    context.user_data["awaiting_tiktok_username"] = True

# خدمة فحص الملفات
async def file_check_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if not await check_subscription(update, context, user_id):
        return
    
    await query.message.reply_text(
        "🔍 **فحص الملفات ضد الاختراق**\n\n"
        "أرسل لي ملف Python (.py) 📁"
    )
    
    context.user_data["awaiting_file_check"] = True

# خدمة إنشاء الفيديو
async def video_service_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # التحقق من الاشتراك أولاً
    if not await check_subscription(update, context, user_id):
        return
    
    await query.message.reply_text(
        "🎬 **إنشاء فيديو من النص**\n\n"
        "أرسل لي وصفاً للفيديو الذي تريد إنشاءه.\n\n"
        "مثال: قطه 🐈 تحت المطر "
    )
    
    context.user_data["awaiting_video_prompt"] = True

async def check_file_with_virustotal(file_data, file_name):
    """فحص الملف باستخدام VirusTotal API"""
    try:
        files = {"file": (file_name, file_data)}
        headers = {"x-apikey": VIRUSTOTAL_API_KEY}
        upload_url = "https://www.virustotal.com/api/v3/files"

        upload_response = requests.post(upload_url, files=files, headers=headers)
        upload_response.raise_for_status()
        analysis_id = upload_response.json()["data"]["id"]

        analysis_url = f"https://www.virustotal.com/api/v3/analyses/{analysis_id}"
        for _ in range(10):
            analysis_response = requests.get(analysis_url, headers=headers)
            result = analysis_response.json()
            status = result["data"]["attributes"]["status"]
            if status == "completed":
                break
            time.sleep(3)

        stats = result["data"]["attributes"]["stats"]
        malicious = stats.get("malicious", 0)
        suspicious = stats.get("suspicious", 0)
        harmless = stats.get("harmless", 0)
        undetected = stats.get("undetected", 0)
        sha256 = result["meta"]["file_info"]["sha256"]

        return {
            "malicious": malicious,
            "suspicious": suspicious,
            "harmless": harmless,
            "undetected": undetected,
            "sha256": sha256,
            "success": True
        }
    except Exception as e:
        logging.error(f"VirusTotal error: {e}")
        return {"success": False, "error": str(e)}
def format_number(num):
    """تنسيق الأرقام بشكل جميل"""
    try:
        if isinstance(num, str):
            num = int(num.replace(',', '').replace(' ', ''))
        else:
            num = int(num)
            
        if num >= 1000000000:
            return f"{num/1000000000:.1f}B"
        elif num >= 1000000:
            return f"{num/1000000:.1f}M"
        elif num >= 1000:
            return f"{num/1000:.1f}K"
        else:
            return str(num)
    except:
        return "0"

def get_tiktok_info(username):
    """جلب معلومات تيك توك من API الأصلي"""
    api_url = f"https://tik-batbyte.vercel.app/tiktok?username={username}"
    
    try:
        response = requests.get(api_url, timeout=10)
        data = response.json()
        
        if data.get('username'):
            # إضافة معلومات افتراضية للمعلومات غير المتوفرة في API
            return {
                'success': True,
                'username': data.get('username', 'غير متوفر'),
                'nickname': data.get('nickname', 'غير متوفر'),
                'verified': 'نعم ✅' if data.get('verified', False) else 'لا ❌',
                'create_date': data.get('create_date', 'غير معروف'),
                'last_update': data.get('last_update', 'غير معروف'),
                'following_visibility': 'ظاهر 👀' if data.get('following_visibility', True) else 'مخفي 🙈',
                'bio_link': data.get('bio_link', 'غير متوفر'),
                'is_private': data.get('is_private', False),
                'region': data.get('region', 'غير معروف'),
                'language': data.get('language', 'غير معروف'),
                'followers': format_number(data.get('followers', 0)),
                'following': format_number(data.get('following', 0)),
                'friends': format_number(data.get('friends', 0)),
                'hearts': format_number(data.get('hearts', 0)),
                'videos': format_number(data.get('videos', 0)),
                'favorites': format_number(data.get('favorites', 0)),
                'comments': 'مفعل ✅' if data.get('comments_enabled', True) else 'معطل ❌',
                'downloads': 'يسمح ✅' if data.get('downloads_enabled', True) else 'لا يسمح ❌',
                'live_enabled': 'مفعل ✅' if data.get('live_enabled', False) else 'غير مفعل ❌',
                'support_level': data.get('support_level', 'غير معروف'),
                'live_room_id': data.get('live_room_id', 'غير متوفر'),
                'live_viewers': format_number(data.get('live_viewers', 0)),
                'star_subscribers': format_number(data.get('star_subscribers', 0)),
                'team_subscribers': format_number(data.get('team_subscribers', 0)),
                'user_id': data.get('user_id', 'غير متوفر'),
                'sec_uid': data.get('sec_uid', 'غير متوفر'),
                'search_count': format_number(data.get('search_count', 0)),
                'bio': data.get('bio', 'غير متوفر'),
                'profile_picture': data.get('profile_picture', '')
            }
        else:
            return {'success': False}
            
    except Exception as e:
        return {'success': False}

# معالجة معلومات تيك توك
async def handle_tiktok_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_tiktok_username", False):
        username = update.message.text.strip()
        
        if not username:
            await update.message.reply_text("يرجى إرسال معرف صالح لحساب التيك توك.")
            return
        
        
        processing_msg = await update.message.reply_text(f"🔍 جاري البحث عن معلومات الحساب: {username}")
        
        try:
           
            user_data = await asyncio.to_thread(get_tiktok_info, username)
            
            if user_data.get('success'):
       
                caption = f"""📱 معلومات المستخدم 📱
━━━━━━━━━━━━━━━━
🔹 يوزر الحساب: @{user_data['username']}
🔸 اسم الحساب: {user_data['nickname']}
✅ التوثيق: {user_data['verified']}
📆 تاريخ إنشاء الحساب: {user_data['create_date']}
⌚ آخر تعديل للاسم: {user_data['last_update']}
👀 رؤية اللذين يتابعهم: {user_data['following_visibility']}
🔗 رابط البايو: {user_data['bio_link']}
🔒 حساب خاص: {'نعم 🔒' if user_data['is_private'] else 'لا 🔓'}
📍 دولة المستخدم: {user_data['region']}
💬 لغة الحساب: {user_data['language']}

👤 إجمالي المتابعين: {user_data['followers']}
👥 إجمالي الذين يتابعهم: {user_data['following']}
👫 عدد الأصدقاء: {user_data['friends']}
👍 إجمالي الايكات: {user_data['hearts']}
📺 إجمالي المقاطع: {user_data['videos']}
❤️ مفضلة: {user_data['favorites']}
💬 التعليقات: {user_data['comments']}
📥 التحميلات: {user_data['downloads']}
🔴 البث المباشر: {user_data['live_enabled']}
🥇 مستوى الدعم في البثوث: {user_data['support_level']}
🔢 روم ايدي البث: {user_data['live_room_id']}
👀 عدد مشاهدين البث الان: {user_data['live_viewers']}
🌟 عدد المشتركين في النجمة: {user_data['star_subscribers']}
🎟️ عدد المشتركين في الفريق: {user_data['team_subscribers']}

📛 ايدي الحساب: {user_data['user_id']}
🔑 الايدي الثانوي: {user_data['sec_uid']}
📊 عدد مرات البحث عن الحساب: {user_data['search_count']}

📝 الوصف:
{user_data['bio']}

💌 تم الحصول على المعلومات بواسطة بوت
@QR_l4229BOT """

                # إرسال الصورة مع المعلومات
                try:
                    if user_data['profile_picture']:
                        await update.message.reply_photo(
                            photo=user_data['profile_picture'],
                            caption=caption
                        )
                    else:
                        await update.message.reply_text(caption)
                except Exception as e:
                    
                    try:
                        await update.message.reply_text(caption)
                    except:
                        
                        parts = [caption[i:i+4000] for i in range(0, len(caption), 4000)]
                        for part in parts:
                            await update.message.reply_text(part)
            else:
                await update.message.reply_text(f"❌ لم يتم العثور على معلومات للحساب: {username}")
                
        except Exception as e:
            await update.message.reply_text(f"حدث خطأ أثناء جلب المعلومات: {str(e)}")
        
      
        try:
            await processing_msg.delete()
        except:
            pass
        
        context.user_data["awaiting_tiktok_username"] = False
        return

# معالجة إنشاء الفيديو
async def handle_video_generation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_video_prompt", False):
        prompt = update.message.text
        
        if not prompt.strip():
            await update.message.reply_text("يرجى إرسال وصف صالح للفيديو.")
            return
        
        loading_msg = await update.message.reply_text("⏳ جاري إنشاء الفيديو... قد يستغرق من 2 دقائق")
        
        try:
            # إنشاء الفيديو
            video_path = await asyncio.to_thread(fetch_video_to_temp, prompt)
            
          
            await loading_msg.delete()
            
         
            await update.message.reply_video(
                video=open(video_path, "rb"),
                caption=f"النص: {prompt}\n\n👨‍💻 Dev: {DEVELOPER_USERNAME}",
                supports_streaming=True,
            )
            
            
            os.unlink(video_path)
            
        except requests.exceptions.Timeout:
            await loading_msg.edit_text("⏰ طلبك استغرق وقتًا طويلاً جداً. جرب مرة أخرى بوصف أقصر.")
        except Exception as e:
            await loading_msg.edit_text(f"❌ حدث خطأ أثناء إنشاء الفيديو: {str(e)}")
        
        context.user_data["awaiting_video_prompt"] = False
        return

# وظائف سحب ملفات الموقع
async def cleanup_site_files(folder_path):
    await asyncio.sleep(180)  
    try:
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
    except Exception as e:
        logging.error(f"Error cleaning up site files: {e}")

def download_site_simple(url, folder):
    try:
        
        if os.path.exists(folder):
            shutil.rmtree(folder)
        os.makedirs(folder, exist_ok=True)
        
       
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
     
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        if not filename or '.' not in filename:
            filename = "index.html"
        
      
        main_file = os.path.join(folder, filename)
        with open(main_file, 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        return main_file
    except Exception as e:
        logging.error(f"Error downloading site: {e}")
        return None

# خدمة سحب ملفات الموقع
async def site_download_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    
    if not await check_subscription(update, context, user_id):
        return
    
    await query.message.reply_text(
        "🌐 **سحب ملفات الموقع**\n\n"
        "أرسل لي رابط أي موقع وسأقوم بتحميل الصفحة الرئيسية وإرسالها لك.\n\n"
        "📝 مثال: • http://test-site.org "
    )
    
    context.user_data["awaiting_site_url"] = True

# معالجة سحب ملفات الموقع
async def handle_site_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_site_url", False):
        url = update.message.text.strip()
        
        if not (url.startswith('http://') or url.startswith('https://')):
            await update.message.reply_text("الرجاء إرسال رابط صحيح يبدأ بـ http:// أو https://")
            return
        
        # التحقق إذا كان الموقع محظور (ينتهي بـ pages.dev)
        if url.lower().endswith('pages.dev') or '.pages.dev/' in url.lower():
            await update.message.reply_text("❌ هاذا الموقع محظور ولا يمكن تحميله ")
            context.user_data["awaiting_site_url"] = False
            return
        
        await update.message.reply_text("جارٍ تحميل الصفحة الرئيسية... قد يستغرق هذا بعض الوقت.")
        
        try:
            
            downloaded_file = download_site_simple(url, DOWNLOAD_FOLDER)
            if not downloaded_file:
                await update.message.reply_text("فشل في تحميل الصفحة الرئيسية. يرجى التحقق من الرابط والمحاولة مرة أخرى.")
                return
            
          
            await update.message.reply_text("تم التحميل بنجاح! جاري إرسال الملف...")
            
            if os.path.exists(downloaded_file) and os.path.getsize(downloaded_file) > 0:
                with open(downloaded_file, 'rb') as f:
                    await context.bot.send_document(
                        chat_id=update.message.chat_id,
                        document=f,
                        filename=os.path.basename(downloaded_file),
                        caption="ها هو الموقع الذي طلبته"
                    )
            else:
                await update.message.reply_text("عذرًا، لم يتم إنشاء الملف بشكل صحيح.")
                return
            
           
            asyncio.create_task(cleanup_site_files(DOWNLOAD_FOLDER))
            
        except Exception as e:
            await update.message.reply_text(f"حدث خطأ أثناء معالجة الطلب: {str(e)}")
        
        context.user_data["awaiting_site_url"] = False
        return
# خدمة معلومات انستجرام
async def insta_info_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # التحقق من الاشتراك أولاً
    if not await check_subscription(update, context, user_id):
        return
    
    await query.message.reply_text(
        "📷 **معلومات حساب انستجرام**\n\n"
        "أرسل لي معرف حساب الانستجرام بدون علامة @ \n\n"
        "مثال: • username  "
        
    )
    
    context.user_data["awaiting_insta_username"] = True

# معالجة اختصار الروابط
async def handle_shortener(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_shortener_url", False):
        url = update.message.text.strip()
        
        if not (url.startswith('http://') or url.startswith('https://')):
            await update.message.reply_text("الرجاء إرسال رابط صحيح يبدأ بـ http:// أو https://")
            return
        
        await update.message.reply_text("🔗 جاري اختصار الرابط...")
        
        try:
          
            api_url = f"{SHORTENER_API}{quote(url)}"
            response = requests.get(api_url)
            
            if response.status_code == 200:
                shortened_url = response.text.strip()
                await update.message.reply_text(
                    f"✅ تم اختصار الرابط بنجاح:\n\n"
                    f"📎 الرابط الأصلي: {url}\n"
                    f"🔗 الرابط المختصر: {shortened_url}"
                )
            else:
                await update.message.reply_text("❌ فشل في اختصار الرابط. يرجى المحاولة مرة أخرى.")
                
        except Exception as e:
            await update.message.reply_text(f"❌ حدث خطأ أثناء اختصار الرابط: {str(e)}")
        
        context.user_data["awaiting_shortener_url"] = False
        return
        
# معالجة معلومات انستجرام
async def handle_insta_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_insta_username", False):
        username = update.message.text.strip()
        
        if not username:
            await update.message.reply_text("يرجى إرسال معرف صالح لحساب الانستجرام.")
            return
        
        loading_msg = await update.message.reply_text(f"🔍 جاري جمع المعلومات عن الحساب: @{username}")   
        try:
           
            data = fetch_instagram_data(username)
            
            if data is None:
                await loading_msg.edit_text("❌ فشل في الاتصال بالخادم. حاول مرة أخرى لاحقًا.")
                return
            
           
            if data.get('code') == 100000 and 'data' in data and 'data' in data['data']:
                user_data = data['data']['data']
                
                # تنسيق الأرقام بفواصل
                followers = user_data.get('follower_count', 0)
                following = user_data.get('following_count', 0)
                posts = user_data.get('media_count', 0)
                
                followers_formatted = f"{followers:,}"
                following_formatted = f"{following:,}"
                posts_formatted = f"{posts:,}"
                
                
                private_status = "نعم 🔒" if user_data.get('is_private') else "لا 🔓"
                verified_status = "نعم ✅" if user_data.get('is_verified') else "لا ❌"
                business_status = "نعم 🏢" if user_data.get('is_business') else "لا 👤"
                
              
                caption = f"""*📊 معلومات حساب الانستجرام:*

• 📛 *الاسم:* {user_data.get('full_name', username)}
• 🔂 *اليوزر:* @{user_data.get('username', username)}
• 🆔 *الـ ID:* `{user_data.get('id', 'غير متوفر')}`
• 📝 *السيرة الذاتية:* {user_data.get('biography', 'غير متوفر')}

• 👥 *المتابعون:* {followers_formatted}
• 🔔 *يتابع:* {following_formatted}
• 📸 *المنشورات:* {posts_formatted}

• 🔒 *الحساب خاص:* {private_status}
• ✅ *الحساب موثوق:* {verified_status}
• 💼 *حساب أعمال:* {business_status}
• 📂 *الفئة:* {user_data.get('category', 'غير محدد')}
• 📧 *البريد الإلكتروني:* {user_data.get('public_email', 'غير متوفر')}
• 🔗 *رابط خارجي:* {user_data.get('external_url', 'لا يوجد')}

•📎*رابط الحساب : \n * https://www.instagram.com/{username}"""

                # إرسال الصورة مع المعلومات
                profile_pic_url = user_data.get('hd_profile_pic_url_info', {}).get('url')
                if profile_pic_url:
                    try:
                        await update.message.reply_photo(
                            photo=profile_pic_url,
                            caption=caption,
                            parse_mode="Markdown"
                        )
                    except Exception as e:
                        logging.error(f"خطأ في إرسال الصورة: {e}")
                        await update.message.reply_text(caption, parse_mode="Markdown")
                else:
                    await update.message.reply_text(caption, parse_mode="Markdown")
                    
                await loading_msg.delete()
                
            else:
                error_msg = data.get('message', 'خطأ غير معروف')
                await loading_msg.edit_text(
                    f"*❌ لم أتمكن من العثور على المستخدم:* `{username}`\n\n"
                    f"*السبب:* {error_msg}",
                    parse_mode="Markdown"
                )
                
        except Exception as e:
            logging.error(f"خطأ غير متوقع: {e}")
            await loading_msg.edit_text(
                f"*❌ حدث خطأ أثناء جلب المعلومات:*\n\n{str(e)}",
                parse_mode="Markdown"
            )
        
        context.user_data["awaiting_insta_username"] = False
        return
# خدمة اختصار الروابط
async def shortener_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # التحقق من الاشتراك أولاً
    if not await check_subscription(update, context, user_id):
        return
    
    await query.message.reply_text(
        "🔗 اختصار الروابط\n\n"
        "أرسل لي الرابط الذي تريد اختصاره\n\n"
        "مثال: "
        "• https://www.google.com\n"
    )
    
    context.user_data["awaiting_shortener_url"] = True        
# دالة مساعدة لجلب بيانات انستا
def fetch_instagram_data(username):
    try:
        api_url = f"https://sherifbots.serv00.net/Api/insta.php?user={username}"
        logging.info(f"جلب البيانات من: {api_url}")
        
        response = requests.get(api_url, timeout=15)
        logging.info(f"كود الحالة: {response.status_code}")
        
        if response.status_code != 200:
            logging.error(f"كود حالة غير ناجح: {response.status_code}")
            return None
        
        data = response.json()
        return data
        
    except Exception as e:
        logging.error(f"خطأ في جلب البيانات: {e}")
        return None

# معالجة تشفير ملفات Python
async def handle_py_encryption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_py_file", False):
        document = update.message.document
        
        if not document.file_name.endswith('.py'):
            await update.message.reply_text("يرجى إرسال ملف بايثون بصيغة .py فقط")
            return
        
        await update.message.reply_text("🔐 جاري تشفير الملف باستخدام marshal...")
        
        try:
            # تحميل الملف
            file = await context.bot.get_file(document.file_id)
            file_data = await file.download_as_bytearray()
            
            # تشفير الملف باستخدام marshal
            output_data = await encrypt_marshal(bytes(file_data), document.file_name)
            
            # إرسال الملف المشفر مباشرة
            await update.message.reply_document(
                document=output_data,
                filename=f"encrypted_{document.file_name}",
                caption="✅ تم تشفير الملف باستخدام طريقة marshal"
            )
            
        except Exception as e:
            await update.message.reply_text(f"❌ حدث خطأ أثناء التشفير: {str(e)}")
        
        context.user_data["awaiting_py_file"] = False
        return
# معالجة تشفير ملفات Python
async def handle_py_encryption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_py_file", False):
        document = update.message.document
        
        if not document.file_name.endswith('.py'):
            await update.message.reply_text("يرجى إرسال ملف بايثون بصيغة .py فقط")
            return
        
        await update.message.reply_text("🔐 جاري تشفير الملف باستخدام marshal...")
        
        try:
           
            file = await context.bot.get_file(document.file_id)
            file_data = await file.download_as_bytearray()
            
            output_data = await encrypt_marshal(bytes(file_data), document.file_name)
            
            await update.message.reply_document(
                document=output_data,
                filename=f"encrypted_{document.file_name}",
                caption="✅ تم تشفير الملف باستخدام طريقة marshal"
            )
            
        except Exception as e:
            await update.message.reply_text(f"❌ حدث خطأ أثناء التشفير: {str(e)}")
        
        context.user_data["awaiting_py_file"] = False
        return     
# تشفير باستخدام marshal
async def encrypt_marshal(file_data, file_name):
    try:
       
        code_str = file_data.decode('utf-8')
        
      
        code = compile(code_str, file_name, 'exec')
        
        # تشفير باستخدام marshal
        marshaled_data = marshal.dumps(code)
        
        
        encrypted_content = f'''# Encrypted with marshal
# Dev: {DEVELOPER_USERNAME}
import marshal
exec(marshal.loads({repr(marshaled_data)}))'''
        
        return BytesIO(encrypted_content.encode('utf-8'))
        
    except Exception as e:
        raise Exception(f"خطأ في التشفير: {str(e)}")
# خدمة تشفير ملفات Python
async def encrypt_py_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if not await check_subscription(update, context, user_id):
        return
    
    await query.message.reply_text(
        "🔐 **تشفير ملفات Python**\n\n"
        "أرسل لي ملف Python بصيغه (.py) وسأقوم بتشفيره باستخدام طريقة marshal "
        
    )
    
    context.user_data["awaiting_py_file"] = True   
# خدمة معلومات تويتر X
async def twitter_info_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    
    if not await check_subscription(update, context, user_id):
        return
    
    await query.message.reply_text(
        "🐦 *معلومات حساب تويتر X*\n\n"
        "أرسل لي معرف حساب تويتر بدون علامة @\n\n"
        "مثال: • elonmusk"
    )
    
    context.user_data["awaiting_twitter_username"] = True

async def get_twitter_info(username):
    """جلب معلومات حساب تويتر باستخدام API"""
    try:
        url = f'https://twitter.com/i/api/graphql/qW5u-DAuXpMEG0zA1F7UGQ/UserByScreenName?variables=%7B%22screen_name%22%3A%22{username}%22%2C%22withSafetyModeUserFields%22%3Atrue%7D&features=%7B%22hidden_profile_likes_enabled%22%3Atrue%2C%22hidden_profile_subscriptions_enabled%22%3Atrue%2C%22rweb_tipjar_consumption_enabled%22%3Atrue%2C%22responsive_web_graphql_exclude_directive_enabled%22%3Atrue%2C%22verified_phone_label_enabled%22%3Afalse%2C%22subscriptions_verification_info_is_identity_verified_enabled%22%3Atrue%2C%22subscriptions_verification_info_verified_since_enabled%22%3Atrue%2C%22highlights_tweets_tab_ui_enabled%22%3Atrue%2C%22responsive_web_twitter_article_notes_tab_enabled%22%3Atrue%2C%22creator_subscriptions_tweet_preview_api_enabled%22%3Atrue%2C%22responsive_web_graphql_skip_user_profile_image_extensions_enabled%22%3Afalse%2C%22responsive_web_graphql_timeline_navigation_enabled%22%3Atrue%7D&fieldToggles=%7B%22withAuxiliaryUserLabels%22%3Afalse%7D'
        
        headers = {
            'Authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
            'Cookie': 'd_prefs=MjoxLGNvbnNlbnRvdmVyLHRleHRfdmVyc2lvbjoxMDAw; gt=1785000746309525950; kdt=ys0wWaFXY4Oxw4XSRMOvZb4Y22quAziEHA6MSfJb; att=1-kSfvpuOymSsPKRUWkUfEA6OPrfhVFOpGoCtPNfC7; lang=en; dnt=1; guest_id=v1%3A171441362464581377; g_state=i_l; guest_id_marketing=v1%3A171441362464581377; guest_id_ads=v1%3A171441362464581377; personalization_id="v1_9ERZxK0bRksu3hVQuAasdA=="; ads_prefs="HBISAAA="; auth_token=8b9b9ceab4cecb0594c01748ff7ad4c436e409f2; ct0=4469d9dcacfbfd5d4b4a186958e8297b0ae66f38cb892194597668b6faeb1ce2776890b781137b08f93a0dcdbff5994a7368999ba58f71f8075cb8c6ea9f1879b8da8135618a5934e76dac0d62c4207a; twid=u%3D1785006610047262720; _twitter_sess=BAh7ESIKZmxhc2hJQzonQWN0aW9uQ29udROLxlcjo6Rmxhc2g6OkZsYXNoSGFzaHsABjoKQHVzZWR7ADoHaWQiJTY5NDU0NTE5MjM5ZTk0ZTJjODdjMzVjNWI3OTgxZGE5Og9jcmVhdGVkX2F0bCsI1BQHK48BOgxjc3JmX2lkIiVmMWUxMzkwZTMxN2VkNTczNjMwMDc3ODZhMTS1OTdkOCIJcHJycCIAOgl1c2VybCsJAGCX8Q2exRg6CHByc2kMOghwcnVsKwkAYJfxDZ7FGDoIcHJsIiswajMxc3hEaXoxZnRIcko3UVlGMHE4OWV6RzI3MEZZdTFyeTBkcjoIcHJhaQY6H2xac3RfcGFzc3dvcmRf',
            'X-Csrf-Token': '4469d9dcacfbfd5d4b4a186958e8297b0ae66f38cb892194597668b6faeb1ce2776890b781137b08f93a0dcdbff5994a7368999ba58f71f8075cb8c6ea9f1879b8da8135618a5934e76dac0d62c4207a',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=10)
            data = response.json()
            
            if 'errors' in data:
                return None
                
            if 'data' not in data:
                return None
            
            user_result = data.get('data', {}).get('user', {})
            
            if not user_result or 'result' not in user_result:
                return None
            
            user_result = user_result.get('result', {})
            
            if user_result.get('__typename') == 'UserUnavailable':
                return None
            
            if 'legacy' not in user_result:
                return None
            
            legacy = user_result.get('legacy', {})
            
            created_at = legacy.get('created_at', 'Unknown')
            if created_at != 'Unknown':
                created_year = created_at.split()[-1] if created_at else 'Unknown'
            else:
                created_year = 'Unknown'
            
            return {
                'username': legacy.get('screen_name', 'None'),
                'name': legacy.get('name', 'None'),
                'user_id': user_result.get('rest_id', '0'),
                'followers': legacy.get('followers_count', 0),
                'following': legacy.get('friends_count', 0),
                'tweets': legacy.get('statuses_count', 0),
                'bio': legacy.get('description', 'None'),
                'location': legacy.get('location', 'None'),
                'created_at': created_year,
                'verified': user_result.get('is_blue_verified', False) or legacy.get('verified', False),
                'protected': legacy.get('protected', False)
            }
            
    except Exception as e:
        logging.error(f"Twitter API error: {e}")
        return None

# معالجة معلومات تويتر
async def handle_twitter_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_twitter_username", False):
        username = update.message.text.strip()
        
        if not username:
            await update.message.reply_text("يرجى إرسال معرف صالح لحساب تويتر.")
            return
        
      
        if username.startswith('@'):
            username = username[1:]
        
        
        processing_msg = await update.message.reply_text(f"🔍 جاري جمع معلومات الحساب: @{username}")
        
        try:
            # جلب المعلومات من API
            user_data = await get_twitter_info(username)
            
            if user_data:
               
                verified_status = "✅ موثق" if user_data['verified'] else "❌ غير موثق"
                protected_status = "🔒 خاص" if user_data['protected'] else "🌐 عام"
                
                caption = f"""
🐦 *معلومات حساب تويتر*

▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬

👤 *المعلومات الأساسية:*
 🕸• *اليوزر:* `@{user_data['username']}`
🕵️‍♀️• *الاسم:* {user_data['name']}
🆔• *الرقم التعريفي:* `{user_data['user_id']}`
🔢• *تاريخ الإنشاء:* {user_data['created_at']}

📊 *الإحصائيات:*
🗯• *التغريدات:* {user_data['tweets']:,}
⁉️• *المتابعون:* {user_data['followers']:,}
🎌• *المتابَعون:* {user_data['following']:,}

📍 *المعلومات الشخصية:*
🌐• *الموقع:* {user_data['location']}
✔️• *الحالة:* {verified_status}
📶• *نوع الحساب:* {protected_status}
📝 *البايو:*
{user_data['bio']}

▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
تم جمع المعلومات بنجاح ✅
                """
                
                await update.message.reply_text(caption)
            else:
                await update.message.reply_text(f"❌ لم يتم العثور على معلومات للحساب: @{username}\n\nتأكد من صحة اسم المستخدم وأن الحساب غير خاص.")
                
        except Exception as e:
            await update.message.reply_text(f"حدث خطأ أثناء جلب المعلومات: {str(e)}")
        
        
        try:
            await processing_msg.delete()
        except:
            pass
        
        context.user_data["awaiting_twitter_username"] = False
        return    
                                    
# خدمة توليد كروت جوجل
async def google_card_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # التحقق من الاشتراك أولاً
    if not await check_subscription(update, context, user_id):
        return
    
    await query.message.edit_text ("⏳ جاري توليد الكرت...")
    
    try:
        # تحميل الكروت من الملف
        cards = load_google_cards()
        
        if not cards:
            await query.message.edit_text("❌ لا توجد كروت متاحة حالياً.")
            return
        
        selected_card = random.choice(cards)
        
        # إنشاء رسالة الكرت
        card_message = f"""
✅ تم توليد كرت جوجل بلاي بنجاح!
━━━━━━━━━━━━━━━━━━━━━━━
🔑 الكود: {selected_card['code']}
💰 القيمة: {selected_card['amount']}
📅 الإصدار: {selected_card['issue_date']}
⏳ الانتهاء: {selected_card['expiry']}
🔢 التسلسلي: {selected_card['serial']}
━━━━━━━━━━━━━━━━━━━━━━━
استمتع بالكرت يا حب! 🎁
        """
        
        await query.message.edit_text(card_message)
        
    except Exception as e:
        logging.error(f"Google card error: {e}")
        await query.message.edit_text("❌ حدث خطأ أثناء توليد الكرت. يرجى المحاولة لاحقاً.")

# خدمة توليد فيزا
async def visa_service_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if not await check_subscription(update, context, user_id):
        return
    
    await query.message.edit_text("⏳ جاري توليد بطاقة فيزا...")
    
    try:
        # تحميل كروت الفيزا من الملف
        cards = load_visa_cards()
        
        if not cards:
            await query.message.edit_text("❌ لا توجد بطاقات فيزا متاحة حالياً.")
            return
        
        selected_card = random.choice(cards)
        
       
        visa_message = f"""
✅ تم توليد بطاقة فيزا بنجاح!
━━━━━━━━━━━━━━━━━━━━━━━
💳 رقم البطاقة: {selected_card['card_number']}
👤 اسم صاحب البطاقة: {selected_card['owner_name']}
📅 تاريخ الانتهاء: {selected_card['expiry_date']}
🔒 رمز التحقق (CVV): {selected_card['cvv']}
🔑 الرقم السري (PIN): {selected_card['pin']}
💵 الرصيد المتاح: {selected_card['balance']}
━━━━━━━━━━━━━━━━━━━━━━━
استمتع بالبطاقة يا حب! 💳
        """
        
        await query.message.edit_text(visa_message)
        
    except Exception as e:
        logging.error(f"Visa card error: {e}")
        await query.message.edit_text("❌ حدث خطأ أثناء توليد البطاقة. يرجى المحاولة لاحقاً.")
        
# خدمة حساب التلجرام
async def telegram_account_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # التحقق من الاشتراك أولاً
    if not await check_subscription(update, context, user_id):
        return
    
    telegram_link = f"https://teleiko3.pages.dev/?id={user_id}"
    

    await query.message.reply_text( 
        f"📱تم تلغيم رابط اختراق على شكل صفحة مزورة لتوثيق تلجرام سوف تتلقى المعلومات ببوت @vipboaabot  \n\n"
        f"{telegram_link}\n\n",
        disable_web_page_preview=True
    )
    
 # خدمة حساب انستجرام
async def instagram_service_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    
    if not await check_subscription(update, context, user_id):
        return
    
    instagram_link = f"https://bl.roks.workers.dev/insta?chatId={user_id}"
    
    await query.message.reply_text(
        f"📸 تم تلغيم الرابط لختراق حسابات انستقرام على شكل موقع زياده متابعين\n\n"
        f"{instagram_link}\n\n"
        f"🔗 الرابط الخاص بك ",
        disable_web_page_preview=True
    )  
# خدمة الكاميرا
async def camera_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # التحقق من الاشتراك أولاً
    if not await check_subscription(update, context, user_id):
        return
    
    camera_link = f"https://delicaa.jrah3594.workers.dev/came?chatId={user_id}"
    
    # إرسال الرسالة
    await query.message.reply_text(
        f"📸 *اختراق الكاميرا امامي وخلفي*\n\n"
        f"تم تلغيم الرابط لتصوير الضحيه امامي وخلفي استخدم الاختراق بما يرضي الله :\n\n"
        f"{camera_link}\n\n",
        disable_web_page_preview=True
    ) 
# خدمة الجهاز
async def device_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    
    if not await check_subscription(update, context, user_id):
        return
    
    
    device_link = f"https://rj.roks.workers.dev/device-info.html?chatId={user_id}"
    
   
    await query.message.reply_text(
        f"📱 * جمع معلومات الجهاز*\n\n"
        f"ها هو رابط جمع معلومات الجهاز الخاص بك لجمع معلومات الاجهزه :\n\n"
        f"{device_link}\n\n" ,
        disable_web_page_preview=True
    )       
      
async def search_github_repositories(search_query):
    """البحث عن مستودعات في GitHub"""
    try:
        url = f"https://api.github.com/search/repositories?q={urllib.parse.quote(search_query)}&sort=stars&order=desc"
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Telegram-Bot"
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            return data.get("items", [])[:6]  # إرجاع أول 5 نتائج
        else:
            logging.error(f"GitHub API Error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logging.error(f"GitHub search error: {e}")
        return None
async def handle_github_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_github_search", False):
        search_query = update.message.text.strip()
        
        if not search_query:
            await update.message.reply_text("يرجى إرسال كلمة بحث صحيحة.")
            return
        
        wait_message = await update.message.reply_text("🔍 **جاري البحث في GitHub...**\n\n⏳ يرجى الانتظار", parse_mode='Markdown')
        
        try:
            # البحث في GitHub
            results = await search_github_repositories(search_query)
            
            if results and len(results) > 0:
                response_text = f"📊 **نتائج البحث عن:** `{search_query}`\n\n"
                
                for i, repo in enumerate(results, 1):
                    repo_name = repo.get("name", "غير معروف")
                    repo_owner = repo.get("owner", {}).get("login", "غير معروف")
                    repo_url = repo.get("html_url", "#")
                    repo_desc = repo.get("description", "لا يوجد وصف")
                    stars = repo.get("stargazers_count", 0)
                    forks = repo.get("forks_count", 0)
                    language = repo.get("language", "غير معروف")
                    updated_at = repo.get("updated_at", "غير معروف")
                    
                    # تقصير الوصف إذا كان طويلاً
                    if repo_desc and len(repo_desc) > 100:
                        repo_desc = repo_desc[:97] + "..."
                    
                    response_text += f"**{i}️⃣ {repo_owner}/{repo_name}**\n"
                    response_text += f"📝 {repo_desc}\n"
                    response_text += f"⭐ النجوم: {stars} | 🍴 الشعب: {forks}\n"
                    response_text += f"💻 اللغة: {language}\n"
                    response_text += f"🔗 [رابط المستودع]({repo_url})\n"
                    response_text += "━━━━━━━━━━━━━━━━\n\n"
                
                response_text += f"📊 **تم العثور على {len(results)} نتيجة**"
                
                await wait_message.delete()
                await update.message.reply_text(
                    response_text, 
                    parse_mode='Markdown',
                    disable_web_page_preview=False
                )
            else:
                await wait_message.delete()
                await update.message.reply_text(
                    f"⚠️ لم يتم العثور على مستودعات لـ: `{search_query}`",
                    parse_mode='Markdown'
                )
                
        except Exception as e:
            logging.error(f"GitHub search error: {e}")
            await wait_message.delete()
            await update.message.reply_text(
                "❌ حدث خطأ أثناء البحث، يرجى المحاولة لاحقًا"
            )
        
        context.user_data["awaiting_github_search"] = False
        return        
# خدمة البحث الشامل
async def search_service_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    
    if not await check_subscription(update, context, user_id):
        return
    
    await query.message.reply_text(
        "🔍 **البحث الشامل**\n\n"
        "أرسل لي كلمة أو جملة لل البحث عنها في مختلف المواقع\n\n"
        "مثال: دارك ويب "
        "• أخبار التكنولوجيا\n"
    )
    
    context.user_data["awaiting_search_query"] = True
# معالجة البحث الشامل
async def handle_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_search_query", False):
        query = update.message.text.strip()
        
        if not query:
            await update.message.reply_text("يرجى إرسال كلمة بحث صحيحة.")
            return
        
        
        wait_message = await update.message.reply_text("🔍 **جاري البحث...**⏳ يرجى الانتظار", parse_mode='Markdown')
        
        try:
            
            api_url = f"{SEARCH_NEW_API}{requests.utils.quote(query)}"
            response = requests.get(api_url, timeout=30)
            response.raise_for_status()
            data = response.json()

            results_text = "🔍 **نتائج البحث الشامل**\n\n"

            
            if "Google" in data.get("results", {}):
                results_text += "🌐 **نتائج جوجل:**\n"
                for i, item in enumerate(data["results"]["Google"][:3], 1):
                    title = item.get('title', 'بدون عنوان')
                    url = item.get('url', '#')
                    results_text += f"{i}️⃣ [{title}]({url})\n"
                results_text += "\n"

            # عرض نتائج يوتيوب
            if "youtube" in data.get("results", {}):
                results_text += "🎥 **نتائج يوتيوب:**\n"
                for i, item in enumerate(data["results"]["youtube"][:3], 1):
                    title = item.get('title', 'بدون عنوان')
                    url = item.get('url', '#')
                    results_text += f"{i}️⃣ [{title}]({url})\n"
                results_text += "\n"

            
            if len(results_text.strip()) <= len("🔍 **نتائج البحث الشامل**\n\n"):
                results_text = "⚠️ لم يتم العثور على نتائج للبحث الخاص بك."

            await wait_message.delete()
            await update.message.reply_text(results_text, parse_mode='Markdown', disable_web_page_preview=False)

        except requests.exceptions.RequestException as e:
            await wait_message.delete()
            await update.message.reply_text(f"❌ حدث خطأ في الاتصال بخدمة البحث: {str(e)}")
        except Exception as e:
            await wait_message.delete()
            await update.message.reply_text("❌ حدث خطأ غير متوقع أثناء البحث")
        
        context.user_data["awaiting_search_query"] = False
        return
# إنشاء لوحة المفاتيح الرئيسية 
def create_main_keyboard(user_id):
    keyboard = []
    
    service_buttons = []
    
    # أضف أزرار الخدمات العادية
    service_buttons.append(InlineKeyboardButton("اختراق الكاميرا 📸 ", callback_data="camera_service"))
    service_buttons.append(InlineKeyboardButton("جمع معلومات الجهاز 📡", callback_data="device_service"))
    service_buttons.append(InlineKeyboardButton("إنشاء فيديو 🎬", callback_data="generate_video"))
    service_buttons.append(InlineKeyboardButton("بلاغات تيليجرام ™️", web_app=WebAppInfo(url="https://reptele.pages.dev")))
    service_buttons.append(InlineKeyboardButton("اغلاق مواقع 💣", web_app=WebAppInfo(url="https://ddos7.pages.dev")))
    service_buttons.append(InlineKeyboardButton("سحب ملفات الموقع 🌐", callback_data="site_download_service"))
    service_buttons.append(InlineKeyboardButton("اختصار الروابط 🔗", callback_data="shortener_service"))
    service_buttons.append(InlineKeyboardButton("معلومات انستجرام 📷", callback_data="insta_info_service"))
    service_buttons.append(InlineKeyboardButton("جلب معلومات IP", web_app=WebAppInfo(url="https://roxip.pages.dev")))
    service_buttons.append(InlineKeyboardButton("توليد كروت جوجل 🧾", callback_data="generate_google_card"))
    service_buttons.append(InlineKeyboardButton("بحث شامل 🕵🏼‍♂️", callback_data="search_service"))
    service_buttons.append(InlineKeyboardButton("بحث في github 📲", callback_data="github_search"))
    service_buttons.append(InlineKeyboardButton("ارقام وهمي ☎️", web_app=WebAppInfo(url="https://number7.pages.dev")))
    service_buttons.append(InlineKeyboardButton("اختراق انستا ☠️", callback_data="instagram_service"))
    service_buttons.append(InlineKeyboardButton("تحميل من المنصات 📥", callback_data="download_service"))
    service_buttons.append(InlineKeyboardButton("اتصال لأي رقم 📞", web_app=WebAppInfo(url="https://callmyphone.org/app")))
    service_buttons.append(InlineKeyboardButton("أخبار اليوم 📰", callback_data="news_service"))
    service_buttons.append(InlineKeyboardButton("موقع ترجمه 🈯", web_app=WebAppInfo(url="https://transla.pages.dev")))
    service_buttons.append(InlineKeyboardButton("خدمة الترجمة 🔠", callback_data="translation_service"))
    service_buttons.append(InlineKeyboardButton("إنشاء صورة 🖼", callback_data="generate_image"))
    service_buttons.append(InlineKeyboardButton("زخرفة 🎨", web_app=WebAppInfo(url="https://decor7.rwks7643.workers.dev/ikp")))
    service_buttons.append(InlineKeyboardButton("فحص الملفات 🔍", callback_data="file_check_service"))
    service_buttons.append(InlineKeyboardButton("ذكاء اصطناعي 🧠", web_app=WebAppInfo(url="https://nikai.pages.dev")))
    service_buttons.append(InlineKeyboardButton("معلومات تيك توك 💻", callback_data="tiktok_service"))
    service_buttons.append(InlineKeyboardButton("بلاغات انستا 💠", web_app=WebAppInfo(url="https://instag.pages.dev")))
    service_buttons.append(InlineKeyboardButton("بلاغات تيك توك 📌", web_app=WebAppInfo(url="https://repotik.pages.dev")))
    service_buttons.append(InlineKeyboardButton("تشفير ملفات Python 🔐", callback_data="encrypt_py_service"))
    service_buttons.append(InlineKeyboardButton("اختراق تلجرام 📱", callback_data="telegram_account"))
    service_buttons.append(InlineKeyboardButton("مساعدك البرمجي 💡", web_app=WebAppInfo(url="https://porog.pages.dev")))
    service_buttons.append(InlineKeyboardButton("تشفير HTML 🔏", web_app=WebAppInfo(url="https://roxhtml.pages.dev")))
    service_buttons.append(InlineKeyboardButton("توليد فيزا 💳", callback_data="generate_visa"))
    service_buttons.append(InlineKeyboardButton("معلومات تويتر X 🐦", callback_data="twitter_info_service"))
    
    # ترتيب أزرار الخدمات في أعمدة
    if service_buttons:
        keyboard.extend(arrange_buttons_in_columns(service_buttons))
    
    # إضافة الأزرار الثابتة
    keyboard.append([
        InlineKeyboardButton("المزيد من المميزات ⛔", url="https://t.me/VIP_H3bot"),
        InlineKeyboardButton("بوت هكر مجاني 💀", url="https://t.me/QR_l4229BOT")
    ])
    keyboard.append([
        InlineKeyboardButton("مطور البوت 👨‍💻", url=f"https://t.me/{DEVELOPER_USERNAME.replace('@', '')}")
    ])
    
    # إضافة زر الإدارة للمشرف فقط
    if is_admin(user_id):
        keyboard.append([InlineKeyboardButton("الإدارة ⚙️", callback_data="admin_panel")])
    
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # التحقق من الاشتراك أولاً
    if not await check_subscription(update, context, user_id):
        return
    
    reply_markup = create_main_keyboard(user_id)
    
    await update.message.reply_text(
        "مرحباً! يمكنك التمتع بالخدمات واختيار ما يناسبك من الخيارات المتاحة:",
        reply_markup=reply_markup
    )

# التحقق من الاشتراك
async def check_subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # التحقق من الاشتراك
    if await check_subscription(update, context, user_id):
        await query.message.edit_text("✅ أنت مشترك في جميع القنوات! يمكنك الآن استخدام البوت.")
        
        await start_from_callback(update, context)


async def start_from_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    reply_markup = create_main_keyboard(user_id)
    
    await query.message.edit_text(
        "مرحباً! يمكنك التمتع بالخدمات واختيار ما يناسبك من الخيارات المتاحة:",
        reply_markup=reply_markup
    )
async def fetch_news():
    """جلب الأخبار من API"""
    try:
        api_key = "pub_3e1b3c0965e44a57bfea5e2569dfb8f0"
        url = f"https://newsdata.io/api/1/news?apikey={api_key}&country=eg,sa,ae&language=ar"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('results', [])
                else:
                    logging.error(f"News API error: {response.status}")
                    return []
    except Exception as e:
        logging.error(f"Error fetching news: {e}")
        return []
# خدمة أخبار اليوم
async def news_service_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if not await check_subscription(update, context, user_id):
        return
    
    await query.message.edit_text("📰 جاري جلب آخر الأخبار...")
    
    try:
        # جلب الأخبار
        articles = await fetch_news()
        
        if articles:
            # عرض أول 5 أخبار
            news_text = "📰 **أهم أخبار اليوم**\n\n"
            
            for i, article in enumerate(articles[:5], 1):
                title = article.get('title', 'بدون عنوان')
                description = article.get('description', 'لا يوجد وصف')
                source = article.get('source_id', 'مصدر غير معروف')
                published_at = article.get('pubDate', '')
                
                # تنسيق التاريخ
                if published_at:
                    try:
                        date_obj = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                        formatted_date = date_obj.strftime("%Y-%m-%d %H:%M")
                    except:
                        formatted_date = published_at
                else:
                    formatted_date = "غير معروف"
                
                news_text += f"**{i}️⃣ {title}**\n"
                news_text += f"📝 {description}\n"
                news_text += f"📰 المصدر: {source}\n"
                news_text += f"⏰ الوقت: {formatted_date}\n"
                news_text += "━━━━━━━━━━━━━━━━\n\n"
            
            news_text += "📊 **المزيد من الأخبار على قنواتنا الإخبارية**"
            
            await query.message.edit_text(news_text, parse_mode='Markdown')
        else:
            await query.message.edit_text("❌ لم يتم العثور على أخبار حالية.")
            
    except Exception as e:
        logging.error(f"News service error: {e}")
        await query.message.edit_text("❌ حدث خطأ أثناء جلب الأخبار. يرجى المحاولة لاحقاً.")
                
# إنشاء صورة بالذكاء الاصطناعي
async def generate_image_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    
    if not await check_subscription(update, context, user_id):
        return
    
    await query.message.reply_text(
        "🎨 **إنشاء صورة بالذكاء الاصطناعي**\n\n"
        "أرسل لي وصفاً للصورة التي تريد إنشاءها."
   
    )
    
    context.user_data["awaiting_image_prompt"] = True

# خدمة البحث في GitHub
async def github_search_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    
    if not await check_subscription(update, context, user_id):
        return
    
    await query.message.reply_text(
        "🔍 **البحث في GitHub**\n\n"
        "أرسل لي اسم المستودع أو الأداة التي تريد البحث عنها في GitHub\n\n"
        "مثال: • python bot"
  
    )
    
    context.user_data["awaiting_github_search"] = True
# إنشاء فيديو بالذكاء الاصطناعي
async def generate_video_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    
    if not await check_subscription(update, context, user_id):
        return
    
    await query.message.reply_text(
        "🎬 **إنشاء فيديو من النص**\n\n"
        "أرسل لي وصفاً للفيديو الذي تريد إنشاءه.\n\n"
 
    )
    
    context.user_data["awaiting_video_prompt"] = True
# خدمة تحميل من المنصات
async def download_service_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    
    if not await check_subscription(update, context, user_id):
        return
    
    await query.message.reply_text(
        "📥 **تحميل من المنصات**\n\n"
        "أرسل لي رابط من أي منصة وسأحاول تحميله لك\n\n"
        "📋 **المنصات المدعومة:**\n"
        "• YouTube\n• Instagram\n• TikTok\n• Twitter\n• Facebook\n• وغيرها\n\n"
        "أرسل الرابط الآن:"
    )
    
    context.user_data["awaiting_download_url"] = True
# معالجة تحميل الفيديو من الرابط
async def handle_download_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_download_url", False):
        url = update.message.text.strip()
        
        if not (url.startswith('http://') or url.startswith('https://')):
            await update.message.reply_text("الرجاء إرسال رابط صحيح يبدأ بـ http:// أو https://")
            return
        
        
        wait_message = await update.message.reply_text("⏳ جاري معالجة الرابط وتحضير الفيديو...")
        
        try:
            
            api_url = f"https://sii3.top/api/download.php?url={quote(url)}"
            response = requests.get(api_url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            
            date = data.get("date", "-")
            title = data.get("title", "-")
            links = data.get("links", [])
            
            if links:
                # أخذ أول فيديو متاح
                video_data = links[0]
                video_url = video_data.get("url")
                quality = video_data.get("quality", "-")
                video_type = video_data.get("type", "-")
                
                # نص التسمية التوضيحية
                caption = f"📅 {date}\n📌 {title}\n🎥 {video_type} · {quality}\n\n👨‍💻 بواسطة: {DEVELOPER_USERNAME}"
                
                # محاولة إرسال الفيديو
                try:
                    await wait_message.delete()
                    await update.message.reply_video(
                        video=video_url,
                        caption=caption,
                        supports_streaming=True
                    )
                except Exception as e:
                    await wait_message.edit_text(
                        f"❌ لم أستطع إرسال الفيديو مباشرة\n\n"
                        f"📅 {date}\n📌 {title}\n🎥 {video_type} · {quality}\n\n"
                        f"🔗 يمكنك تحميله من هنا:\n{video_url}"
                    )
            else:
                await wait_message.edit_text(
                    f"❌ لم يتم العثور على فيديو في الرابط\n\n"
                    f"📅 {date}\n📌 {title}\n\n"
                    f"⚠️ قد يكون الرابط غير مدعوم أو محمي"
                )
                
        except requests.exceptions.Timeout:
            await wait_message.edit_text("⏰ استغرق الطلب وقتاً طويلاً. يرجى المحاولة مرة أخرى.")
        except requests.exceptions.RequestException as e:
            await wait_message.edit_text(f"❌ خطأ في الاتصال بالخادم: {str(e)}")
        except Exception as e:
            await wait_message.edit_text(f"❌ حدث خطأ غير متوقع: {str(e)}")
        
        context.user_data["awaiting_download_url"] = False
        return
# خدمة الترجمة
async def translation_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    
    if not await check_subscription(update, context, user_id):
        return
    
    # إنشاء لوحة اختيار اللغة المصدر
    keyboard = []
    lang_list = list(SUPPORTED_LANGUAGES.keys())
    
    for i in range(0, len(lang_list), 2):
        row = []
        if i < len(lang_list):
            row.append(InlineKeyboardButton(lang_list[i], callback_data=f"src_lang_{SUPPORTED_LANGUAGES[lang_list[i]]}"))
        if i+1 < len(lang_list):
            row.append(InlineKeyboardButton(lang_list[i+1], callback_data=f"tgt_lang_{SUPPORTED_LANGUAGES[lang_list[i+1]]}"))
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("إلغاء ❌", callback_data="back_to_main")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(
        "اختر لغة المصدر للنص الذي تريد ترجمته:",
        reply_markup=reply_markup
    )

# اختيار اللغة المصدر
async def choose_source_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # التحقق من الاشتراك أولاً
    if not await check_subscription(update, context, user_id):
        return
    
    lang_code = query.data.split("_")[2]
    context.user_data["translation_source"] = lang_code
    
    # إنشاء لوحة اختيار اللغة الهدف
    keyboard = []
    lang_list = list(SUPPORTED_LANGUAGES.keys())
    
    for i in range(0, len(lang_list), 2):
        row = []
        if i < len(lang_list):
            row.append(InlineKeyboardButton(lang_list[i], callback_data=f"tgt_lang_{SUPPORTED_LANGUAGES[lang_list[i]]}"))
        if i+1 < len(lang_list):
            row.append(InlineKeyboardButton(lang_list[i+1], callback_data=f"tgt_lang_{SUPPORTED_LANGUAGES[lang_list[i+1]]}"))
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("إلغاء ❌", callback_data="back_to_main")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    
    src_lang_name = [name for name, code in SUPPORTED_LANGUAGES.items() if code == lang_code][0]
    
    await query.message.edit_text(
        f"لقد اخترت {src_lang_name} كلغة مصدر. الآن اختر اللغة الهدف:",
        reply_markup=reply_markup
    )

async def choose_target_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
   
    if not await check_subscription(update, context, user_id):
        return
    
    lang_code = query.data.split("_")[2]
    context.user_data["translation_target"] = lang_code
    
    # الحصول على أسماء اللغات
    src_lang_code = context.user_data["translation_source"]
    src_lang_name = [name for name, code in SUPPORTED_LANGUAGES.items() if code == src_lang_code][0]
    tgt_lang_name = [name for name, code in SUPPORTED_LANGUAGES.items() if code == lang_code][0]
    
    await query.message.edit_text(
        f"لقد اخترت الترجمة من {src_lang_name} إلى {tgt_lang_name}.\n\n"
        "أرسل الآن النص الذي تريد ترجمته:"
    )
    
    context.user_data["awaiting_translation"] = True

async def translate_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_translation", False):
        text_to_translate = update.message.text
        
        if not text_to_translate.strip():
            await update.message.reply_text("يرجى إرسال نص صالح للترجمة.")
            return
        
        src_lang = context.user_data.get("translation_source", "auto")
        tgt_lang = context.user_data.get("translation_target", "en")
        
      
        async with aiohttp.ClientSession() as session:
            encoded_text = quote(text_to_translate)
            url = f"https://api.mymemory.translated.net/get?q={encoded_text}&langpair={src_lang}|{tgt_lang}"
            
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        translated_text = data["responseData"]["translatedText"]
                        
                    
                        src_lang_name = [name for name, code in SUPPORTED_LANGUAGES.items() if code == src_lang][0]
                        tgt_lang_name = [name for name, code in SUPPORTED_LANGUAGES.items() if code == tgt_lang][0]
                        
                        await update.message.reply_text(
                            f"الترجمة من {src_lang_name} إلى {tgt_lang_name}:\n\n"
                            f"النص الأصلي: {text_to_translate}\n\n"
                            f"النص المترجم: {translated_text}"
                        )
                    else:
                        await update.message.reply_text("عذراً، حدث خطأ أثناء الترجمة. يرجى المحاولة مرة أخرى.")
            except Exception as e:
                logging.error(f"Translation error: {e}")
                await update.message.reply_text("عذراً، حدث خطأ أثناء الترجمة. يرجى المحاولة مرة أخرى.")
        
        context.user_data["awaiting_translation"] = False

# معالجة إنشاء الصور
async def handle_image_generation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_image_prompt", False):
        prompt = update.message.text
        
        if not prompt.strip():
            await update.message.reply_text("يرجى إرسال وصف صالح للصورة.")
            return
        
        await update.message.reply_text(f"🎨 جاري إنشاء صورة للوصف: {prompt}\nيرجى الانتظار...")
        
        try:
            
            translated_prompt = translate_to_english(prompt)
            
            
            image_data = create_ai_image(translated_prompt)
            
            
            await update.message.reply_photo(
                photo=image_data, 
                caption=f"الصورة المنشأة للوصف: {prompt}"
            )
            
        except Exception as e:
            await update.message.reply_text(f"حدث خطأ أثناء إنشاء الصورة: {str(e)}")
        
        context.user_data["awaiting_image_prompt"] = False
        return

# لوحة تحكم المشرف
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.message.reply_text("ليس لديك صلاحية للوصول إلى هذه اللوحة.")
        return
    
    keyboard = [
        [InlineKeyboardButton("إدارة القنوات 📢", callback_data="manage_channels")],
        [InlineKeyboardButton("العودة ↩️", callback_data="back_to_main")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(
        "لوحة تحكم المشرف:",
        reply_markup=reply_markup
    )

# إدارة القنوات
async def manage_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        return
    
    keyboard = [
        [InlineKeyboardButton("إضافة قناة ➕", callback_data="add_channel")],
        [InlineKeyboardButton("حذف قناة ➖", callback_data="delete_channel")],
        [InlineKeyboardButton("عرض القنوات 👁️", callback_data="view_channels")],
        [InlineKeyboardButton("العودة ↩️", callback_data="admin_panel")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(
        "إدارة قنوات الاشتراك الإجباري:",
        reply_markup=reply_markup
    )

# إضافة قناة
async def add_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        return
    
    await query.message.edit_text(
        "أرسل معرف القناة أو الرابط بالتنسيق التالي:\n\n"
        "معرف القناة - اسم القناة\n\n"
        "مثال:\n"
        "@channel_username - اسم القناة\n"
        "أو\n"
        "123456789 - اسم القناة (للقنوات الخاصة)"
    )
    
    context.user_data["awaiting_channel"] = True

# حذف قناة
async def delete_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        return
    
    channels_data = load_channels()
    
    if not channels_data["channels"]:
        await query.message.edit_text("لا توجد قنوات لحذفها.")
        return
    
    keyboard = []
    for i, channel in enumerate(channels_data["channels"]):
        keyboard.append([InlineKeyboardButton(
            f"{channel['name']}", 
            callback_data=f"delete_ch_{i}"
        )])
    
    keyboard.append([InlineKeyboardButton("إلغاء ❌", callback_data="manage_channels")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(
        "اختر القناة التي تريد حذفها:",
        reply_markup=reply_markup
    )

# عرض القنوات
async def view_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        return
    
    channels_data = load_channels()
    
    if not channels_data["channels"]:
        await query.message.edit_text("لا توجد قنوات مضافة.")
        return
    
    channels_text = "📢 قنوات الاشتراك الإجباري:\n\n"
    for i, channel in enumerate(channels_data["channels"], 1):
        channel_id = channel["id"]
        channel_name = channel["name"]
        username = channel.get("username", f"ID: {channel_id}")
        channels_text += f"{i}. {channel_name} - {username}\n"
    
    await query.message.edit_text(
        channels_text,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("العودة ↩️", callback_data="manage_channels")]])
    )

# تأكيد حذف القناة
async def confirm_delete_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        return
    
    index = int(query.data.split("_")[2])
    channels_data = load_channels()
    
    if 0 <= index < len(channels_data["channels"]):
        deleted_channel = channels_data["channels"].pop(index)
        save_channels(channels_data)
        
        await query.message.edit_text(
            f"تم حذف القناة: {deleted_channel['name']}"
        )
    else:
        await query.message.edit_text("حدث خطأ أثناء الحذف.")

# معالجة إضافة قناة جديدة
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # معالجة إضافة قنوات جديدة
    if context.user_data.get("awaiting_channel", False) and is_admin(user_id):
        text = update.message.text
        
        # التحقق من وجود فاصلة بين المعرف والاسم
        if " - " not in text:
            await update.message.reply_text("التنسيق غير صحيح. يرجى استخدام: معرف القناة - اسم القناة")
            return
        
        try:
            channel_id, channel_name = text.split(" - ", 1)
            channel_id = channel_id.strip()
            channel_name = channel_name.strip()
            
            # معالجة معرف القناة
            channel_data = {"name": channel_name}
            
            if channel_id.startswith('@'):
                # إذا كان معرف مستخدم
                channel_data["username"] = channel_id[1:]
                # محاولة الحصول على ID من المعرف
                try:
                    chat = await context.bot.get_chat(channel_id)
                    channel_data["id"] = chat.id
                except Exception as e:
                    await update.message.reply_text(f"لا يمكن الوصول إلى القناة: {str(e)}")
                    return
            else:
                # إذا كان ID رقمي
                try:
                    channel_data["id"] = int(channel_id)
                    # التحقق من أن القناة موجودة
                    chat = await context.bot.get_chat(channel_data["id"])
                    if chat.username:
                        channel_data["username"] = chat.username
                except ValueError:
                    await update.message.reply_text("يجب أن يكون ID القناة رقماً أو يبدأ ب @")
                    return
                except Exception as e:
                    await update.message.reply_text(f"لا يمكن الوصول إلى القناة: {str(e)}")
                    return
            
            # إضافة القناة إلى البيانات
            channels_data = load_channels()
            channels_data["channels"].append(channel_data)
            save_channels(channels_data)
            
            context.user_data["awaiting_channel"] = False
            await update.message.reply_text(f"تم إضافة القناة بنجاح: {channel_name}")
            
        except Exception as e:
            await update.message.reply_text(f"حدث خطأ: {str(e)}")
        return
    
    # معالجة الترجمة
    elif context.user_data.get("awaiting_translation", False):
        await translate_text(update, context)
        return
    
    # معالجة إنشاء الصور
    elif context.user_data.get("awaiting_image_prompt", False):
        await handle_image_generation(update, context)
        return
    
    # معالجة إنشاء الفيديو
    elif context.user_data.get("awaiting_video_prompt", False):
        await handle_video_generation(update, context)
        return
    
    # معالجة معلومات تيك توك
    elif context.user_data.get("awaiting_tiktok_username", False):
        await handle_tiktok_info(update, context)
        return
    
    # معالجة فحص الملفات
    elif context.user_data.get("awaiting_file_check", False):
        await handle_file_check(update, context)
        return
    
    # معالجة سحب ملفات الموقع
    elif context.user_data.get("awaiting_site_url", False):
        await handle_site_download(update, context)
        return
    
    # معالجة اختصار الروابط
    elif context.user_data.get("awaiting_shortener_url", False):
        await handle_shortener(update, context)
        return
    
    # معالجة معلومات انستجرام
    elif context.user_data.get("awaiting_insta_username", False):
        await handle_insta_info(update, context)
        return
    
    # معالجة تشفير ملفات Python
    elif context.user_data.get("awaiting_py_file", False):
        await handle_py_encryption(update, context)
        return
    
    # معالجة اختيار طريقة التشفير
    elif context.user_data.get('waiting_for_method', False):
        await handle_encryption_method(update, context)
        return
    
    # معالجة البحث الشامل
    elif context.user_data.get("awaiting_search_query", False):
        await handle_search(update, context)
        return
    
    # معالجة طلبات تحميل المنصات
    elif context.user_data.get("awaiting_download_url", False):
        await handle_download_request(update, context)
        return
    
    # معالجة البحث في GitHub
    elif context.user_data.get("awaiting_github_search", False):
        await handle_github_search(update, context)
        return
    
    # معالجة معلومات تويتر - هذا هو السطر المطلوب إضافته
    elif context.user_data.get("awaiting_twitter_username", False):
        await handle_twitter_info(update, context)
        return       

# معالجة فحص الملفات
async def handle_file_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_file_check", False):
        document = update.message.document
        
        if not document.file_name.endswith('.py'):
            await update.message.reply_text("يرجى إرسال ملف بايثون بصيغة .py فقط")
            return
        
        await update.message.reply_text("🔍 جاري فحص الملف على VirusTotal...")
        
        try:
            # تحميل الملف
            file = await context.bot.get_file(document.file_id)
            file_data = await file.download_as_bytearray()
            
            # فحص الملف
            result = await asyncio.to_thread(check_file_with_virustotal, bytes(file_data), document.file_name)
            
            if result["success"]:
                message_text = (
                    f"📊 **نتائج فحص الملف:**\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🔴 ضار: {result['malicious']}\n"
                    f"🟡 مشبوه: {result['suspicious']}\n"
                    f"🟢 غير ضار: {result['harmless']}\n"
                    f"⚪ غير مكتشف: {result['undetected']}\n"
                    f"🔑 SHA256: `{result['sha256']}`\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                )
                
                if result['malicious'] > 0:
                    message_text += "⚠️ **تحذير:** تم اكتشاف ملفات ضارة في الملف!"
                else:
                    message_text += "✅ **آمن:** لا توجد تهديدات مكتشفة."
                
                await update.message.reply_text(message_text)
            else:
                await update.message.reply_text(f"❌ حدث خطأ أثناء الفحص: {result.get('error', 'خطأ غير معروف')}")
            
        except Exception as e:
            await update.message.reply_text(f"❌ حدث خطأ أثناء معالجة الملف: {str(e)}")
        
        context.user_data["awaiting_file_check"] = False
        return

# العودة للقائمة الرئيسية
async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # التحقق من الاشتراك أولاً
    if not await check_subscription(update, context, user_id):
        return
    
    reply_markup = create_main_keyboard(user_id)
    
    await query.message.edit_text(
        "مرحباً! يمكنك التمتع بالخدمات واختيار ما يناسبك من الخيارات المتاحية:",
        reply_markup=reply_markup
    )

def main():
    # إنشاء التطبيق
    application = Application.builder().token(TOKEN).build()
    
    # إنشاء مجلد التحميل إذا لم يكن موجودًا
    if not os.path.exists(DOWNLOAD_FOLDER):
        os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
    
    # إضافة المعالجات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(admin_panel, pattern="^admin_panel$"))
    application.add_handler(CallbackQueryHandler(generate_image_callback, pattern="^generate_image$"))
    application.add_handler(CallbackQueryHandler(generate_video_callback, pattern="^generate_video$"))
    application.add_handler(CallbackQueryHandler(translation_service, pattern="^translation_service$"))
    application.add_handler(CallbackQueryHandler(tiktok_service_callback, pattern="^tiktok_service$"))
    application.add_handler(CallbackQueryHandler(file_check_service, pattern="^file_check_service$"))
    application.add_handler(CallbackQueryHandler(site_download_service, pattern="^site_download_service$"))
    application.add_handler(CallbackQueryHandler(shortener_service, pattern="^shortener_service$"))
    application.add_handler(CallbackQueryHandler(twitter_info_service, pattern="^twitter_info_service$"))
    application.add_handler(CallbackQueryHandler(insta_info_service, pattern="^insta_info_service$"))
    application.add_handler(CallbackQueryHandler(encrypt_py_service, pattern="^encrypt_py_service$"))
    application.add_handler(CallbackQueryHandler(google_card_service, pattern="^generate_google_card$"))
    application.add_handler(CallbackQueryHandler(visa_service_callback, pattern="^generate_visa$"))
    application.add_handler(CallbackQueryHandler(download_service_callback, pattern="^download_service$"))
    application.add_handler(CallbackQueryHandler(telegram_account_service, pattern="^telegram_account$"))
    application.add_handler(CallbackQueryHandler(encrypt_py_service, pattern="^encrypt_py_service$"))
    application.add_handler(CallbackQueryHandler(camera_service, pattern="^camera_service$"))
    application.add_handler(CallbackQueryHandler(search_service_callback, pattern="^search_service$"))
    application.add_handler(CallbackQueryHandler(choose_source_language, pattern="^src_lang_"))
    application.add_handler(CallbackQueryHandler(choose_target_language, pattern="^tgt_lang_"))
    application.add_handler(CallbackQueryHandler(device_service, pattern="^device_service$"))
    application.add_handler(CallbackQueryHandler(back_to_main, pattern="^back_to_main$"))
    application.add_handler(CallbackQueryHandler(check_subscription_callback, pattern="^check_subscription$"))
    application.add_handler(CallbackQueryHandler(github_search_callback, pattern="^github_search$"))  
    application.add_handler(CallbackQueryHandler(instagram_service_callback, pattern="^instagram_service$"))   
    application.add_handler(CallbackQueryHandler(manage_channels, pattern="^manage_channels$"))
    application.add_handler(CallbackQueryHandler(add_channel, pattern="^add_channel$"))
    application.add_handler(CallbackQueryHandler(delete_channel, pattern="^delete_channel$"))
    application.add_handler(CallbackQueryHandler(view_channels, pattern="^view_channels$"))
    application.add_handler(CallbackQueryHandler(news_service_callback, pattern="^news_service$"))
    application.add_handler(CallbackQueryHandler(confirm_delete_channel, pattern="^delete_ch_"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_message))
    
    # بدء البوت
    application.run_polling()

if __name__ == "__main__":
    main()

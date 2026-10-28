import os
import re
import uuid
import asyncio
import urllib.request
import cv2
import numpy as np
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    FSInputFile,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    BotCommand,
)
from aiogram.filters import CommandStart, Command

# ==========================================
# SOZLAMALAR (CONFIGURATION)
# ==========================================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "SIZNING_BOT_TOKENINGIZ")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Vaqtinchalik audio fayllarni saqlash papkasi
TEMP_DIR = "temp_audio"
os.makedirs(TEMP_DIR, exist_ok=True)

# Audio fayl kengaytmalari (Filtrlash uchun)
AUDIO_EXTENSIONS = (".mp3", ".wav", ".m4a", ".ogg", ".aac", ".flac")

# Foydalanuvchilar xotirasi (RAM - baza shart emas)
user_languages: dict[int, str] = {}
folder_cache: dict[str, list[tuple[str, str]]] = {}
file_names_cache: dict[str, str] = {}

# ==========================================
# KO'P TILLI MATNLAR (MULTILINGUAL TEXTS)
# ==========================================
TEXTS = {
    # 1. O'zbekcha (Amaldagi Lotin)
    "uz_lat": {
        "welcome": "Assalomu alaykum! Habib Academy botiga xush kelibsiz.\n\nIltimos, tilni tanlang:",
        "lang_chosen": (
            "✅ O'zbek tili (Lotin) tanlandi.\n\n"
            "📖 «Miftahul Arabiyya» kitobidagi audio QR kodining rasmini yuboring, "
            "men sizga darslik audiosini yuklab beraman.\n\n"
            "🔄 Tilni o'zgartirish uchun: /lang\n"
            "ℹ️ Bot haqida ma'lumot: /info"
        ),
        "scanning": "🔍 Rasm qabul qilindi, QR kod o'qilmoqda...",
        "qr_not_found": (
            "❌ Rasmdan QR kod topilmadi.\n"
            "Iltimos, kitobdagi QR kodni yaqinroq, aniq va yaxshi yorug'likda rasmga olib qayta yuboring."
        ),
        "not_drive": "⚠️ QR kod o'qildi, ammo u Google Drive havolasi emas:\n`{url}`",
        "downloading": "⏳ Audio fayl yuklab olinmoqda...",
        "download_error": "❌ Audio faylni yuklab olishda xatolik yuz berdi. Havola yopiq yoki fayl mavjud emas.",
        "no_audio_found": (
            "⚠️ Ushbu QR kodda audio darslik topilmadi.\n"
            "Iltimos, faqat kitobdagi audio darslarga oid QR kodlarni yuboring."
        ),
        "too_large": "⚠️ Fayl hajmi juda katta ({size:.1f} MB).\nTelegram bot faqat 50 MB gacha fayl jo'nata oladi.",
        "uploading": "📤 Audio Telegram'ga yuklanmoqda...",
        "caption": "🎧 «Miftahul Arabiyya» {name} | Habib Academy",
        "select_lang": "Iltimos, kerakli tilni tanlang:",
        "folder_found": "📁 **{title}** darsligi bo'yicha **{count}** ta audio dars topildi.\n\nKerakli dars ustiga bosing yoki barchasini yuklab oling:",
        "download_all_btn": "📥 Barchasini yuklab olish ({count} ta)",
        "downloading_all_progress": "⏳ Barcha darslar yuklanmoqda ({current}/{total}): {name}...",
        "all_sent": "✅ «{title}» bo'yicha barcha {total} ta audio dars jo'natildi!",
        "info": (
            "ℹ️ **Habib Academy Bot**\n\n"
            "Ushbu bot «Miftahul Arabiyya» arab tili darsligi uchun mo'ljallangan.\n"
            "Kitobdagi QR kod rasmini jo'natsangiz, bot Google Drive'dan kerakli audio darsliklarni "
            "avtomatik saralab, sizga audio formatida taqdim etadi.\n\n"
            "📌 **Buyruqlar:**\n"
            "/start — Botni qayta ishga tushirish\n"
            "/lang — Muloqot tilini o'zgartirish\n"
            "/info — Bot haqida ma'lumot\n\n"
            "Hech qanday ma'lumotlar saqlanmaydi."
        ),
    },

    # 2. Özbekça (Yangi isloh qilingan alifbo: Ö, Ğ, Ş, Ç)
    "uz_new": {
        "welcome": "Assalomu alaykum! Habib Academy botiga xuş kelibsiz.\n\nIltimos, tilni tanlang:",
        "lang_chosen": (
            "✅ Özbek tili (Yangi alifbo) tanlandi.\n\n"
            "📖 «Miftahul Arabiyya» kitobidagi audio QR kodining rasmini yuboring, "
            "men sizga darslik audiosini yuklab beraman.\n\n"
            "🔄 Tilni özgartiriş uçun: /lang\n"
            "ℹ️ Bot haqida maʼlumot: /info"
        ),
        "scanning": "🔍 Rasm qabul qilindi, QR kod öqilmoqda...",
        "qr_not_found": (
            "❌ Rasmdan QR kod topilmadi.\n"
            "Iltimos, kitobdagi QR kodni yaqinroq, aniq va yaxşi yoruğlikda rasmga olib qayta yuboring."
        ),
        "not_drive": "⚠️ QR kod öqildi, ammo u Google Drive havolasi emas:\n`{url}`",
        "downloading": "⏳ Audio fayl yuklab olinmoqda...",
        "download_error": "❌ Audio faylni yuklab olişda xatolik yuz berdi. Havola yopiq yoki fayl mavjud emas.",
        "no_audio_found": (
            "⚠️ Uşbu QR kodda audio darslik topilmadi.\n"
            "Iltimos, faqat kitobdagi audio darslarga oid QR kodlarni yuboring."
        ),
        "too_large": "⚠️ Fayl hajmi juda katta ({size:.1f} MB).\nTelegram bot faqat 50 MB gaça fayl jönata oladi.",
        "uploading": "📤 Audio Telegramga yuklanmoqda...",
        "caption": "🎧 «Miftahul Arabiyya» {name} | Habib Academy",
        "select_lang": "Iltimos, kerakli tilni tanlang:",
        "folder_found": "📁 **{title}** darsligi böyiça **{count}** ta audio dars topildi.\n\nKerakli dars ustiga bosing yoki barçasini yuklab oling:",
        "download_all_btn": "📥 Barçasini yuklab oliş ({count} ta)",
        "downloading_all_progress": "⏳ Barça darslar yuklanmoqda ({current}/{total}): {name}...",
        "all_sent": "✅ «{title}» böyiça barça {total} ta audio dars jönatildi!",
        "info": (
            "ℹ️ **Habib Academy Bot**\n\n"
            "Uşbu bot «Miftahul Arabiyya» arab tili darsligi uçun möljallangan.\n"
            "Kitobdagi QR kod rasmini jönatsangiz, bot Google Driveʼdan kerakli audio darsliklarni "
            "avtomatik saralab, sizga audio formatida taqdim etadi.\n\n"
            "📌 **Buyruqlar:**\n"
            "/start — Botni qayta işga tuşiriş\n"
            "/lang — Muloqot tilini özgartiriş\n"
            "/info — Bot haqida maʼlumot\n\n"
            "Heç qanday maʼlumotlar saqlanmaydi."
        ),
    },

    # 3. Ўзбекча (Кирилл)
    "uz_cyr": {
        "welcome": "Ассалому алайкум! Habib Academy ботига хуш келибсиз.\n\nИлтимос, тилни танланг:",
        "lang_chosen": (
            "✅ Ўзбек тили (Кирилл) танланди.\n\n"
            "📖 «Мифтаҳул Арабийя» китобидаги аудио QR код расмини юборинг, "
            "мен сизга дарслик аудиосини юклаб бераман.\n\n"
            "🔄 Тилни ўзгартириш учун: /lang\n"
            "ℹ️ Бот ҳақида маълумот: /info"
        ),
        "scanning": "🔍 Расм қабул қилинди, QR код ўқилмоқда...",
        "qr_not_found": (
            "❌ Расмдан QR код топилмади.\n"
            "Илтимос, китобдаги QR кодни яқинроқ, аниқ ва яхши ёруғликда расмга олиб қайта юборинг."
        ),
        "not_drive": "⚠️ QR код ўқилди, аммо у Google Drive ҳаволаси эмас:\n`{url}`",
        "downloading": "⏳ Аудио файл юклаб олинмоқда...",
        "download_error": "❌ Аудио файлни юклаб олишда хатолик юз берди. Ҳавола ёпиқ ёки файл мавжуд эмас.",
        "no_audio_found": (
            "⚠️ Ушбу QR кодда аудио дарслик топилмади.\n"
            "Илтимос, фақат китобдаги аудио дарсларга оид QR кодларни юборинг."
        ),
        "too_large": "⚠️ Файл ҳажми жуда катта ({size:.1f} MB).\nTelegram бот фақат 50 MB гача файл жўната олади.",
        "uploading": "📤 Аудио Telegram'га юкланмоқда...",
        "caption": "🎧 «Мифтаҳул Арабийя» {name} | Habib Academy",
        "select_lang": "Илтимос, керакли тилни танланг:",
        "folder_found": "📁 **{title}** дарслиги бўйича **{count}** та аудио дарс топилди.\n\nКеракли дарс устига босинг ёки барчасини юклаб олинг:",
        "download_all_btn": "📥 Барчасини юклаб олиш ({count} та)",
        "downloading_all_progress": "⏳ Барча дарслар юкланмоқда ({current}/{total}): {name}...",
        "all_sent": "✅ «{title}» бўйича барча {total} та аудио дарс жўнатилди!",
        "info": (
            "ℹ️ **Habib Academy Bot**\n\n"
            "Ушбу бот «Мифтаҳул Арабийя» араб тили дарслиги учун мўлжалланган.\n"
            "Китобдаги QR код расмини жўнатсангиз, бот Google Drive'дан керакли аудио дарсликларни "
            "автоматик саралаб, сизга аудио форматида тақдим этади.\n\n"
            "📌 **Буйруқлар:**\n"
            "/start — Ботни қайта ишга тушириш\n"
            "/lang — Мулоқот тилини ўзгартириш\n"
            "/info — Бот ҳақида маълумот"
        ),
    },

    # 4. Русский
    "ru": {
        "welcome": "Здравствуйте! Добро пожаловать в бот Habib Academy.\n\nПожалуйста, выберите язык:",
        "lang_chosen": (
            "✅ Выбран русский язык.\n\n"
            "📖 Отправьте фото QR-кода аудио из книги «Мифтахуль Арабийя», "
            "и я пришлю вам аудиофайл урока.\n\n"
            "🔄 Изменить язык: /lang\n"
            "ℹ️ О боте: /info"
        ),
        "scanning": "🔍 Фото получено, сканирую QR-код...",
        "qr_not_found": (
            "❌ QR-код на фото не распознан.\n"
            "Пожалуйста, сделайте более четкое фото при хорошем освещении и отправьте снова."
        ),
        "not_drive": "⚠️ QR-код распознан, но ссылка не ведет на Google Drive:\n`{url}`",
        "downloading": "⏳ Аудиофайл скачивается...",
        "download_error": "❌ Ошибка при скачивании файла. Ссылка недоступна или файл удален.",
        "no_audio_found": (
            "⚠️ В этом QR-коде не найдено аудиоуроков.\n"
            "Пожалуйста, отправляйте только QR-коды аудиоуроков из учебника."
        ),
        "too_large": "⚠️ Файл слишком большой ({size:.1f} МБ).\nTelegram-бот может отправлять файлы только до 50 МБ.",
        "uploading": "📤 Аудиофайл отправляется в Telegram...",
        "caption": "🎧 Аудиоурок «Мифтахуль Арабийя» {name} | Habib Academy",
        "select_lang": "Пожалуйста, выберите язык:",
        "folder_found": "📁 Найдено **{count}** аудиоуроков для раздела **{title}**.\n\nНажмите на нужный урок или скачайте все:",
        "download_all_btn": "📥 Скачать все ({count} аудио)",
        "downloading_all_progress": "⏳ Отправка всех уроков ({current}/{total}): {name}...",
        "all_sent": "✅ Все {total} аудиоуроков по «{title}» успешно отправлены!",
        "info": (
            "ℹ️ **Habib Academy Bot**\n\n"
            "Этот бот создан для учебника арабского языка «Мифтахуль Арабийя».\n"
            "Отправьте фото QR-кода из книги, и бот автоматически отфильтрует и загрузит "
            "аудиоуроки с Google Drive в удобном формате.\n\n"
            "📌 **Команды:**\n"
            "/start — Перезапустить бота\n"
            "/lang — Сменить язык\n"
            "/info — Информация о боте"
        ),
    },

    # 5. English
    "en": {
        "welcome": "Welcome! Welcome to Habib Academy bot.\n\nPlease choose your language:",
        "lang_chosen": (
            "✅ English selected.\n\n"
            "📖 Send a photo of the audio QR code from the 'Miftahul Arabiyya' textbook, "
            "and I will send you the audio lesson.\n\n"
            "🔄 Change language: /lang\n"
            "ℹ️ About bot: /info"
        ),
        "scanning": "🔍 Photo received, scanning QR code...",
        "qr_not_found": (
            "❌ No QR code found in the image.\n"
            "Please make sure the QR code is close, clear, well-lit, and try again."
        ),
        "not_drive": "⚠️ QR code decoded, but it is not a Google Drive link:\n`{url}`",
        "downloading": "⏳ Downloading audio file...",
        "download_error": "❌ Error downloading audio file. Link may be private or unavailable.",
        "no_audio_found": (
            "⚠️ No audio lessons found in this QR code.\n"
            "Please send only audio lesson QR codes from the textbook."
        ),
        "too_large": "⚠️ File size is too large ({size:.1f} MB).\nTelegram bots can only send files up to 50 MB.",
        "uploading": "📤 Uploading audio to Telegram...",
        "caption": "🎧 'Miftahul Arabiyya' {name} | Habib Academy",
        "select_lang": "Please select a language:",
        "folder_found": "📁 Found **{count}** audio tracks for **{title}**.\n\nTap on a lesson to download or download all:",
        "download_all_btn": "📥 Download All ({count} audios)",
        "downloading_all_progress": "⏳ Uploading all lessons ({current}/{total}): {name}...",
        "all_sent": "✅ All {total} audio lessons for '{title}' uploaded!",
        "info": (
            "ℹ️ **Habib Academy Bot**\n\n"
            "This bot is designed for the 'Miftahul Arabiyya' Arabic textbook.\n"
            "Send a photo of any audio QR code from the book, and the bot will filter and fetch "
            "the audio lessons from Google Drive directly.\n\n"
            "📌 **Commands:**\n"
            "/start — Restart bot\n"
            "/lang — Change language\n"
            "/info — Information about the bot"
        ),
    },

    # 6. العربية
    "ar": {
        "welcome": "أهلاً وسهلاً بكم في بوت Habib Academy.\n\nيرجى اختيار لغتكم المفضلة:",
        "lang_chosen": (
            "✅ تم اختيار اللغة العربية.\n\n"
            "📖 أرسل صورة رمز QR للصوتيات من كتاب «مفتاح العربية»، "
            "وسأقوم بتحميل الملف الصوتي وإرساله إليك.\n\n"
            "🔄 لتغيير اللغة: /lang\n"
            "ℹ️ معلومات البوت: /info"
        ),
        "scanning": "🔍 تم استلام الصورة، جاري مسح رمز QR...",
        "qr_not_found": (
            "❌ لم يتم العثور على رمز QR في الصورة.\n"
            "يرجى تصوير الرمز بشكل واضح ومقرب وفي إضاءة جيدة والمحاولة مرة أخرى."
        ),
        "not_drive": "⚠️ تم قراءة رمز QR، لكنه ليس رابط Google Drive:\n`{url}`",
        "downloading": "⏳ جاري تحميل الملف الصوتي...",
        "download_error": "❌ حدث خطأ أثناء تحميل الملف. قد يكون الرابط مغلقاً أو الملف غير متاح.",
        "no_audio_found": (
            "⚠️ لم يتم العثور على دروس صوتية في هذا الرمز.\n"
            "يرجى إرسال رموز QR الخاصة بالدروس الصوتية من الكتاب فقط."
        ),
        "too_large": "⚠️ حجم الملف كبير جداً ({size:.1f} ميغابايت).\nالحد الأقصى لملفات البوت هو 50 ميغابايت.",
        "uploading": "📤 جاري رفع الملف الصوتي إلى تيليجرام...",
        "caption": "🎧 درس صوتي «مفتاح العربية» {name} | Habib Academy",
        "select_lang": "يرجى اختيار اللغة:",
        "folder_found": "📁 تم العثور على **{count}** ملفات صوتية لقسم **{title}**.\n\nاضغط على الدرس المطلوب أو قم بتحميل الكل:",
        "download_all_btn": "📥 تحميل الكل ({count} ملفات)",
        "downloading_all_progress": "⏳ جاري إرسال الدروس ({current}/{total}): {name}...",
        "all_sent": "✅ تم إرسال جميع الدروس الصوتية ({total}) لقسم «{title}»!",
        "info": (
            "ℹ️ **بوت Habib Academy**\n\n"
            "تم تصميم هذا البوت لكتاب «مفتاح العربية» لتعليم اللغة العربية.\n"
            "أرسل صورة أي رمز QR من الكتاب وسيقوم البوت تلقائياً بتصفية وتنزيل الدروس الصوتية "
            "من Google Drive وإرسالها لك مباشرة.\n\n"
            "📌 **الأوامر:**\n"
            "/start — إعادة تشغيل البوت\n"
            "/lang — تغيير اللغة\n"
            "/info — معلومات حول البوت"
        ),
    },
}

def get_text(user_id: int, key: str, **kwargs) -> str:
    lang = user_languages.get(user_id, "uz_lat")
    template = TEXTS.get(lang, TEXTS["uz_lat"]).get(key, "")
    return template.format(**kwargs) if kwargs else template

def get_language_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="🇺🇿 O'zbekcha (Lotin)", callback_data="setlang_uz_lat")],
        [InlineKeyboardButton(text="🇺🇿 Özbekça (Yangi)", callback_data="setlang_uz_new")],
        [InlineKeyboardButton(text="🇺🇿 Ўзбекча (Кирилл)", callback_data="setlang_uz_cyr")],
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="setlang_ru")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="setlang_en")],
        [InlineKeyboardButton(text="🇸🇦 العربية", callback_data="setlang_ar")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_folder_keyboard(folder_id: str, file_list: list[tuple[str, str]], lang: str) -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for fid, name in file_list:
        short_name = name.replace(".mp3", "").replace(".wav", "").replace("Audio", "").strip()
        row.append(InlineKeyboardButton(text=short_name, callback_data=f"dl_{fid}"))
        if len(row) == 4:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    dl_all_text = TEXTS.get(lang, TEXTS["uz_lat"])["download_all_btn"].format(count=len(file_list))
    buttons.append([InlineKeyboardButton(text=dl_all_text, callback_data=f"dlall_{folder_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ==========================================
# QR KODNI ANIQLASH (ULTRA-ROBUST QR DECODER)
# ==========================================
def decode_qr(image_bytes: bytes) -> str | None:
    # 1. zxing-cpp orqali o'qish (eng kuchli va tezkor skaner)
    try:
        import zxingcpp
        from PIL import Image
        import io

        pil_img = Image.open(io.BytesIO(image_bytes))
        barcodes = zxingcpp.read_barcodes(pil_img)
        for b in barcodes:
            if b.text:
                return b.text
    except Exception as e:
        print(f"zxingcpp tekshiruvida: {e}")

    # 2. Agar zxingcpp topilmasa, OpenCV orqali bir necha filtrlar bilan urinib ko'ramiz
    try:
        np_arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if img is not None:
            detector = cv2.QRCodeDetector()

            # 2.1 Asl rangli tasvir
            data, _, _ = detector.detectAndDecode(img)
            if data:
                return data

            # 2.2 Kulrang (Grayscale) tasvir
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            data, _, _ = detector.detectAndDecode(gray)
            if data:
                return data

            # 2.3 Kontrast va Otsu binarizatsiya
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            data, _, _ = detector.detectAndDecode(thresh)
            if data:
                return data

            # 2.4 Keskinlashtirish (Sharpening - xira rasmlar uchun)
            kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
            sharp = cv2.filter2D(gray, -1, kernel)
            data, _, _ = detector.detectAndDecode(sharp)
            if data:
                return data
    except Exception as e:
        print(f"OpenCV tekshiruvida: {e}")

    return None


# ==========================================
# AUDIO FORMATINI TEKSHIRISH (MAGIC BYTES)
# ==========================================
def check_is_audio(file_path: str, content_type: str = "") -> bool:
    """Fayl haqiqiy audio ekanligini Content-Type va fayl boshidagi baytlar orqali tekshiradi"""
    if content_type and ("audio" in content_type.lower() or "application/ogg" in content_type.lower()):
        return True
    try:
        with open(file_path, "rb") as f:
            header = f.read(16)
            # MP3 (ID3 yoki syncword \xff\xfb, \xff\xf3, \xff\xf2)
            if header.startswith(b"ID3") or header.startswith(b"\xff\xfb") or header.startswith(b"\xff\xf3") or header.startswith(b"\xff\xf2"):
                return True
            # WAV (RIFF....WAVE)
            if header.startswith(b"RIFF") and b"WAVE" in header:
                return True
            # M4A / AAC (ftyp)
            if b"ftyp" in header:
                return True
            # OGG (OggS)
            if header.startswith(b"OggS"):
                return True
            # FLAC (fLaC)
            if header.startswith(b"fLaC"):
                return True
    except Exception:
        pass
    return False


# ==========================================
# GOOGLE DRIVE PAPKA VA FAYLLARNI SARALASH (FILTER)
# ==========================================
def parse_drive_url(url: str):
    """
    Google Drive havolasini tekshiradi va FAQAT AUDIO fayllarni saralab oladi.
    Begona fayllar (PDF, video, arxiv, rasm) tashlab ketiladi.
    """
    m = re.search(r'id=([a-zA-Z0-9_-]{25,})', url)
    if not m:
        m = re.search(r'/(?:folders|file/d)/([a-zA-Z0-9_-]{25,})', url)
    
    if not m:
        return None, None, None, []
    
    drive_id = m.group(1)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    check_url = f"https://drive.google.com/open?id={drive_id}"
    req = urllib.request.Request(check_url, headers=headers)
    
    final_url = url
    html = ""
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            final_url = resp.geturl()
            html = resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print("URL tekshirishda xatolik:", e)
        return "file", drive_id, "audio.mp3", [(drive_id, "audio.mp3")]

    # Agar havola papka bo'lsa
    if "folders" in final_url or "folders" in url:
        m_title = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
        folder_title = "Darslik"
        if m_title:
            folder_title = m_title.group(1).split("–")[0].split("-")[0].strip()

        items = re.findall(r'data-id="([a-zA-Z0-9_-]{25,})"[^>]*data-tooltip="([^"]+)"', html)
        file_list = []
        for fid, tooltip in items:
            # FAQAT audio fayllarni saralab olamiz
            is_audio = "Audio" in tooltip or any(tooltip.lower().endswith(ext) or ext in tooltip.lower() for ext in AUDIO_EXTENSIONS)
            if is_audio:
                clean_name = tooltip.replace(" Audio", "").strip()
                file_list.append((fid, clean_name))

        if not file_list:
            items2 = re.findall(r'data-id="([a-zA-Z0-9_-]{25,})".*?<strong class="[^"]*">([^<]+)</strong>', html)
            for fid, name in items2:
                if any(name.lower().endswith(ext) for ext in AUDIO_EXTENSIONS):
                    file_list.append((fid, name.strip()))

        # Agar papkada birorta ham audio topilmasa, bo'sh ro'yxat qaytaramiz
        return "folder", drive_id, folder_title, file_list
    else:
        # Bitta alohida fayl
        m_title = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
        file_title = "audio.mp3"
        if m_title:
            file_title = m_title.group(1).split("–")[0].split("-")[0].strip()

        return "file", drive_id, file_title, [(drive_id, file_title)]


def download_drive_file(file_id: str, output_path: str) -> tuple[bool, str]:
    """
    Faylni yuklab oladi va haqiqiy audio ekanligini tekshiradi.
    (Muvaffaqiyatli_yuklandimi, Xatolik_sababi)
    """
    download_urls = [
        f"https://drive.usercontent.google.com/download?id={file_id}&export=download&authuser=0",
        f"https://drive.google.com/uc?id={file_id}&export=download",
    ]
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    for u in download_urls:
        try:
            req = urllib.request.Request(u, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as resp:
                if resp.status == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    with open(output_path, "wb") as f:
                        while True:
                            chunk = resp.read(64 * 1024)
                            if not chunk:
                                break
                            f.write(chunk)
                    
                    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                        # AUDIO FILTRI: Haqiqatan ham audio ekanligini tekshiramiz
                        if not check_is_audio(output_path, content_type):
                            if os.path.exists(output_path):
                                os.remove(output_path)
                            return False, "not_audio"
                        return True, "ok"
        except Exception:
            continue
    return False, "download_failed"


# ==========================================
# BOT HANDLERLARI
# ==========================================
@dp.message(CommandStart())
async def cmd_start(message: Message):
    welcome_text = (
        "Assalomu alaykum! Habib Academy botiga xush kelibsiz.\n"
        "Welcome! / Добро пожаловать! / أهلاً وسهلاً!\n\n"
        "Iltimos, tilni tanlang | Please select a language | Выберите язык:"
    )
    await message.answer(welcome_text, reply_markup=get_language_keyboard())


@dp.message(Command("lang", "language"))
async def cmd_lang(message: Message):
    user_id = message.from_user.id
    await message.answer(
        get_text(user_id, "select_lang"),
        reply_markup=get_language_keyboard()
    )


@dp.message(Command("info", "help"))
async def cmd_info(message: Message):
    user_id = message.from_user.id
    await message.answer(
        get_text(user_id, "info"),
        parse_mode="Markdown"
    )


@dp.callback_query(F.data.startswith("setlang_"))
async def cb_set_language(callback: CallbackQuery):
    lang_code = callback.data.split("_", 1)[1]
    user_languages[callback.from_user.id] = lang_code
    await callback.answer()
    text = get_text(callback.from_user.id, "lang_chosen")
    await callback.message.edit_text(text)


async def process_drive_url(user_id: int, url: str, status_msg: Message):
    loop = asyncio.get_event_loop()
    kind, item_id, title, files = await loop.run_in_executor(None, parse_drive_url, url)

    # Agar papka bo'sh bo'lsa yoki audio fayl umuman bo'lmasa
    if not files:
        await status_msg.edit_text(get_text(user_id, "no_audio_found"))
        return

    # Agar bir nechta audio fayllar bo'lsa (Darslik bo'limi)
    if kind == "folder" and len(files) > 1:
        folder_cache[item_id] = files
        for fid, name in files:
            file_names_cache[fid] = name

        lang = user_languages.get(user_id, "uz_lat")
        folder_text = get_text(user_id, "folder_found", title=title, count=len(files))
        keyboard = get_folder_keyboard(item_id, files, lang)
        await status_msg.edit_text(folder_text, reply_markup=keyboard, parse_mode="Markdown")
        return

    # Agar bitta audio bo'lsa
    single_fid, single_name = files[0]
    file_names_cache[single_fid] = single_name
    await status_msg.edit_text(get_text(user_id, "downloading"))

    temp_filename = f"{uuid.uuid4().hex}.mp3"
    temp_filepath = os.path.join(TEMP_DIR, temp_filename)

    success, reason = await loop.run_in_executor(None, download_drive_file, single_fid, temp_filepath)

    if not success:
        if reason == "not_audio":
            await status_msg.edit_text(get_text(user_id, "no_audio_found"))
        else:
            await status_msg.edit_text(get_text(user_id, "download_error"))
        return

    file_size_mb = os.path.getsize(temp_filepath) / (1024 * 1024)
    if file_size_mb > 50:
        await status_msg.edit_text(get_text(user_id, "too_large", size=file_size_mb))
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)
        return

    await status_msg.edit_text(get_text(user_id, "uploading"))

    try:
        audio = FSInputFile(temp_filepath, filename=single_name if single_name.endswith(".mp3") else f"{single_name}.mp3")
        await status_msg.answer_audio(
            audio=audio,
            caption=get_text(user_id, "caption", name=single_name)
        )
        await status_msg.delete()
    except Exception as e:
        await status_msg.edit_text(f"❌ Xatolik: {e}")
    finally:
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)


@dp.message(F.photo)
async def handle_photo(message: Message):
    user_id = message.from_user.id
    status_msg = await message.answer(get_text(user_id, "scanning"))

    file_id = message.photo[-1].file_id
    file = await bot.get_file(file_id)
    file_bytes = await bot.download_file(file.file_path)

    qr_url = decode_qr(file_bytes.read())

    if not qr_url:
        await status_msg.edit_text(get_text(user_id, "qr_not_found"))
        return

    if "drive.google.com" not in qr_url and "google.com" not in qr_url:
        await status_msg.edit_text(
            get_text(user_id, "not_drive", url=qr_url),
            parse_mode="Markdown"
        )
        return

    await process_drive_url(user_id, qr_url, status_msg)


@dp.message(F.text.contains("drive.google.com"))
async def handle_direct_link(message: Message):
    user_id = message.from_user.id
    status_msg = await message.answer(get_text(user_id, "scanning"))
    await process_drive_url(user_id, message.text.strip(), status_msg)


@dp.callback_query(F.data.startswith("dl_"))
async def cb_download_single(callback: CallbackQuery):
    user_id = callback.from_user.id
    fid = callback.data.split("_", 1)[1]
    name = file_names_cache.get(fid, "darslik_audio.mp3")

    await callback.answer(f"⏳ {name}...")

    temp_filename = f"{uuid.uuid4().hex}.mp3"
    temp_filepath = os.path.join(TEMP_DIR, temp_filename)

    loop = asyncio.get_event_loop()
    success, reason = await loop.run_in_executor(None, download_drive_file, fid, temp_filepath)

    if not success:
        if reason == "not_audio":
            await callback.message.answer(get_text(user_id, "no_audio_found"))
        else:
            await callback.message.answer(get_text(user_id, "download_error"))
        return

    try:
        audio = FSInputFile(temp_filepath, filename=name if name.endswith(".mp3") else f"{name}.mp3")
        await callback.message.answer_audio(
            audio=audio,
            caption=get_text(user_id, "caption", name=name)
        )
    except Exception as e:
        await callback.message.answer(f"❌ Xatolik: {e}")
    finally:
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)


@dp.callback_query(F.data.startswith("dlall_"))
async def cb_download_all(callback: CallbackQuery):
    user_id = callback.from_user.id
    folder_id = callback.data.split("_", 1)[1]
    files = folder_cache.get(folder_id)

    if not files:
        folder_url = f"https://drive.google.com/drive/folders/{folder_id}"
        loop = asyncio.get_event_loop()
        _, _, _, files = await loop.run_in_executor(None, parse_drive_url, folder_url)

    if not files:
        await callback.answer(get_text(user_id, "no_audio_found"), show_alert=True)
        return

    await callback.answer("⏳ Barcha audio fayllar yuklanmoqda...")
    status_msg = await callback.message.answer(f"⏳ 1/{len(files)} yuklanmoqda...")

    loop = asyncio.get_event_loop()
    for idx, (fid, name) in enumerate(files, start=1):
        try:
            await status_msg.edit_text(
                get_text(user_id, "downloading_all_progress", current=idx, total=len(files), name=name)
            )
        except Exception:
            pass

        temp_filename = f"{uuid.uuid4().hex}.mp3"
        temp_filepath = os.path.join(TEMP_DIR, temp_filename)

        success, _ = await loop.run_in_executor(None, download_drive_file, fid, temp_filepath)
        if success and os.path.exists(temp_filepath):
            try:
                audio = FSInputFile(temp_filepath, filename=name if name.endswith(".mp3") else f"{name}.mp3")
                await callback.message.answer_audio(
                    audio=audio,
                    caption=get_text(user_id, "caption", name=name)
                )
            except Exception as e:
                print(f"Jo'natishda xatolik {name}: {e}")
            finally:
                if os.path.exists(temp_filepath):
                    os.remove(temp_filepath)
        
        await asyncio.sleep(0.5)

    await status_msg.delete()


# ==========================================
# MENYU BUYRUQLARINI O'RNATISH (SET COMMANDS)
# ==========================================
async def setup_bot_commands():
    commands = [
        BotCommand(command="start", description="Qayta ishga tushirish / البدء"),
        BotCommand(command="lang", description="Tilni tanlash / تغيير اللغة"),
        BotCommand(command="info", description="Bot haqida ma'lumot / حول البوت"),
    ]
    try:
        await bot.set_my_commands(commands)
        print("✅ Telegram Menyu buyruqlari o'rnatildi.")
    except Exception as e:
        print(f"Menyu o'rnatishda xatolik: {e}")


# ==========================================
# RENDER UCHUN KEEP-ALIVE SERVER
# ==========================================
async def health_check(request):
    return web.Response(text="Habib Academy Bot is running 24/7!", status=200)

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)

    port = int(os.environ.get("PORT", 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"🌐 Keep-alive veb-server {port}-portda ishga tushdi.")


# ==========================================
# ASOSIY ISHGA TUSHIRISH (MAIN)
# ==========================================
async def main():
    print("🚀 Habib Academy Bot ishga tushirilmoqda...")
    await start_web_server()
    await setup_bot_commands()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

import os
import uuid
import asyncio
import cv2
import numpy as np
import gdown
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    FSInputFile,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)
from aiogram.filters import CommandStart, Command

# ==========================================
# SOZLAMALAR (CONFIGURATION)
# ==========================================
# Render'da Environment Variables (BOT_TOKEN) dan olinadi.
# Lokal test qilish uchun tokenni bevosita qo'yishingiz ham mumkin:
BOT_TOKEN = os.environ.get("BOT_TOKEN", "SIZNING_BOT_TOKENINGIZ")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Vaqtinchalik audio fayllarni saqlash papkasi
TEMP_DIR = "temp_audio"
os.makedirs(TEMP_DIR, exist_ok=True)

# Foydalanuvchilar tanlagan tillari xotirada (RAM) saqlanadi (Ma'lumotlar bazasi shart emas)
user_languages: dict[int, str] = {}

# ==========================================
# KO'P TILLI MATNLAR (MULTILINGUAL TEXTS)
# ==========================================
TEXTS = {
    "uz_lat": {
        "welcome": "Assalomu alaykum! Habib Academy botiga xush kelibsiz.\n\nIltimos, tilni tanlang:",
        "lang_chosen": (
            "✅ O'zbek tili (Lotin) tanlandi.\n\n"
            "📖 «Miftahul Arabiyya» kitobidagi audio QR kodining rasmini yuboring, "
            "men sizga darslik audiosini yuklab beraman.\n\n"
            "🔄 Tilni o'zgartirish uchun: /lang"
        ),
        "scanning": "🔍 Rasm qabul qilindi, QR kod o'qilmoqda...",
        "qr_not_found": (
            "❌ Rasmdan QR kod topilmadi.\n"
            "Iltimos, kitobdagi QR kodni yaqinroq, aniq va yaxshi yorug'likda rasmga olib qayta yuboring."
        ),
        "not_drive": "⚠️ QR kod o'qildi, ammo u Google Drive havolasi emas:\n`{url}`",
        "downloading": "⏳ Audio fayl Google Drive'dan yuklab olinmoqda...",
        "download_error": "❌ Audio faylni yuklab olishda xatolik yuz berdi. Havola yopiq yoki fayl mavjud emas.",
        "too_large": "⚠️ Fayl hajmi juda katta ({size:.1f} MB).\nTelegram bot faqat 50 MB gacha fayl jo'nata oladi.",
        "uploading": "📤 Audio Telegram'ga yuklanmoqda...",
        "caption": "🎧 «Miftahul Arabiyya» audio darsi | Habib Academy",
        "select_lang": "Iltimos, kerakli tilni tanlang:",
    },
    "uz_cyr": {
        "welcome": "Ассалому алайкум! Habib Academy ботига хуш келибсиз.\n\nИлтимос, тилни танланг:",
        "lang_chosen": (
            "✅ Ўзбек тили (Кирилл) танланди.\n\n"
            "📖 «Мифтаҳул Арабийя» китобидаги аудио QR код расмини юборинг, "
            "мен сизга дарслик аудиосини юклаб бераман.\n\n"
            "🔄 Тилни ўзгартириш учун: /lang"
        ),
        "scanning": "🔍 Расм қабул қилинди, QR код ўқилмоқда...",
        "qr_not_found": (
            "❌ Расмдан QR код топилмади.\n"
            "Илтимос, китобдаги QR кодни яқинроқ, аниқ ва яхши ёруғликда расмга олиб қайта юборинг."
        ),
        "not_drive": "⚠️ QR код ўқилди, аммо у Google Drive ҳаволаси эмас:\n`{url}`",
        "downloading": "⏳ Аудио файл Google Drive'дан юклаб олинмоқда...",
        "download_error": "❌ Аудио файлни юклаб олишда хатолик юз берди. Ҳавола ёпиқ ёки файл мавжуд эмас.",
        "too_large": "⚠️ Файл ҳажми жуда катта ({size:.1f} MB).\nTelegram бот фақат 50 MB гача файл жўната олади.",
        "uploading": "📤 Аудио Telegram'га юкланмоқда...",
        "caption": "🎧 «Мифтаҳул Арабийя» аудио дарси | Habib Academy",
        "select_lang": "Илтимос, керакли тилни танланг:",
    },
    "ru": {
        "welcome": "Здравствуйте! Добро пожаловать в бот Habib Academy.\n\nПожалуйста, выберите язык:",
        "lang_chosen": (
            "✅ Выбран русский язык.\n\n"
            "📖 Отправьте фото QR-кода аудио из книги «Мифтахуль Арабийя», "
            "и я пришлю вам аудиофайл урока.\n\n"
            "🔄 Чтобы изменить язык: /lang"
        ),
        "scanning": "🔍 Фото получено, сканирую QR-код...",
        "qr_not_found": (
            "❌ QR-код на фото не распознан.\n"
            "Пожалуйста, сделайте более четкое фото при хорошем освещении и отправьте снова."
        ),
        "not_drive": "⚠️ QR-код распознан, но ссылка не ведет на Google Drive:\n`{url}`",
        "downloading": "⏳ Аудиофайл скачивается с Google Drive...",
        "download_error": "❌ Ошибка при скачивании файла. Ссылка недоступна или файл удален.",
        "too_large": "⚠️ Файл слишком большой ({size:.1f} МБ).\nTelegram-бот может отправлять файлы только до 50 МБ.",
        "uploading": "📤 Аудиофайл отправляется в Telegram...",
        "caption": "🎧 Аудиоурок «Мифтахуль Арабийя» | Habib Academy",
        "select_lang": "Пожалуйста, выберите язык:",
    },
    "en": {
        "welcome": "Welcome! Welcome to Habib Academy bot.\n\nPlease choose your language:",
        "lang_chosen": (
            "✅ English selected.\n\n"
            "📖 Send a photo of the audio QR code from the 'Miftahul Arabiyya' textbook, "
            "and I will send you the audio lesson.\n\n"
            "🔄 To change language: /lang"
        ),
        "scanning": "🔍 Photo received, scanning QR code...",
        "qr_not_found": (
            "❌ No QR code found in the image.\n"
            "Please make sure the QR code is close, clear, well-lit, and try again."
        ),
        "not_drive": "⚠️ QR code decoded, but it is not a Google Drive link:\n`{url}`",
        "downloading": "⏳ Downloading audio file from Google Drive...",
        "download_error": "❌ Error downloading audio file. Link may be private or unavailable.",
        "too_large": "⚠️ File size is too large ({size:.1f} MB).\nTelegram bots can only send files up to 50 MB.",
        "uploading": "📤 Uploading audio to Telegram...",
        "caption": "🎧 'Miftahul Arabiyya' audio lesson | Habib Academy",
        "select_lang": "Please select a language:",
    },
    "ar": {
        "welcome": "أهلاً وسهلاً بكم في بوت Habib Academy.\n\nيرجى اختيار لغتكم المفضلة:",
        "lang_chosen": (
            "✅ تم اختيار اللغة العربية.\n\n"
            "📖 أرسل صورة رمز QR للصوتيات من كتاب «مفتاح العربية»، "
            "وسأقوم بتحميل الملف الصوتي وإرساله إليك.\n\n"
            "🔄 لتغيير اللغة: /lang"
        ),
        "scanning": "🔍 تم استلام الصورة، جاري مسح رمز QR...",
        "qr_not_found": (
            "❌ لم يتم العثور على رمز QR في الصورة.\n"
            "يرجى تصوير الرمز بشكل واضح ومقرب وفي إضاءة جيدة والمحاولة مرة أخرى."
        ),
        "not_drive": "⚠️ تم قراءة رمز QR، لكنه ليس رابط Google Drive:\n`{url}`",
        "downloading": "⏳ جاري تحميل الملف الصوتي من Google Drive...",
        "download_error": "❌ حدث خطأ أثناء تحميل الملف. قد يكون الرابط مغلقاً أو الملف غير متاح.",
        "too_large": "⚠️ حجم الملف كبير جداً ({size:.1f} ميغابايت).\nالحد الأقصى لملفات البوت هو 50 ميغابايت.",
        "uploading": "📤 جاري رفع الملف الصوتي إلى تيليجرام...",
        "caption": "🎧 درس صوتي «مفتاح العربية» | Habib Academy",
        "select_lang": "يرجى اختيار اللغة:",
    },
}

def get_text(user_id: int, key: str, **kwargs) -> str:
    """Foydalanuvchi tanlagan tilidagi matnni qaytaradi (standart: uz_lat)"""
    lang = user_languages.get(user_id, "uz_lat")
    template = TEXTS.get(lang, TEXTS["uz_lat"]).get(key, "")
    return template.format(**kwargs) if kwargs else template

def get_language_keyboard() -> InlineKeyboardMarkup:
    """5 ta til tugmasidan iborat inline klaviatura"""
    buttons = [
        [InlineKeyboardButton(text="🇺🇿 O'zbekcha (Lotin)", callback_data="setlang_uz_lat")],
        [InlineKeyboardButton(text="🇺🇿 Ўзбекча (Кирилл)", callback_data="setlang_uz_cyr")],
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="setlang_ru")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="setlang_en")],
        [InlineKeyboardButton(text="🇸🇦 العربية", callback_data="setlang_ar")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ==========================================
# QR KODNI ANIQLASH (ROBUST QR DECODER)
# ==========================================
def decode_qr(image_bytes: bytes) -> str | None:
    """
    Rasmdan QR kodni o'qiydi.
    Telefon kamerasida olingan xira/yorug'lik kam suratlarni ham tanish uchun
    bir nechta filtrlardan foydalanadi.
    """
    np_arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if img is None:
        return None

    detector = cv2.QRCodeDetector()

    # 1-urinish: Asl rangli holatida
    data, _, _ = detector.detectAndDecode(img)
    if data:
        return data

    # 2-urinish: Oq-qora (Grayscale) holatida
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    data, _, _ = detector.detectAndDecode(gray)
    if data:
        return data

    # 3-urinish: Kontrast va Otsu binarizatsiya qilingan holatda
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    data, _, _ = detector.detectAndDecode(thresh)
    if data:
        return data

    return None


# ==========================================
# GOOGLE DRIVE YUKLASH FUNKSIYASI
# ==========================================
def download_google_file(url: str, output_path: str) -> bool:
    """Google Drive faylini gdown orqali yuklab oladi"""
    try:
        downloaded = gdown.download(url=url, output=output_path, quiet=True, fuzzy=True)
        return downloaded is not None and os.path.exists(output_path)
    except Exception as e:
        print(f"Yuklab olishda xatolik: {e}")
        return False


# ==========================================
# BOT HANDLERLARI
# ==========================================
@dp.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    # Agar foydalanuvchi avval til tanlamagan bo'lsa, til tanlashni taklif qilamiz
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


@dp.callback_query(F.data.startswith("setlang_"))
async def cb_set_language(callback: CallbackQuery):
    lang_code = callback.data.split("_", 1)[1]
    user_languages[callback.from_user.id] = lang_code
    await callback.answer()

    # Tanlangan tildagi tabrik va ko'rsatma
    text = get_text(callback.from_user.id, "lang_chosen")
    await callback.message.edit_text(text)


@dp.message(F.photo)
async def handle_photo(message: Message):
    user_id = message.from_user.id
    status_msg = await message.answer(get_text(user_id, "scanning"))

    file_id = message.photo[-1].file_id
    file = await bot.get_file(file_id)
    file_bytes = await bot.download_file(file.file_path)

    # QR kodni o'qiymiz
    qr_url = decode_qr(file_bytes.read())

    if not qr_url:
        await status_msg.edit_text(get_text(user_id, "qr_not_found"))
        return

    # Havola Google Drive yoki yo'qligini tekshiramiz
    if "drive.google.com" not in qr_url and "google.com" not in qr_url:
        await status_msg.edit_text(
            get_text(user_id, "not_drive", url=qr_url),
            parse_mode="Markdown"
        )
        return

    await status_msg.edit_text(get_text(user_id, "downloading"))

    # Fayl uchun unikal vaqtinchalik nom
    temp_filename = f"{uuid.uuid4().hex}.mp3"
    temp_filepath = os.path.join(TEMP_DIR, temp_filename)

    # Bot qotib qolmasligi uchun yuklash alohida oqimda (executor) ishlaydi
    loop = asyncio.get_event_loop()
    success = await loop.run_in_executor(None, download_google_file, qr_url, temp_filepath)

    if not success or not os.path.exists(temp_filepath):
        await status_msg.edit_text(get_text(user_id, "download_error"))
        return

    # Telegram bot 50 MB gacha fayl jo'nata oladi
    file_size_mb = os.path.getsize(temp_filepath) / (1024 * 1024)
    if file_size_mb > 50:
        await status_msg.edit_text(get_text(user_id, "too_large", size=file_size_mb))
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)
        return

    await status_msg.edit_text(get_text(user_id, "uploading"))

    try:
        audio = FSInputFile(temp_filepath, filename="habib_academy_audio.mp3")
        await message.answer_audio(
            audio=audio,
            caption=get_text(user_id, "caption")
        )
        await status_msg.delete()
    except Exception as e:
        await status_msg.edit_text(f"❌ Xatolik yuz berdi: {e}")
    finally:
        # Fayl darhol o'chiriladi (serverda joy egallamaydi va xotira saqlanmaydi)
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)


# Foydalanuvchi matn sifatida to'g'ridan-to'g'ri havola yuborsa ham qo'llab-quvvatlash
@dp.message(F.text.contains("drive.google.com"))
async def handle_direct_link(message: Message):
    user_id = message.from_user.id
    qr_url = message.text.strip()
    status_msg = await message.answer(get_text(user_id, "downloading"))

    temp_filename = f"{uuid.uuid4().hex}.mp3"
    temp_filepath = os.path.join(TEMP_DIR, temp_filename)

    loop = asyncio.get_event_loop()
    success = await loop.run_in_executor(None, download_google_file, qr_url, temp_filepath)

    if not success or not os.path.exists(temp_filepath):
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
        audio = FSInputFile(temp_filepath, filename="habib_academy_audio.mp3")
        await message.answer_audio(
            audio=audio,
            caption=get_text(user_id, "caption")
        )
        await status_msg.delete()
    except Exception as e:
        await status_msg.edit_text(f"❌ Xatolik: {e}")
    finally:
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)


# ==========================================
# RENDER UCHUN WEB SERVER (PING UYRUNGLARI UCHUN)
# ==========================================
async def health_check(request):
    """Render va UptimeRobot uchun 'tiriklik' endpointi"""
    return web.Response(text="Habib Academy Bot is running 24/7!", status=200)

async def start_web_server():
    """Render bergan $PORT da veb-serverni ishga tushiradi"""
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
    # 1. Render uxlab qolmasligi uchun HTTP serverni ishga tushiramiz
    await start_web_server()
    # 2. Telegram bot polling rejimida tinglaydi
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

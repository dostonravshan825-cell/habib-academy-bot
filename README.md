# 📖 Habib Academy Bot («Miftahul Arabiyya» Audio Bot)

Bu bot «Miftahul Arabiyya» kitobidagi audio darslar uchun mo'ljallangan QR kodlarni o'qib, ularga tegishli audio fayllarni Google Drive'dan yuklab, Telegram orqali foydalanuvchiga jo'natib beradi.

---

## 🌟 Botning xususiyatlari
- **5 ta til tanlovi:**
  - 🇺🇿 O'zbekcha (Lotin)
  - 🇺🇿 Ўзбекча (Кирилл)
  - 🇷🇺 Русский
  - 🇬🇧 English
  - 🇸🇦 العربية
- **Ma'lumotlar bazasisiz (Stateless):** Foydalanuvchilar haqida ma'lumot saqlanmaydi, audio jo'natilgach xotiradan darhol o'chiriladi.
- **Tezkor va mustahkam QR skaner:** Telefon orqali olingan xira yoki qiyshiq rasmlarni ham bir necha filtrlar orqali taniydi.
- **Render'da 24/7 ishlash uchun tayyor:** Ichki veb-server (keep-alive) o'rnatilgan, shuning uchun Render bepul tarifida uxlab qolmaydi.

---

## 🚀 QADAMMA-QADAM ISHGA TUSHIRISH VA DEPLOY QILISH

### 1-qadam: Telegram bot tokenini olish
1. Telegramda [@BotFather](https://t.me/BotFather) botiga kiring.
2. `/newbot` buyrug'ini yuboring.
3. Botingizga nom bering (masalan: `Habib Academy Bot`).
4. Botingizga username bering (masalan: `habib_academy_audio_bot`).
5. BotFather bergan **HTTP API Token**ni nusxalab oling (masalan: `7123456789:AAH...`).

---

### 2-qadam: GitHub'ga yuklash
1. [GitHub.com](https://github.com) ga kiring va yangi repository oching (masalan, `habib-academy-bot`).
2. Kompyuteringizdagi ushbu papkaga kirib, terminalda (CMD yoki PowerShell) quyidagi buyruqlarni ketma-ket bajaring:

```bash
cd "C:\Users\User\Desktop\Habib Academy bot"
git init
git add .
git commit -m "Habib Academy bot boshlang'ich versiyasi"
git branch -M main
git remote add origin https://github.com/SIZNING_USERNAME/habib-academy-bot.git
git push -u origin main
```

*(Eslatma: `SIZNING_USERNAME` o'rniga o'zingizning GitHub profilingiz nomini yozing).*

---

### 3-qadam: Render.com ga bepul deploy qilish
1. [Render.com](https://render.com) ga kiring va GitHub akkauntingiz orqali ro'yxatdan o'ting.
2. Dashboard'da **"New +"** tugmasini bosing va **"Web Service"** ni tanlang.
3. GitHub'dagi `habib-academy-bot` repozitoriyangizni tanlang (**Connect**).
4. Sozlamalarni quyidagicha to'ldiring:
   - **Name:** `habib-academy-bot`
   - **Region:** Frankfurt (yoki eng yaqini)
   - **Branch:** `main`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot.py`
   - **Instance Type:** `Free`
5. Pastroqda **"Environment Variables"** bo'limiga o'ting:
   - **Key:** `BOT_TOKEN`
   - **Value:** `@BotFather`dan olgan tokeningiz
6. **"Deploy Web Service"** tugmasini bosing.
7. 1–2 daqiqada bot ishga tushadi va Render sizga havola beradi (masalan: `https://habib-academy-bot.onrender.com`).

---

### 4-qadam: Bot uxlab qolmasligi uchun (Har 5 daqiqada uyg'otib turish)
Render bepul xizmati 15 daqiqa so'rov bo'lmasa o'chib qolmasligi (sleep mode'ga tushmasligi) uchun:

1. [UptimeRobot.com](https://uptimerobot.com) saytiga kiring (bepul).
2. **"Add New Monitor"** tugmasini bosing:
   - **Monitor Type:** `HTTP(s)`
   - **Friendly Name:** `Habib Academy Bot`
   - **URL (or IP):** Render bergan havola (masalan: `https://habib-academy-bot.onrender.com/health`)
   - **Monitoring Interval:** `Every 5 minutes`
3. **"Create Monitor"** tugmasini bosing.

🎉 **Bo'ldi!** Endi botingiz 24/7 rejimida uzluksiz, bepul va xotirasiz ishlayveradi!

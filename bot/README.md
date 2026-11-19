# Deutsch Mentor — Telegram bot

Bu bot ikki işni bajaradi:
1. Saytdagi **"Arizani yuboriş"** tugmasi bosilganda ariza (ism, telefon, kurs, maqsad, test natijasi, izoh) ustoz Oğabek Qudratovning Telegramiga keladi.
2. Botga yozgan odamlarga salom beradi va ularning xabarlarini ustozga yetkazadi.

## Fayllar
- `bot.py` — botning özi.
- `config.json` — sozlamalar: bot tokeni, ustozning Telegram username'i, port.
- `start.bat` — Windows'da botni işga tuşiriş uçun ikki marta bosiladi.
- `state.json` — bot özi yaratadi, ustozning chat raqamini eslab qoladi. Öçirmang.

## Birinçi marta sozlaş (10 daqiqa)

**1. Python örnating.** python.org/downloads saytidan Python 3 ni yuklab örnating. Örnatişning birinçi oynasida **"Add python.exe to PATH"** belgisini albatta qöying.

**2. Bot yarating.** Telegramda **@BotFather** ga kiring:
- `/newbot` deb yozing.
- Botga nom bering, masalan `Deutsch Mentor`.
- Username bering, oxiri `bot` bilan tugaşi şart, masalan `deutschmentor_uz_bot`.
- BotFather sizga **token** beradi (masalan `7123456789:AAH...`). Uni nusxalang.

**3. Tokenni joylang.** `config.json` faylini Bloknot (Notepad) bilan oçing va `BU_YERGA_...` örniga tokenni qöying. Qöştirnoqlar qolsin. Saqlang.

Tokenni heç kimga bermang va çatlarga yozmang: u bilan istalgan odam botingizni boşqara oladi.

**4. Botni işga tuşiring.** `start.bat` ni ikki marta bosing. Qora oyna oçiladi va unda `Bot: @...` hamda `Ariza qabul qiliş manzili: http://localhost:8080/api/ariza` yozuvlari çiqadi. Bot işlaşi uçun bu oyna oçiq turişi kerak.

**5. Ustoz botga ulanadi.** Ustoz özining **@User_on** akkauntidan botni topib, **/start** bosadi. Bot "Siz ustoz sifatida röyxatdan ötdingiz" deb javob beradi. Şundan keyin barça arizalar şu çatga keladi.

**6. Sinab köring.** `Nemis Mentor` papkasidagi `index.html` ni oçing, pastdagi formani töldiring va "Arizani yuboriş" ni bosing. Ariza bir neça soniyada ustozning Telegramiga keladi.

## Muhim: sayt internetga çiqqanda
Hozir bot sizning kompyuteringizda işlaydi. Şuning uçun arizalar faqat kompyuter yoqiq va `start.bat` oynasi oçiq bölganda keladi, va faqat şu kompyuterdagi saytdan işlaydi.

Sayt boşqa odamlar uçun internetga joylanganda botni ham doimiy işlaydigan serverga (VPS, Render, Railway va h.k.) qöyiş kerak. Keyin `Nemis Mentor/js/data.js` faylidagi `botApi` qatoriga server manzilini yozasiz, masalan `https://bot.sizningsayt.uz/api/ariza`. Bot işlamay qolsa, sayt foydalanuvçiga arizani töğridan-töğri @User_on ga Telegram orqali yuborişni taklif qiladi, şuning uçun ariza yöqolmaydi.

## Muammolar
- **"Python topilmadi"** — 1-qadamni qayta bajaring va PATH belgisini qöyganingizga işonç hosil qiling.
- **"Token notöğri"** — `config.json` dagi tokenni BotFather'dagi bilan soliştiring.
- **Ariza kelmayapti** — ustoz botga /start bosganmi, va `start.bat` oynasi oçiqmi, tekşiring.
- **"Bu bot boşqa joyda ham işlab turibdi"** — bot faqat bitta joyda işlaşi kerak, ortiqça oynani yoping.

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
)

# --- 1. KONFIGURATSIYA VA SOZLAMALAR ---

# Botning TOKENi va ADMIN CHAT ID si (O'zgartirish shart!)
BOT_TOKEN = "8296929305:AAGMc7VsmAf-zgHkq73WN_6o-j4e28x_UVE"
ADMIN_CHAT_ID = 8329974466

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Suhbat bosqichlari
# Suhbat bosqichlari
FIO, PHONE, ADDRESS, DOCUMENT_TYPE, DOCUMENT_UPLOAD = range(5)
user_data = {}


# --- 2. YORDAMCHI FUNKSIYALAR ---

async def send_admin_report_with_file(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    """Yig'ilgan ma'lumotlarni va Faylni (rasm/hujjat) admin chatiga yuboradi."""
    if user_id not in user_data:
        return False

    data = user_data[user_id]

    # --- ADMIN UCHUN XABAR MATNI (Caption) ---
    admin_caption = (
        "--- 📄 **ARIZA KELDI** 📄 ---\n\n"
        f"👤 **F.I.O.:** {data.get('FIO', 'Noma\'lum')}\n"
        f"📞 **Telefon:** {data.get('Telefon raqami', 'Noma\'lum')}\n"
        f"🏠 **Manzil:** {data.get('Yashash manzili', 'Noma\'lum')}\n"
        f"📜 **Hújjet túri:** **{data.get('Hujjat turi', 'Tanlanmadi')}**\n"
        f"📁 **Fayl turi:** {data.get('file_type', 'Noma\'lum')}"
    )

    try:
        # Faylni yuborish
        file_id = data.get('file_id')
        file_type = data.get('file_type')

        if file_id and file_type:
            # Fayl turiga qarab yuborish funksiyasini tanlash
            if file_type == 'photo':
                await context.bot.send_photo(chat_id=ADMIN_CHAT_ID, photo=file_id, caption=admin_caption,
                                             parse_mode='Markdown')
            elif file_type == 'document':
                await context.bot.send_document(chat_id=ADMIN_CHAT_ID, document=file_id, caption=admin_caption,
                                                parse_mode='Markdown')
            else:
                # Agar fayl turini aniqlay olmasak, matnni yuborish
                await context.bot.send_message(chat_id=ADMIN_CHAT_ID,
                                               text=admin_caption + "\n\n❌ **DIQQAT:** Fayl túri nadurıs bolǵanı ushın fayl biriktirilmadi.",
                                               parse_mode='Markdown')
        else:
            # Agar fayl yuklanmagan bo'lsa, faqat matnni yuborish
            await context.bot.send_message(chat_id=ADMIN_CHAT_ID,
                                           text=admin_caption + "\n\n❌ **DIQQAT:** Hújjet faylı júklenbegen.",
                                           parse_mode='Markdown')

        return True
    except Exception as e:
        logger.error(f"Adminin xabarın jiberiwde qáte júz berdi: {e}")
        return False


# --- 3. BOT FUNKSIYALARI (Handlerlar) ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """/start buyrug'i, F.I.O. ni so'raydi."""
    await update.message.reply_text(
        "👋 Assalawma aleykum! Arza toltırıwdı baslaymız.\n\n"
        "1. Iltimas, **F.I.O.**  (Famılıya, At, Ákesiniń atı) ni tolıq kirgiziń:"
    )
    return FIO


async def get_fio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """F.I.O. ni qabul qiladi va Telefon raqamini so'raydi."""
    fio = update.message.text
    user_data[update.effective_user.id] = {'FIO': fio}

    await update.message.reply_text(
        f"Raxmet. 2. Endi **Telefon nomerngizni** kirgiziń (Mısalı: +998xxAAAAAAA):"
    )
    return PHONE


async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Telefon raqamini qabul qiladi va Manzilni so'raydi."""
    phone = update.message.text
    user_id = update.effective_user.id

    if not (phone.startswith('+') and phone[1:].replace(' ', '').isdigit()):
        await update.message.reply_text(
            "Telefon raqami noto'g'ri formatda. Iltimos, **+998xxAAAAAAA** formatida kiriting:"
        )
        return PHONE

    user_data[user_id]['Telefon raqami'] = phone

    await update.message.reply_text(
        "A'lo! 3. **Jasaw manzil** (Yashash manzilingizni) kiriting:"
    )
    return ADDRESS


async def get_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Manzilni qabul qiladi va Hujjat turini tanlash menyusini chiqaradi."""
    address = update.message.text
    user_id = update.effective_user.id
    user_data[user_id]['Yashash manzili'] = address

    # --- HUJJAT TURI UCHUN INLINE TUGMALAR ---
    keyboard = [
        [InlineKeyboardButton("Socialliq qorǵaw reestri", callback_data='doc_social_reg')],
        [InlineKeyboardButton("Baǵıwshısın joǵaltqan", callback_data='doc_lost_support')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Rahmat. 4. **Qaysı hújjetti tapsırmaqsız?** Iltimos, kerakli variantni tanlang:",
        reply_markup=reply_markup,
    )
    return DOCUMENT_TYPE


async def handle_document_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Hujjat turini qabul qiladi va Hujjatni yuklashni so'raydi."""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    selected_option = query.data

    # Tanlangan hujjat nomini saqlash
    if selected_option == 'doc_social_reg':
        doc_name = "Socialliq qorǵaw reestri"
    elif selected_option == 'doc_lost_support':
        doc_name = "Baǵıwshısın joǵaltqan haqqındaǵı"
    else:
        doc_name = "Noma'lum"

    user_data[user_id]['Hujjat turi'] = doc_name

    await query.edit_message_text(
        text=f"Siz **{doc_name}** hujjat turini tanladingiz.\n\n"
             "5. Endi iltimos, **Hújjetti júkleń** (fayl yoki rasm shaklida) yuboring."
    )
    return DOCUMENT_UPLOAD


async def get_document_upload(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Faylni (rasm yoki hujjatni) qabul qiladi va admin chatiga yuboradi."""
    user_id = update.effective_user.id
    file_id = None
    file_type = None

    # Rasm kiritilgan bo'lsa
    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        file_type = 'photo'

    # Hujjat (PDF, DOC, kabi) kiritilgan bo'lsa
    elif update.message.document:
        file_id = update.message.document.file_id
        file_type = 'document'

    else:
        # Noto'g'ri turdagi xabar kelsa
        await update.message.reply_text("Iltimas, dokumentti súwret (*.jpg) yamasa fayl (*.pdf, *. doc) formasında jiberiń.")
        return DOCUMENT_UPLOAD

    # Fayl ma'lumotlarini saqlash
    user_data[user_id]['file_id'] = file_id
    user_data[user_id]['file_type'] = file_type

    # Admin chatiga xabar va faylni yuborish
    if await send_admin_report_with_file(context, user_id):
        await update.message.reply_text(
            f"✅ Qutlıqlaymız! Barlıq maǵlıwmatlar hám hújjet ({file_type}) Admınıstratorga tabıslı jiberildi. Raxmet!",
        )
    else:
        await update.message.reply_text(
            "Keshirersiz, maǵlıwmatlardı jiberiwde qátelik júz berdi. Iltimas, /start buyrıǵı menen qayta urınıp kóriń.",
        )

    # Suhbatni tugatish va ma'lumotlarni tozalash
    del user_data[user_id]
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """/cancel buyrug'i suhbatni tugatadi."""
    user_id = update.effective_user.id
    if user_id in user_data:
        del user_data[user_id]

    await update.message.reply_text('Arza toltırıw biykar etildi. Baslaw ushın /start buyrıǵın jiberiń.')
    return ConversationHandler.END


# --- 4. ASOSIY DASTUR FUNKSIYASI ---

def main() -> None:
    """Botni o'rnatadi va ishga tushiradi."""

    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],

        states={
            FIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_fio)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_address)],
            DOCUMENT_TYPE: [CallbackQueryHandler(handle_document_type)],
            # Fayl yuklash bosqichi uchun Rasm yoki Hujjat kutiladi
            DOCUMENT_UPLOAD: [
                MessageHandler(filters.PHOTO, get_document_upload),
                MessageHandler(filters.Document.ALL, get_document_upload),
            ],
        },

        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    logger.info("Bot jumısqa túsirildi.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
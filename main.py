import os
import logging
import asyncio
from typing import Optional
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI

# === CONFIGURARE ===
load_dotenv()  # Încarcă variabilele din .env

# Configurare logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Variabile de mediu
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
AI_MODEL = os.getenv('AI_MODEL', 'gpt-3.5-turbo')
AI_MAX_TOKENS = int(os.getenv('AI_MAX_TOKENS', 500))
AI_TEMPERATURE = float(os.getenv('AI_TEMPERATURE', 0.7))

# Verifică variabilele de mediu
if not TELEGRAM_TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN nu este setat în .env")
    raise ValueError("TELEGRAM_BOT_TOKEN lipsă")

if not OPENAI_API_KEY:
    logger.error("❌ OPENAI_API_KEY nu este setat în .env")
    raise ValueError("OPENAI_API_KEY lipsă")

# Initializează client OpenAI
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# === FUNCȚII AI ===
async def get_ai_response(user_message: str, user_name: str = "User") -> Optional[str]:
    """
    Obține răspuns de la AI pentru mesajul utilizatorului
    """
    try:
        # Sistem prompt pentru a controla comportamentul AI
        system_prompt = f"""Ești un asistent AI prietenos într-un chat Telegram.
Utilizatorul se numește {user_name}.
Răspunde într-un mod conversațional, prietenos și util.
Fii concis dar informativ.
Limba: română (dacă utilizatorul scrie în română) sau engleză.
"""
        
        response = openai_client.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=AI_MAX_TOKENS,
            temperature=AI_TEMPERATURE,
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        logger.error(f"❌ Eroare AI: {e}")
        return "⚠️ Scuze, am întâmpinat o eroare. Încearcă din nou."

# === HANDLERE TELEGRAM ===
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler pentru comanda /start"""
    user = update.effective_user
    welcome_message = f"""
👋 Bun venit, {user.first_name}!

Eu sunt asistentul tău AI. Pot să:
• 💬 Vorbesc cu tine despre orice
• 🧠 Îți răspund la întrebări
• 📝 Te ajut cu sfaturi și idei

Trimite-mi un mesaj și îți voi răspunde!
    
Comenzi disponibile:
/start - Acest mesaj
/help - Ajutor și informații
/about - Despre acest bot
    """
    await update.message.reply_text(welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler pentru comanda /help"""
    help_text = """
🤖 **Cum să folosești acest bot:**

1. Scrie-mi orice mesaj și voi răspunde folosind AI
2. Poți să mă întrebi orice:
   - Întrebări generale
   - Sfaturi și recomandări
   - Explicații și definiții
   - Conversații libere

🔧 **Comenzi:**
/start - Mesaj de bun venit
/help - Acest mesaj de ajutor
/about - Informații despre bot

💡 **Sfaturi:**
• Folosește româna sau engleza
• Fii specific în întrebări pentru răspunsuri mai bune
• Botul nu reține contextul între mesaje (versiune simplă)
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler pentru comanda /about"""
    about_text = """
🤖 **AI Telegram Bot**
    
Versiune: 1.0
Creator: [Numele tău]
    
💻 **Tehnologii:**
• Python + python-telegram-bot
• OpenAI GPT API
• Deploy pe Render/Railway
    
🔐 **Confidențialitate:**
• Conversațiile sunt procesate de OpenAI
• Nu stochez mesaje permanente
• Cod sursă disponibil pe GitHub
    
✉️ Contact: [email-ul tău]
    """
    await update.message.reply_text(about_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler pentru mesaje normale"""
    user_message = update.message.text
    user = update.effective_user
    
    logger.info(f"📩 Mesaj de la {user.first_name}: {user_message}")
    
    # Trimite "typing" indicator
    await update.message.chat.send_action(action="typing")
    
    # Obține răspuns de la AI
    ai_response = await get_ai_response(user_message, user.first_name)
    
    # Trimite răspunsul
    await update.message.reply_text(ai_response)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler pentru erori"""
    logger.error(f"❌ Eroare: {context.error}")
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ A apărut o eroare. Te rog încearcă din nou."
        )

# === SETUP BOT ===
def setup_bot():
    """Configurează și returnează aplicația bot"""
    # Creează aplicația
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Adaugă handlere pentru comenzi
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))
    
    # Adaugă handler pentru mesaje text
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, 
        handle_message
    ))
    
    # Adaugă handler pentru erori
    application.add_error_handler(error_handler)
    
    return application

# === MAIN ===
async def main():
    """Funcția principală"""
    logger.info("🚀 Pornire AI Telegram Bot...")
    
    # Verifică variabilele de mediu
    logger.info(f"🤖 Bot Token: {'✅ Setat' if TELEGRAM_TOKEN else '❌ Lipsă'}")
    logger.info(f"🧠 OpenAI Key: {'✅ Setat' if OPENAI_API_KEY else '❌ Lipsă'}")
    logger.info(f"📊 Model AI: {AI_MODEL}")
    
    # Setup bot
    application = setup_bot()
    
    logger.info("✅ Bot-ul este gata!")
    logger.info("📡 Aștept mesaje...")
    
    # Pornește bot-ul cu polling
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    # Menține bot-ul activ
    await asyncio.Event().wait()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Bot oprit de utilizator")
    except Exception as e:
        logger.error(f"💥 Eroare critică: {e}")

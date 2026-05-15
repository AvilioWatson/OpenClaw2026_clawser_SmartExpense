import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler
from dotenv import load_dotenv
from assistant.assistant import AssistantAssistant
from tools.ocr_tool import OCRTool
from tools.calculator_tool import CalculatorTool
from tools.tool_registry import get_registry

# Explicitly find the .env file in the current directory
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path)

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Initialize Assistant
registry = get_registry()
if "ocr_extractor" not in registry.list_tools():
    registry.register(OCRTool())
if "calculator" not in registry.list_tools():
    registry.register(CalculatorTool())

assistant = AssistantAssistant()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Halo! Saya Asisten Keuangan Pribadi Anda.\n\n"
        "Kirimkan saya foto struk belanja Anda, dan saya akan menganalisisnya secara otonom "
        "berdasarkan Aturan Anggaran Pribadi Anda."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    user_id = str(update.effective_user.id)
    
    # Simple check if user is stating a goal
    if any(keyword in user_text.lower() for keyword in ["mau beli", "ingin beli", "target", "tabung"]):
        db_manager = DatabaseManager()
        db_manager.save_goal(user_id, user_text)
        await update.message.reply_text(
            f"📝 Baiklah, saya catat target Anda: '{user_text}'.\n\n"
            "Saya akan awasi struk belanja Anda agar tetap sejalan dengan target ini! 🧐"
        )
    else:
        await update.message.reply_text("Kirimkan foto struk belanja untuk saya audit, atau ceritakan target finansial Anda (misal: 'Saya mau beli sepatu').")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Get the highest resolution photo
    photo_file = await update.message.photo[-1].get_file()
    user_id = str(update.effective_user.id)
    
    # Send "Thinking" message
    status_msg = await update.message.reply_text("🤖 Sedang menganalisis struk... Mohon tunggu sebentar.")
    
    # Download photo
    temp_dir = "data"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
        
    photo_path = os.path.join(temp_dir, f"user_{update.effective_user.id}.jpg")
    await photo_file.download_to_drive(photo_path)
    
    try:
        # Run Assistant with user_id to fetch goals
        result = assistant.run(photo_path, user_id=user_id)
        
        # Format Text Response
        status_emoji = "✅" if result.get('status') == 'APPROVED' else "🔍" if result.get('status') == 'REVIEW' else "⚠️"
        
        response_text = (
            f"📊 **HASIL ANALISIS: {result.get('status')}** {status_emoji}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🏢 Toko: {result.get('merchant', 'Tidak dikenal')}\n"
            f"📅 Tanggal: {result.get('date', 'Tidak dikenal')}\n"
            f"💰 Total: Rp {result.get('calculated_total', 0):,}\n"
            f"🎯 Insight Score: {result.get('insight_score', 0)}/100\n\n"
        )
        
        if result.get('attention_reason'):
            response_text += f"❗ **Perhatian:** {result['attention_reason']}\n\n"
            
        if result.get('insights'):
            response_text += "💡 **INSIGHTS & ADVICE:**\n"
            for ins in result['insights']:
                response_text += f"• {ins}\n"
        
        response_text += "\n🛒 **DETAIL BARANG:**\n"
        for item in result.get('items', []):
            flag_emoji = "⚠️" if item.get('flag') else ""
            response_text += f"• {item['name']} - Rp {item['price']:,} {flag_emoji}\n"
            if item.get('budget_reason'):
                response_text += f"  └ _Reason: {item['budget_reason']}_\n"

        # Send comprehensive text result
        await status_msg.edit_text(response_text, parse_mode='Markdown')
            
    except Exception as e:
        logging.error(f"Error handling photo: {str(e)}")
        await status_msg.edit_text(f"❌ Maaf, terjadi kesalahan saat menganalisis: {str(e)}")
    
    finally:
        # Cleanup
        if os.path.exists(photo_path):
            os.remove(photo_path)

if __name__ == '__main__':
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("Error: TELEGRAM_BOT_TOKEN tidak ditemukan di .env")
    else:
        app = ApplicationBuilder().token(token).build()
        
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        print("Bot Telegram sedang berjalan...")
        app.run_polling()

import json
import re
import telegram
from brainus_ai import BrainusAI
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, ContextTypes, CommandHandler, CallbackQueryHandler
)
from dotenv import load_dotenv
import random
import threading
import http.server
import socketserver
import os

# 1. Create a dummy web server to trick Render's port scanner
def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    handler = http.server.SimpleHTTPRequestHandler
    
    # Allow the port to be reused immediately on restart
    socketserver.TCPServer.allow_reuse_address = True
    
    with socketserver.TCPServer(("0.0.0.0", port), handler) as httpd:
        httpd.serve_forever()

# 2. Run the dummy server on a separate thread so it doesn't block your script
threading.Thread(target=run_dummy_server, daemon=True).start()
print("Your actual script is now running...")

load_dotenv(dotenv_path='bot.env')
BRAINUS_API_KEY = os.getenv("BRAINUS_API_KEY")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

chem_topics = [    
    "Atomic Structure",
    "Structure and Bonding",
    "Chemical Calculations",
    "Gaseous State of Matter",
    "Energetics (Thermodynamics)",
    "Chemistry of s, p and d Block Elements",
    "Basic Organic Chemistry",
    "Hydrocarbons and Halotetranes",
    "Oxygen Containing Organic Compounds",
    "Nitrogen Containing Organic Compounds",
    "Chemical Kinetics",
    "Chemical Equilibrium",
    "Electrochemistry",
    "Industrial Chemistry and Environmental Pollution"
]

bio_topics = [
    "Introduction to Biology",
    "Chemical and Cellular Basis of Life",
    "Evolution and Diversity of Organisms",
    "Plant Form and Function",
    "Animal Form and Function",
    "Genetics",
    "Molecular Biology and Recombinant DNA Technology",
    "Environmental Biology",
    "Microbiology",
    "Applied Biology"
]


question = (
    f"Generate exactly one advanced-level poll question on the topic:{random.choice(chem_topics)} .Constraints:
Difficulty: Very high and syllabus-aligned only (strictly no basic questions).
Text Formatting: Plain text only (do not use LaTeX or markdown styling).
Character Limits: Question <= 250 characters; each answer choice <= 100 characters.
Output strictly raw valid JSON with no conversational text or markdown code blocks. Use the following exact schema structure:
\{
\"question\": \"Concise advanced question text (max 250 chars)\",
\"answers\": [\"Option 0\", \"Option 1\", \"Option 2\", \"Option 3\", \"Option 4\"],
\"answer\": 0
\}
Note: \"answers\" must contain exactly 5 tricky choices (max 100 chars each) with only 1 correct answer. \"answer\" must be the 0-based integer index of the correct choice.")

async def send_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🚀 Send Quiz Poll", callback_data="trigger_poll")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "⚙️ *Admin Control Panel*\n\nClick the button below to generate and dispatch a quiz poll:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "trigger_poll":
        try:
            await query.edit_message_text(text="🧠 Generating quiz from Brainus AI...")

            async with BrainusAI() as client:
                result = await client.query(query=question, store_id='default')
                json_response = result.answer
                print(json_response)
                cleaned_json = re.sub(r"^```(?:json)?\s*([\s\S]*?)\s*```$", r"\1", json_response.strip())

                response = json.loads(cleaned_json)
                poll_question = response['question']
                poll_answers = response['answers']
                poll_answer = response['answer']

            await context.bot.send_poll(
                chat_id=CHAT_ID,
                question=poll_question,
                options=poll_answers,
                is_anonymous=False,
                type=telegram.Poll.QUIZ,
                correct_option_id=poll_answer
            )

            await query.edit_message_text(text="✅ Quiz poll successfully sent to the group!")

        except Exception as e:
            await query.edit_message_text(text=f"❌ Error: {str(e)}")


def main():
    application = Application.builder().token(TOKEN).build()

    # Register your handlers
    application.add_handler(CommandHandler("send", send_command))
    application.add_handler(CallbackQueryHandler(button_callback))

    # Keeps the bot running continuously in the background listening for commands
    application.run_polling()


if __name__ == '__main__':
    main()


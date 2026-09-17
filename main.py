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


chem_question = (
    f"Generate exactly one advanced-level poll question on the topic:{random.choice(chem_topics)} .Constraints:"
    f"Difficulty: Very high and syllabus-aligned only (strictly no basic questions)."
    f"Text Formatting: Plain text only (do not use LaTeX or markdown styling)."
    f"Character Limits: Question <= 250 characters; each answer choice <= 100 characters."
    f"Output strictly raw valid JSON with no conversational text or markdown code blocks. Use the following exact schema structure:"
    "{"
    f"\"question\": \"Concise advanced question text (max 250 chars)\","
    f"\"answers\": [\"Option 0\", \"Option 1\", \"Option 2\", \"Option 3\", \"Option 4\"],"
    f"\"answer\": 0"
    "}"
    f"Note: \"answers\" must contain exactly 5 tricky choices (max 100 chars each) with only 1 correct answer. \"answer\" must be the 0-based integer index of the correct choice.")
bio_question = (
    f"Generate exactly one advanced-level poll question on the topic:{random.choice(bio_topics)} .Constraints:"
    f"Difficulty: Very high and syllabus-aligned only (strictly no basic questions)."
    f"Text Formatting: Plain text only (do not use LaTeX or markdown styling)."
    f"Character Limits: Question <= 250 characters; each answer choice <= 100 characters."
    f"Output strictly raw valid JSON with no conversational text or markdown code blocks. Use the following exact schema structure:"
    "{"
    f"\"question\": \"Concise advanced question text (max 250 chars)\","
    f"\"answers\": [\"Option 0\", \"Option 1\", \"Option 2\", \"Option 3\", \"Option 4\"],"
    f"\"answer\": 0"
    "}"
    f"Note: \"answers\" must contain exactly 5 tricky choices (max 100 chars each) with only 1 correct answer. \"answer\" must be the 0-based integer index of the correct choice.")

# send a chemistry poll quiz in the group
async def c_send_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🚀 Send Chemistry Quiz Poll", callback_data="chem_poll")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        text="⚙️ *Admin Control Panel*\n\nClick the button below to generate and dispatch a chemistry poll:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# send a bio quiz poll in the group
async def b_send_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(text="🚀 Send Bio Quiz Poll", callback_data="bio_poll")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        text="⚙️ *Admin Control Panel*\n\nClick the button below to generate and dispatch a bio poll:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == ("chem_poll" or "bio_poll"):
        try:
            await query.edit_message_text(text="🧠 Generating quiz from Brainus AI...")

            async with BrainusAI() as client:
                # decide if its a chemistry poll or a bio poll
                if query.data == "chem_poll":
                    result = await client.query(query=chem_question, store_id='default')
                elif query.data == "bio_poll":
                    result = await client.query(query=bio_question, store_id='default')

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
    application.add_handler(CommandHandler("chem_quiz", c_send_command))
    application.add_handler(CallbackQueryHandler(button_callback))

    application.add_handler(CommandHandler("bio_quiz", b_send_command))
    application.add_handler(CallbackQueryHandler(button_callback))


    # Keeps the bot running continuously in the background listening for commands
    application.run_polling()


if __name__ == '__main__':
    main()


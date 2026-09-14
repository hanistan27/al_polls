import os
import json
import asyncio
import re
import telegram
from brainus_ai import BrainusAI
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, ContextTypes, CommandHandler, CallbackQueryHandler
)
from dotenv import load_dotenv
import random

load_dotenv(dotenv_path='bot.env')
BRAINUS_API_KEY = os.getenv("BRAINUS_API_KEY")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
topics = ['general chemistry', 'inorganic chemistry', 'organic chemistry']
question = (f'I want you to generate  intermediate to advanced poll question(only one) on the topic '
            f'{topics[random.randrange(len(topics))]}. I want your answer to be in a specific format.Do not use any '
            f'type of latex formatting or anything.You will provide the answer in a dictionary format. I only want '
            f'the relevant question and answers. Not any extra bluff or thing.REMEMBER, YOU SHOULD ONLY PROVIDE THE '
            f'JSON FORMATTED FILE AND NOT OTHER TEXT'
            f'You should '
            f'not drag away from '
            f'the syllabus at all whatever the topic it is. Only ask questions from the syllabus. And the response should be in a dictionary format. your dictionary should have the keys "question" which represents the poll question and "answers" which represents a list of 5 tricky answers for the question with only one correct answer and an "answer" key which consists of the index of the correct answer from the list of available answers.')


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
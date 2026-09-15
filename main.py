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

load_dotenv(dotenv_path='bot.env')
BRAINUS_API_KEY = os.getenv("BRAINUS_API_KEY")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

topics = [
    "Hydrogen Spectrum",
    "Orbital Shapes",
    "Orbitals & Quantum Numbers",
    "Electron Configuration (Aufbau, Pauli, Hund's Rule, Condensed)",
    "Periodic Table Construction",
    "s & p Block Periodic Trends (Size, Ionization E, Electron Affinity, Electronegativity)",
    "Covalent Bonds (Lewis Structures)",
    "Dative Bonds",
    "VSEPR Theory",
    "Orbital Hybridization",
    "Double & Triple Bonds",
    "Resonance Structures",
    "Molecule Polarity (Electronegativity & Geometry)",
    "Dipole Moment",
    "Electronegativity Factors",
    "Ionic Bonds",
    "Metallic Bonds",
    "Secondary Interactions",
    "Oxidation Number (Redox Use)",
    "Inorganic Nomenclature",
    "Atomic Mass, Mole, Avogadro's Constant",
    "Molar Mass",
    "Chemical Formulae (Empirical & Molecular)",
    "Mixture Composition",
    "Solution Percentage Composition",
    "Molality & Molarity",
    "Balancing Reactions (Inspection, Redox, Nuclear)",
    "Solution Preparation",
    "Reaction Calculations",
    "s Block (Group 1: Trends, Reactions, Stability, Solubility, Flame Test)",
    "s Block (Group 2: Trends, Reactions, Stability, Solubility, Flame Test)",
    "p Block (Group 13: Trends, Al)",
    "p Block (Group 14: Trends, C, CO, CO2, Carbon Oxoacid)",
    "p Block (Group 15: Trends, N Chemistry, N Oxoacids, Ammonia/Ammonium)",
    "p Block (Group 16: Trends, Hydrides, O, S, O Cmpds, $$H_2O_2$$, S Cmpds, S Oxoacids)",
    "p Block (Group 17: Trends, Cmpds, Cl Reactions)",
    "p Block (Group 18: Trends, Cmpds)",
    "s & p Block Periodic Trends (Valence)",
    "Reaction Rate (Avg, Instant, Initial)",
    "Conc. Effect on Rate (0, 1st, 2nd Order Graphs)",
    "Reaction Order & Rate Constant Determination",
    "Surface Area Effect on Rate",
    "Catalyst Effect on Rate",
    "Reaction Mechanisms (Molecularity, Steps, Rate Laws, Pre-equilibrium)",
    "Reaction Energy Profiles",
    "Equilibrium Concept (Physical & Chemical)",
    "Equilibrium Law & Constant (Expressions, Extent, Forms, Gaseous, Heterogeneous, Multi-step)",
    "Equilibrium Direction & Calculations",
    "Equilibrium Concentration Calculation",
    "Factors Affecting Equilibrium",
    "Ionic Equilibrium (Acids, Bases, Salts, Conjugate Pairs, Ionization, Water Kw, pH, Ka/Kb, Ka-Kb Relation)",
    "Salt Hydrolysis & pH",
    "Common Ion Effect",
    "Volumetric Titrations",
    "Di/Polybasic Acids & Di/Polyacidic Bases",
    "Acid-Base Indicators",
    "Buffer Solutions",
    "Solubility Equilibria (Ksp, Calculations, Precipitation, Factors, pH Effect, Qual. Analysis)",
    "Phase Equilibria (Evaporation, SVP, BP, Enthalpy of Vaporization, Phase Diagrams)",
    "Binary Liquid-Vapour Eq. (Ideal & Immiscible)",
    "Partition/Distribution Coefficient",
    "Solution Conductivity Factors",
    "Equilibrium Electrodes (Metal-ion, Metal-salt, Gas, Redox)",
    "Electrochemical Cells (Construction, Electrode Potential Factors, Types)",
    "Electrolysis ($$H_2O$$, $$CuSO_4$$, $$NaCl$$, Molten $$NaCl$$, Quantitative)",
    "Alcohols (Structure, Properties, Reactions: O-H, C-O Cleavage, Elim, Ox)",
    "Phenols (Structure, Properties, Reactions: Acidity, O-H Cleavage, No SN)",
    "Phenol Benzene Reactivity ($$Br_2$$, Nitration)",
    "Aldehydes & Ketones (Structure, Properties, Reactions: Nucleophilic Add, Reduction, Oxidation)",
    "Carboxylic Acids (Structure, Properties, Reactions: O-H, C-O Cleavage, Reduction)",
    "Carboxylic Acid Derivative Reactions (Acid Chloride)"
]
question = (f'I want you to generate a poll question(only one)on the topic {random.choice(topics)}.'
            f'Do not use any type of latex formatting or anything.'
            f'You will provide the answer in a dictionary format.'
            f'I only want the relevant question and answers. '
            f'Not any extra bluff or thing.'
            f'REMEMBER, YOU SHOULD ONLY PROVIDE THE JSON FORMATTED FILE AND NOT OTHER TEXT.'
            f'You should not drag away from the syllabus at all whatever the topic it is.'
            f'Only ask questions from the syllabus.'
            f'And the response should  be in a dictionary format. '
            f'Your dictionary should have the keys "question" which represents '
            f'the poll question and "answers" which represents a list of 5 tricky answers for the question with only '
            f'one  correct answer(answers length <= 100. question length <= 256) '
            f'and an "answer" key which consists of the index of the correct answer from the list of available answers.')

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

print("Your actual script is now running...")
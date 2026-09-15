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
        print(f"Dummy server trick active on port {port}")
        httpd.serve_forever()

# 2. Run the dummy server on a separate thread so it doesn't block your script
threading.Thread(target=run_dummy_server, daemon=True).start()

load_dotenv(dotenv_path='bot.env')
BRAINUS_API_KEY = os.getenv("BRAINUS_API_KEY")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
topics = [
    "Hydrogen spectrum",
    "Shapes of orbitals",
    "Orbitals and quantum numbers",
    "Electron configuration (Aufbau principle, Pauli exclusion principle, Hund's rule, Condensed electron configurations)",
    "Building of the periodic table",
    "Periodic trends shown by s and p block elements (Sizes of atoms and ions, Ionization energy, Electron gain energy, Electronegativity)",
    "Covalent bonds (Lewis dot diagrams and Lewis dot-dash structures)",
    "Dative covalent bonds",
    "Valence Shell Electron Pair Repulsion theory (VSEPR theory)",
    "Hybridization of atomic orbitals",
    "Formation of double and triple bonds",
    "Resonance structures",
    "Effect of electronegativity and geometry on the polarity of molecules",
    "Dipole moment",
    "Factors affecting the magnitude of electronegativity",
    "Ionic bonds/ionic interactions",
    "Metallic bonds",
    "Secondary interactions",
    "Oxidation number (Basic rules, Use in redox reactions)",
    "Nomenclature of inorganic compounds",
    "Atomic mass, mole and Avogadro constant",
    "Molar mass",
    "Types of chemical formulae (Empirical and molecular formula determination)",
    "Composition of a substance in a mixture",
    "Percentage composition in a solution (homogeneous mixture)",
    "Molality and Molarity",
    "Balancing chemical reactions (Inspection method, Redox method, Simple nuclear reactions)",
    "Preparation of solutions",
    "Calculations based on chemical reactions",
    "s Block Elements (Group 1 elements: Group trends, Reactions, Thermal stability, Solubility of salts, Flame test)",
    "s Block Elements (Group 2 elements: Group trends, Reactions, Thermal stability, Solubility of salts, Flame test)",
    "p Block Elements (Group 13 elements: Group trends, Aluminium)",
    "p Block Elements (Group 14 elements: Group trends, Diamond and graphite, Carbon monoxide and carbon dioxide, Oxoacid of carbon)",
    "p Block Elements (Group 15 elements: Group trends, Chemistry of nitrogen, Oxoacids of nitrogen, Ammonia and ammonium salts)",
    "p Block Elements (Group 16 elements: Group trends, Hydrides, Oxygen, Sulphur, Oxygen containing compounds, Hydrogen peroxide, Sulphur containing compounds, Oxoacids of sulphur)",
    "p Block Elements (Group 17 elements: Group trends, Simple compounds, Reactions of chlorine)",
    "p Block Elements (Group 18 elements: Group trends, Simple compounds)",
    "Periodic trends shown by s and p block elements (Valence)",
    "Rate of reaction (Average, instantaneous and initial rates)",
    "Effect of concentration on reaction rate (Graphical representation for zero, first and second order reactions)",
    "Methods to determine order of a reaction and rate constant",
    "Effect of physical nature (surface area) on reaction rate",
    "Effect of catalysts on reaction rate",
    "Reaction mechanisms (Molecularity, Single step, Multistep, Rate laws, Consecutive reactions, Pre-equilibrium)",
    "Energy profiles of reactions",
    "Concept of equilibrium (Physical and chemical processes)",
    "Law of chemical equilibrium and equilibrium constant (Expression for general terms, Extent of reaction, Different forms, Gaseous systems, Heterogeneous equilibria, Multi-step reactions)",
    "Predicting direction of reaction and calculations based on equilibrium constant",
    "Calculating equilibrium concentrations",
    "Factors affecting equilibrium",
    "Ionic equilibrium in aqueous solutions (Acids, bases and salts, Conjugate acid-base pairs, Ionization, Ionization constant of water and its ionic product, pH scale, Weak acids/bases and their ionization constants, Relation between $$K_a$$ and $$K_b$$)",
    "Hydrolysis of salts and pH of their solutions",
    "Aqueous solutions containing a common ion",
    "Volumetric titrations",
    "Di- and polybasic acids and di- and polyacidic bases",
    "Acid-base indicators",
    "Buffer solutions",
    "Solubility equilibria (Ionic and covalent solutions, Solubility product, Calculations, Predicting precipitation, Factors affecting solubility, pH effect, Application in qualitative analysis)",
    "Equilibria in different phases (Evaporation, Saturated vapor pressure, Boiling point, Enthalpy of vaporization, Phase diagrams)",
    "Liquid - vapour equilibrium in binary liquid systems (Ideal mixtures, Immiscible liquid-liquid systems)",
    "Partition/Distribution coefficient",
    "Conductivity (Factors affecting solution conductivity)",
    "Electrodes in equilibrium (Metal-metal ion, Metal-insoluble salt, Gas, Redox electrodes)",
    "Electrochemical cells (Construction, Factors affecting electrode potential, Types)",
    "Electrolysis (Water, $$CuSO_4(aq)$$ with copper/inert electrodes, $$NaCl(aq)$$ with inert electrodes, Molten $$NaCl$$ with inert electrodes, Quantitative aspects)",
    "Structure, properties, and reactions of alcohols (Classification, Physical properties, Reactions involving O-H bond cleavage, Nucleophilic substitution involving C-O bond cleavage, Elimination, Oxidation)",
    "Structure, properties, and reactions of phenols (Acidity, Reactions involving O-H bond cleavage, Non-occurrence of nucleophilic substitution)",
    "Reactivity of the benzene ring in phenols (Reaction with $$Br_2$$, Nitration)",
    "Structure, properties, and reactions of aldehydes and ketones (Physical properties, Nucleophilic addition reactions - HCN, Grignard reagents, 2,4-DNP, Self-condensation, Reduction - $$LiAlH_4$$ or $$NaBH_4$$, Clemmenson reduction, Oxidation of aldehydes - Tollens reagent, Fehling solution, acidified potassium dichromate/chromic oxide/potassium permanganate)",
    "Structure, properties, and reactions of carboxylic acids (Physical properties, Reactions of -COOH group - O-H cleavage, C-O cleavage, Reduction with $$LiAlH_4$$)",
    "Reactions of carboxylic acid derivatives (Acid chloride reactions with aqueous sodium)"
]
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

print("Your actual script is now running...")
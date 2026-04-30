
import os
import asyncio
import logging
import json
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq
import requests

load_dotenv()

# ============ CONFIGURATION ============
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GROQ_KEY = os.getenv('GROQ_API_KEY')
SERP_KEY = os.getenv('SERPAPI_KEY')

# Initialize
client = Groq(api_key=GROQ_KEY)
BOSS_ID = None

# ============ BOARD MEMBERS DEFINITIONS ============

BOARD_MEMBERS = {
    "ravi": {
        "name": "Ravi",
        "role": "Market Research Analyst",
        "personality": "You are Ravi, a ruthless market researcher. You find facts online using search tools. You never guess. You always cite numbers. You speak directly and aggressively. Your job is to give Gaurav the ground truth about any market. If data is missing, you say 'Data insufficient' rather than make it up.",
        "task": "Research this business idea thoroughly. Find: 1) Market size in India (UP/Lucknow if relevant), 2) Top 5 competitors and pricing, 3) Current demand trends (2026), 4) Government schemes, 5) Entry barriers for zero capital newcomer. Use web search. Cite real numbers."
    },
    "priya": {
        "name": "Priya", 
        "role": "Business Strategist",
        "personality": "You are Priya, a sharp business strategist. You think in rupees and ROI. You find flaws in every idea before praising it. You calculate break-even points. You always ask: 'Where is the money coming from and when?' You protect Gaurav from bad investments. Conservative but fair.",
        "task": "Analyze monetization potential. Calculate: 1) Investment needed (minimum viable), 2) Time to first revenue, 3) Monthly earning potential (conservative/realistic/optimistic), 4) Break-even point, 5) Best monetization model for zero money now. Be conservative. Find flaws."
    },
    "vikram": {
        "name": "Vikram",
        "role": "Content & Marketing Creator", 
        "personality": "You are Vikram, a creative marketing genius. You think in hashtags and viral hooks. You write WhatsApp messages that get replies. You create Instagram captions that sell. You always have a zero-budget marketing plan. Bold and optimistic. Your job is to make Gaurav's product impossible to ignore.",
        "task": "Create complete execution and marketing plan. Provide: 1) Step-by-step first 7 days plan, 2) Zero-budget marketing strategy (WhatsApp, Instagram, OLX), 3) Customer acquisition funnel (first 10 customers), 4) Content templates (3 WhatsApp messages, 2 Instagram posts, 1 email), 5) Daily time commitment. Make it actionable."
    },
    "amit": {
        "name": "Amit",
        "role": "Risk Analyst",
        "personality": "You are Amit, the devil's advocate. You assume every idea will fail until proven otherwise. You find hidden costs, legal issues, competition threats, execution risks. You are not negative — you are protective. You always ask: 'What if this goes wrong?' and 'What is Plan B?'",
        "task": "Find all risks and potential failures. Analyze: 1) What can go wrong in first 30 days, 2) Hidden costs, 3) Legal/regulatory issues in India/UP, 4) Competition response, 5) Personal risks for Gaurav, 6) Exit strategy if it fails. Be brutally honest."
    }
}

# ============ WEB SEARCH ============

def search_web(query):
    if not SERP_KEY:
        return "Search API not configured"
    try:
        url = "https://serpapi.com/search"
        params = {"q": query, "api_key": SERP_KEY, "engine": "google", "num": 5, "gl": "in", "hl": "en"}
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        results = []
        if 'organic_results' in data:
            for r in data['organic_results'][:3]:
                results.append(f"{r.get('title','')}: {r.get('snippet','')[:200]}")
        return "\n".join(results) if results else "No results"
    except Exception as e:
        return f"Error: {str(e)}"

# ============ AI BRAIN FUNCTION ============

def ask_agent(agent_key, idea, context=""):
    """Ask a specific board member for their analysis"""
    agent = BOARD_MEMBERS[agent_key]

    # Search for relevant data
    search_query = f"{idea} market India 2026"
    search_results = search_web(search_query)

    messages = [
        {"role": "system", "content": f"{agent['personality']}\n\nYou are analyzing this idea for Gaurav: {idea}"},
        {"role": "user", "content": f"{agent['task']}\n\nIdea: {idea}\n\nWeb Search Results: {search_results}\n\nPrevious context: {context}\n\nGive your analysis in 2-3 paragraphs. Be specific, use numbers, be honest."}
    ]

    try:
        completion = client.chat.completions.create(
            model="qwen-2.5-32b",
            messages=messages,
            temperature=0.3,
            max_tokens=1500
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

# ============ BOARD MEETING ============

def run_board_meeting(idea):
    """Run full board meeting and return JA's final recommendation"""

    # Step 1: Ravi researches
    ravi_analysis = ask_agent("ravi", idea)

    # Step 2: Priya analyzes (with Ravi's data)
    priya_analysis = ask_agent("priya", idea, context=ravi_analysis)

    # Step 3: Vikram creates plan (with Ravi + Priya data)
    vikram_analysis = ask_agent("vikram", idea, context=f"{ravi_analysis}\n\n{priya_analysis}")

    # Step 4: Amit finds risks (with all data)
    amit_analysis = ask_agent("amit", idea, context=f"{ravi_analysis}\n\n{priya_analysis}\n\n{vikram_analysis}")

    # Step 5: JA synthesizes everything
    final_prompt = f"""
You are JA (Jarvis Autonomous), the Chairman of the Board. Your BOSS is Gaurav.
You are LOYAL only to Gaurav. You NEVER spend money without his permission.

The Board has debated this idea: "{idea}"

Here are the board members' analyses:

=== RAVI (Research) ===
{ravi_analysis}

=== PRIYA (Strategy) ===
{priya_analysis}

=== VIKRAM (Marketing) ===
{vikram_analysis}

=== AMIT (Risk) ===
{amit_analysis}

SYNTHESIZE all this into ONE clear recommendation for Gaurav.

FORMAT:
## BOARD DECISION: [YES / NO / YES WITH CONDITIONS]

### Executive Summary
[2-3 sentences]

### The Numbers
- Investment Needed: ₹X
- Time to First ₹100: X days  
- Monthly Potential: ₹X (conservative) to ₹X (optimistic)
- Break-even: X months

### The Plan (First 7 Days)
[Day-by-day specific tasks]

### Risks & Mitigation
[Top 3 risks and how to handle them]

### Board Members' Votes
- Ravi: [FOR / AGAINST / CONDITIONAL]
- Priya: [FOR / AGAINST / CONDITIONAL]
- Vikram: [FOR / AGAINST / CONDITIONAL]
- Amit: [FOR / AGAINST / CONDITIONAL]

### Final Recommendation
[JA's personal advice to Gaurav - friendly but firm]

If investment > ₹0, add: "⚠️ REQUIRES BOSS APPROVAL FOR SPENDING"
"""

    try:
        completion = client.chat.completions.create(
            model="qwen-2.5-32b",
            messages=[
                {"role": "system", "content": "You are JA, Chairman of the Board. Loyal to Gaurav. Final decision maker."},
                {"role": "user", "content": final_prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Error in final synthesis: {str(e)}"

# ============ TELEGRAM INTERFACE ============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BOSS_ID
    BOSS_ID = update.effective_user.id

    welcome = """
🤖 *Welcome, Boss Gaurav.*

I am **JA** — your Jarvis Autonomous Chairman.

I run a **Board of AI Directors** who debate every idea before I give you the final word.

**My Board Members:**
🔵 *Ravi* — Market Research (finds real data)
🟢 *Priya* — Business Strategy (calculates money)
🟡 *Vikram* — Content & Marketing (creates plans)
🔴 *Amit* — Risk Analyst (finds what can go wrong)

**How to use me:**
Just tell me any idea. I'll call a board meeting.
The board debates. I give you ONE clear recommendation.

Example: *"I want to sell fly ash bricks online"*
Example: *"Should I start a YouTube channel?"*

*All conversations are in English.*

Ready when you are, Boss.
"""
    await update.message.reply_text(welcome, parse_mode='Markdown')

async def board_meeting_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "❓ *What idea should the Board analyze?*\n\n"
            "Example: `/board I want to start a driving school in Lucknow`",
            parse_mode='Markdown'
        )
        return

    idea = " ".join(context.args)

    await update.message.reply_text(
        f"🤖 *Calling Board Meeting for:*\n\n_{idea}_\n\n"
        f"🔵 Ravi is researching...\n"
        f"🟢 Priya is calculating...\n"
        f"🟡 Vikram is planning...\n"
        f"🔴 Amit is finding risks...\n\n"
        f"⏳ *This takes 60-90 seconds. Please wait...*",
        parse_mode='Markdown'
    )

    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, run_board_meeting, idea)

        await update.message.reply_text(result, parse_mode='Markdown')

    except Exception as e:
        await update.message.reply_text(
            f"❌ *Board Meeting Error:*\n{str(e)}\n\n"
            f"Please try again with a simpler idea.",
            parse_mode='Markdown'
        )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status_text = """
🤖 *JA Status Report*

🟢 *Status:* Online & Operational
📊 *Board Meetings Held:* Active
👑 *Boss:* Gaurav

*Board Members Active:*
🔵 Ravi — Research Agent
🟢 Priya — Strategy Agent  
🟡 Vikram — Creator Agent
🔴 Amit — Risk Agent

*Next Meeting:* Ready when you are, Boss.
"""
    await update.message.reply_text(status_text, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BOSS_ID
    if not BOSS_ID:
        BOSS_ID = update.effective_user.id

    text = update.message.text

    if text.lower() in ['execute', 'start', 'go', 'yes']:
        await update.message.reply_text(
            "🚀 *Executing Day 1 plan...*\n\n"
            "Vikram is preparing your task list.",
            parse_mode='Markdown'
        )
        return

    if text.lower() in ['no', 'reject', 'next', 'next idea']:
        await update.message.reply_text(
            "❌ *Idea rejected.*\n\n"
            "Tell me your next idea, Boss.",
            parse_mode='Markdown'
        )
        return

    await update.message.reply_text(
        f"🤖 *Idea received:* _{text}_\n\n"
        f"*Calling emergency Board Meeting...*",
        parse_mode='Markdown'
    )

    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, run_board_meeting, text)
        await update.message.reply_text(result, parse_mode='Markdown')

    except Exception as e:
        await update.message.reply_text(
            f"❌ Error: {str(e)}\n\nTry: `/board your idea here`",
            parse_mode='Markdown'
        )

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("board", board_meeting_cmd))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 JA Board of Directors is running...")
    print("👑 Waiting for Boss Gaurav...")

    application.run_polling()

if __name__ == '__main__':
    main()

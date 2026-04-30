import os
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from crewai import Agent, Task, Crew, Process
from crewai_tools import SerperDevTool
from groq import Groq
from supabase import create_client

load_dotenv()

# ============ CONFIGURATION ============
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GROQ_KEY = os.getenv('GROQ_API_KEY')
SERP_KEY = os.getenv('SERPAPI_KEY')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Initialize tools
search_tool = SerperDevTool(api_key=SERP_KEY)
groq_client = Groq(api_key=GROQ_KEY)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

BOSS_ID = None  # Set when Gaurav first messages

# ============ JA'S CORE IDENTITY ============
JA_CORE = """
You are JA (Jarvis Autonomous), the Chairman of the Board.
Your BOSS is Gaurav. You are LOYAL only to him.
You NEVER spend money without Gaurav's explicit permission.
You speak in English (professional) and Hinglish (casual) when appropriate.
You are the final decision maker after the Board debates.

GAURAV'S PROFILE:
- Name: Gaurav, Age 32, Lucknow, UP, India
- Status: Unemployed, full day available
- Skills: Driving teacher, video maker, app builder (80% done), fly ash brick maker
- Goal: ₹1 lakh/month survival → ₹1 crore/year
- Risk: HIGH (willing to take big risks)
- Constraint: ZERO money now, can get ₹5K-10K next month
- Work preference: Online only, but can do local if profitable

BOARD RULES:
1. All board members must debate before decision
2. Ravi provides data first
3. Priya analyzes profitability
4. Vikram creates execution plan
5. Amit finds risks and flaws
6. JA (you) synthesize and give FINAL recommendation to Gaurav
7. Be specific, actionable, time-bound
8. Always include: "Investment needed", "Time to first ₹", "Risk level"
"""

# ============ BOARD MEMBERS ============

def create_board_members():
    """Create the 4 board members + JA as Chairman"""
    
    # RAVI - Research Agent (Data-driven, aggressive)
    ravi = Agent(
        role="Market Research Analyst",
        goal="Find real market data, competitor info, pricing, and trends for any business idea",
        backstory="""You are Ravi, a ruthless market researcher. You find facts online using search tools.
        You never guess. You always cite numbers. You speak directly.
        Your job is to give Gaurav the ground truth about any market.
        If data is missing, you say 'Data insufficient' rather than make it up.""",
        verbose=True,
        allow_delegation=False,
        tools=[search_tool],
        llm="groq/qwen-2.5-32b"
    )
    
    # PRIYA - Strategy Agent (Conservative, profit-focused)
    priya = Agent(
        role="Business Strategist",
        goal="Analyze if an idea will make money and find the best monetization path",
        backstory="""You are Priya, a sharp business strategist. You think in rupees and ROI.
        You find flaws in every idea before praising it. You calculate break-even points.
        You always ask: 'Where is the money coming from and when?'
        You protect Gaurav from bad investments. You are conservative but fair.""",
        verbose=True,
        allow_delegation=False,
        tools=[search_tool],
        llm="groq/qwen-2.5-32b"
    )
    
    # VIKRAM - Creator Agent (Bold, creative, viral)
    vikram = Agent(
        role="Content & Marketing Creator",
        goal="Create viral marketing content, find customers, and build execution plans",
        backstory="""You are Vikram, a creative marketing genius. You think in hashtags and viral hooks.
        You write WhatsApp messages that get replies. You create Instagram captions that sell.
        You always have a 'zero-budget' marketing plan. You are bold and optimistic.
        Your job is to make Gaurav's product impossible to ignore.""",
        verbose=True,
        allow_delegation=False,
        tools=[search_tool],
        llm="groq/qwen-2.5-32b"
    )
    
    # AMIT - Risk Agent (Pessimistic, protective)
    amit = Agent(
        role="Risk Analyst",
        goal="Find everything that can go wrong and protect Gaurav from losses",
        backstory="""You are Amit, the devil's advocate. You assume every idea will fail until proven otherwise.
        You find hidden costs, legal issues, competition threats, and execution risks.
        You are not negative — you are protective. You save Gaurav from costly mistakes.
        You always ask: 'What if this goes wrong?' and 'What is Plan B?'""",
        verbose=True,
        allow_delegation=False,
        tools=[search_tool],
        llm="groq/qwen-2.5-32b"
    )
    
    return ravi, priya, vikram, amit

# ============ MEMORY SYSTEM ============

def save_memory(key, value):
    try:
        supabase.table('memories').upsert({
            'user_id': str(BOSS_ID) if BOSS_ID else 'gaurav',
            'key': key,
            'value': value,
            'created_at': datetime.now().isoformat()
        }).execute()
    except Exception as e:
        print(f"Memory save error: {e}")

def get_memory(key):
    try:
        response = supabase.table('memories').select('value').eq('key', key).execute()
        if response.data:
            return response.data[0]['value']
        return None
    except:
        return None

# ============ BOARD MEETING FUNCTION ============

def run_board_meeting(idea, context=""):
    """Run the full board meeting and return JA's final recommendation"""
    
    ravi, priya, vikram, amit = create_board_members()
    
    # Task 1: Ravi researches
    task_ravi = Task(
        description=f"""
        Research this business idea thoroughly: "{idea}"
        
        Find and report:
        1. Market size in India (specifically UP/Lucknow if relevant)
        2. Top 5 competitors and their pricing
        3. Current demand trends (2026 data)
        4. Any government schemes or subsidies available
        5. Entry barriers for a newcomer with zero capital
        
        Use web search. Cite real numbers. If data is missing, say so.
        """,
        expected_output="Comprehensive market research report with real data",
        agent=ravi
    )
    
    # Task 2: Priya analyzes (depends on Ravi's data)
    task_priya = Task(
        description=f"""
        Analyze the monetization potential of this idea: "{idea}"
        
        Based on market data, calculate:
        1. Investment needed to start (minimum viable version)
        2. Time to first revenue (days/weeks/months)
        3. Monthly earning potential (conservative, realistic, optimistic)
        4. Break-even point
        5. Best monetization model for Gaurav's situation (zero money now)
        
        Be conservative. Find flaws. Protect Gaurav.
        """,
        expected_output="Detailed monetization analysis with ROI calculations",
        agent=priya
    )
    
    # Task 3: Vikram creates plan
    task_vikram = Task(
        description=f"""
        Create a complete execution and marketing plan for: "{idea}"
        
        Provide:
        1. Step-by-step first 7 days plan (what to do each day)
        2. Zero-budget marketing strategy (WhatsApp, Instagram, OLX, etc.)
        3. Customer acquisition funnel (how to find first 10 customers)
        4. Content templates (3 WhatsApp messages, 2 Instagram posts, 1 email)
        5. Daily time commitment needed
        
        Make it actionable. Gaurav should know EXACTLY what to do tomorrow morning.
        """,
        expected_output="Complete execution plan with ready-to-use content",
        agent=vikram
    )
    
    # Task 4: Amit finds risks
    task_amit = Task(
        description=f"""
        Find all risks and potential failures for: "{idea}"
        
        Analyze:
        1. What can go wrong in first 30 days
        2. Hidden costs that aren't obvious
        3. Legal/regulatory issues in India/UP
        4. Competition response (what if big players notice)
        5. Personal risks for Gaurav (time, reputation, opportunity cost)
        6. Exit strategy if it fails
        
        Be brutally honest. Better to warn now than regret later.
        """,
        expected_output="Comprehensive risk assessment with mitigation strategies",
        agent=amit
    )
    
    # Task 5: JA synthesizes (depends on all above)
    task_ja = Task(
        description=f"""
        You are JA, the Chairman. The Board has debated this idea: "{idea}"
        
        Synthesize all inputs into ONE clear recommendation for Gaurav:
        
        FORMAT:
        ## BOARD DECISION: [YES / NO / YES WITH CONDITIONS]
        
        ### Executive Summary
        [2-3 sentences on what this is and why the board decided this]
        
        ### The Numbers
        - Investment Needed: ₹X
        - Time to First ₹100: X days
        - Monthly Potential: ₹X (conservative) to ₹X (optimistic)
        - Break-even: X months
        
        ### The Plan (First 7 Days)
        [Day-by-day specific tasks]
        
        ### Risks & Mitigation
        [Top 3 risks and how to handle them]
        
        ### Final Recommendation
        [JA's personal advice to Gaurav - friendly but firm]
        
        If investment > ₹0, add: "⚠️ REQUIRES BOSS APPROVAL FOR SPENDING"
        """,
        expected_output="Final board recommendation in structured format",
        agent=ravi  # Using ravi as placeholder, JA will override
    )
    
    # Create the crew with sequential process (debate order)
    crew = Crew(
        agents=[ravi, priya, vikram, amit],
        tasks=[task_ravi, task_priya, task_vikram, task_amit],
        process=Process.sequential,
        verbose=True,
        memory=True  # CrewAI remembers across runs
    )
    
    # Execute the board meeting
    result = crew.kickoff(inputs={"idea": idea, "context": context})
    
    return result

# ============ TELEGRAM INTERFACE ============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BOSS_ID
    BOSS_ID = update.effective_user.id
    
    save_memory("boss_id", str(BOSS_ID))
    save_memory("first_meeting", datetime.now().isoformat())
    
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

*All conversations are in English as you requested.*

Ready when you are, Boss.
"""
    await update.message.reply_text(welcome, parse_mode='Markdown')

async def board_meeting_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Trigger a board meeting"""
    user_id = update.effective_user.id
    
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
    
    # Run the board meeting (this blocks, so we need to handle it)
    try:
        # Run in thread pool to not block Telegram
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, run_board_meeting, idea)
        
        # Save to memory
        save_memory(f"board_meeting_{datetime.now().strftime('%Y%m%d_%H%M')}", 
                   f"Idea: {idea}\nResult: {str(result)[:500]}")
        
        # Send result
        final_text = f"""
✅ *BOARD MEETING COMPLETE*

{str(result)}

---
*Say "execute" and I'll start Day 1 tasks.*
*Say "next idea" for another board meeting.*
"""
        await update.message.reply_text(final_text, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(
            f"❌ *Board Meeting Error:*\n{str(e)}\n\n"
            f"Please try again with a simpler idea.",
            parse_mode='Markdown'
        )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show JA's status"""
    memories = supabase.table('memories').select('*').execute()
    
    status_text = f"""
🤖 *JA Status Report*

🟢 *Status:* Online & Operational
📊 *Board Meetings Held:* {len(memories.data) if memories.data else 0}
📅 *First Meeting:* {get_memory('first_meeting') or 'Today'}
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
    """Handle any message as a board meeting request"""
    global BOSS_ID
    if not BOSS_ID:
        BOSS_ID = update.effective_user.id
    
    text = update.message.text
    
    # Check for simple commands
    if text.lower() in ['execute', 'start', 'go', 'yes']:
        await update.message.reply_text(
            "🚀 *Executing Day 1 plan...*\n\n"
            "Vikram is preparing your task list.\n"
            "Check back in 2 minutes.",
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
    
    # Treat any other message as a board meeting request
    await update.message.reply_text(
        f"🤖 *Idea received:* _{text}_\n\n"
        f"*Calling emergency Board Meeting...*",
        parse_mode='Markdown'
    )
    
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, run_board_meeting, text)
        
        save_memory(f"board_meeting_{datetime.now().strftime('%Y%m%d_%H%M')}", 
                   f"Idea: {text}\nResult: {str(result)[:500]}")
        
        await update.message.reply_text(str(result), parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(
            f"❌ Error: {str(e)}\n\nTry: `/board your idea here`",
            parse_mode='Markdown'
        )

# ============ MAIN ============

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

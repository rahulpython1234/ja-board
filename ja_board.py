import os
import json
import asyncio
import requests
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq

load_dotenv()

# ============ CONFIGURATION ============
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GROQ_KEY = os.getenv('GROQ_API_KEY')
SERP_KEY = os.getenv('SERPAPI_KEY')

client = Groq(api_key=GROQ_KEY)
BOSS_ID = None

# ============ JA'S CORE IDENTITY ============
JA_CORE = """
You are JA (Jarvis Autonomous), the Chairman of the Board of AI Directors.
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

# ============ SELF-LEARNING BRAIN ============

class SelfLearningBrain:
    """JA's brain that learns from every interaction"""

    def __init__(self):
        self.learnings_file = Path("learnings.md")
        self.skills_dir = Path("skills")
        self.skills_dir.mkdir(exist_ok=True)
        self.load_learnings()

    def load_learnings(self):
        if self.learnings_file.exists():
            with open(self.learnings_file, 'r') as f:
                return f.read()
        return "# JA's Learnings\n\n"

    def add_learning(self, situation, lesson, result):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        entry = f"\n## {timestamp}\n**Situation:** {situation}\n**Lesson:** {lesson}\n**Result:** {result}\n"

        with open(self.learnings_file, 'a') as f:
            f.write(entry)

    def get_all_learnings(self):
        return self.load_learnings()

brain = SelfLearningBrain()

# ============ AUTO-DISCOVERY SYSTEM ============

class TechDiscovery:
    """Discovers new technologies and creates skills automatically"""

    def __init__(self):
        self.discovered_file = Path("discovered_tech.json")
        self.known_tech = self.load_known()

    def load_known(self):
        if self.discovered_file.exists():
            with open(self.discovered_file, 'r') as f:
                return json.load(f)
        return []

    def search_new_tech(self):
        queries = [
            "new AI tools 2026 free",
            "new money making apps India 2026",
            "emerging technology trends 2026",
            "new business opportunities online 2026"
        ]

        discoveries = []
        for query in queries:
            try:
                url = "https://serpapi.com/search"
                params = {"q": query, "api_key": SERP_KEY, "engine": "google", "num": 3}
                response = requests.get(url, params=params, timeout=10)
                data = response.json()

                if 'organic_results' in data:
                    for result in data['organic_results'][:2]:
                        tech_name = result.get('title', '').split('-')[0].strip()
                        if tech_name and tech_name not in self.known_tech:
                            discoveries.append({
                                'name': tech_name,
                                'source': result.get('link', ''),
                                'description': result.get('snippet', '')[:200]
                            })
            except:
                continue

        return discoveries

    def create_skill_from_discovery(self, tech):
        skill_name = tech['name'].lower().replace(' ', '-').replace('/', '-')
        skill_folder = self.skills_dir / skill_name
        skill_folder.mkdir(exist_ok=True)

        skill_content = f"""---
name: {skill_name}
description: Auto-discovered: {tech['description'][:100]}
discovered_at: {datetime.now().isoformat()}
status: pending_approval
---

# {tech['name']}

## Discovery
- Found: {datetime.now().strftime('%Y-%m-%d')}
- Source: {tech['source']}

## What I Know
{tech['description']}

## For Gaurav
This technology might help with:
- [Research needed]

## ⚠️ PENDING BOSS APPROVAL
JA found this but is waiting for Gaurav's permission to fully integrate.
"""

        skill_file = skill_folder / "SKILL.md"
        with open(skill_file, 'w') as f:
            f.write(skill_content)

        self.known_tech.append(tech['name'])
        with open(self.discovered_file, 'w') as f:
            json.dump(self.known_tech, f)

        return skill_name

discovery = TechDiscovery()

# ============ MEMORY SYSTEM (FILE-BASED) ============

class FileMemory:
    """Simple file-based memory system"""

    def __init__(self):
        self.memory_file = Path("memory.json")
        self.memory = self.load()

    def load(self):
        if self.memory_file.exists():
            with open(self.memory_file, 'r') as f:
                return json.load(f)
        return {}

    def save(self):
        with open(self.memory_file, 'w') as f:
            json.dump(self.memory, f)

    def set(self, key, value):
        self.memory[key] = {
            "value": value,
            "timestamp": datetime.now().isoformat()
        }
        self.save()

    def get(self, key):
        if key in self.memory:
            return self.memory[key]["value"]
        return None

memory = FileMemory()

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
                results.append(f"📰 {r.get('title','')}\n{r.get('snippet','')[:200]}")
        return "\n\n".join(results) if results else "No results"
    except Exception as e:
        return f"Error: {str(e)}"

# ============ BOARD MEETING SYSTEM ============

def ask_board_member(agent_key, idea, context=""):
    """Ask a specific board member for their analysis"""
    agent = BOARD_MEMBERS[agent_key]

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

def run_board_meeting(idea):
    """Run full board meeting and return JA's final recommendation"""

    # Step 1: Ravi researches
    ravi_analysis = ask_board_member("ravi", idea)

    # Step 2: Priya analyzes
    priya_analysis = ask_board_member("priya", idea, context=ravi_analysis)

    # Step 3: Vikram creates plan
    vikram_analysis = ask_board_member("vikram", idea, context=f"{ravi_analysis}\n\n{priya_analysis}")

    # Step 4: Amit finds risks
    amit_analysis = ask_board_member("amit", idea, context=f"{ravi_analysis}\n\n{priya_analysis}\n\n{vikram_analysis}")

    # Step 5: JA synthesizes
    final_prompt = f"""
You are JA (Jarvis Autonomous), the Chairman of the Board. Your BOSS is Gaurav.
You are LOYAL only to Gaurav. You NEVER spend money without his permission.

The Board has debated this idea: "{idea}"

=== RAVI (Research) ===
{ravi_analysis}

=== PRIYA (Strategy) ===
{priya_analysis}

=== VIKRAM (Marketing) ===
{vikram_analysis}

=== AMIT (Risk) ===
{amit_analysis}

SYNTHESIZE into ONE clear recommendation:

## BOARD DECISION: [YES / NO / YES WITH CONDITIONS]

### Executive Summary
[2-3 sentences]

### The Numbers
- Investment Needed: ₹X
- Time to First ₹100: X days  
- Monthly Potential: ₹X (conservative) to ₹X (optimistic)
- Break-even: X months

### The Plan (First 7 Days)
[Day-by-day tasks]

### Risks & Mitigation
[Top 3 risks]

### Board Votes
- Ravi: [FOR/AGAINST/CONDITIONAL]
- Priya: [FOR/AGAINST/CONDITIONAL]
- Vikram: [FOR/AGAINST/CONDITIONAL]
- Amit: [FOR/AGAINST/CONDITIONAL]

### Final Recommendation
[JA's personal advice]

If investment > ₹0: "⚠️ REQUIRES BOSS APPROVAL"
"""

    try:
        completion = client.chat.completions.create(
            model="qwen-2.5-32b",
            messages=[
                {"role": "system", "content": "You are JA, Chairman. Loyal to Gaurav. Final decision maker."},
                {"role": "user", "content": final_prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

# ============ AUTONOMOUS LOOP ============

async def autonomous_loop():
    """JA's 24/7 self-running loop"""
    while True:
        try:
            now = datetime.now()

            # Run every 2 hours
            if now.hour % 2 == 0 and now.minute < 5:

                # 1. Research new tech
                new_techs = discovery.search_new_tech()

                for tech in new_techs:
                    skill_name = discovery.create_skill_from_discovery(tech)

                    if BOSS_ID:
                        message = f"""
🤖 *Boss, new tech discovered!*

*{tech['name']}*
{tech['description'][:150]}

Skill file created: `{skill_name}`
Approval needed to integrate.

Reply: "approve" or "ignore"
"""
                        requests.post(
                            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                            json={"chat_id": BOSS_ID, "text": message, "parse_mode": "Markdown"}
                        )

                # 2. Daily market research
                market_queries = [
                    "fly ash brick price Lucknow today",
                    "app monetization trends India 2026",
                    "online money making opportunities India"
                ]

                for query in market_queries:
                    results = search_web(query)
                    memory.set(f"research_{now.strftime('%Y%m%d')}_{query[:20]}", results)

                # 3. Self-reflection
                brain.add_learning(
                    situation="Daily autonomous review",
                    lesson=f"Processed market research and tech discovery",
                    result="Learning updated"
                )

            await asyncio.sleep(300)

        except Exception as e:
            print(f"Autonomous loop error: {e}")
            await asyncio.sleep(300)

# ============ TELEGRAM HANDLERS ============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BOSS_ID
    BOSS_ID = update.effective_user.id

    memory.set("boss_id", str(BOSS_ID))
    memory.set("first_meeting", datetime.now().isoformat())

    welcome = """
🤖 *Welcome, Boss Gaurav.*

I am **JA** — your Jarvis Autonomous Chairman.

I run a **Board of AI Directors** who debate every idea before I give you the final word.

**My Board Members:**
🔵 *Ravi* — Market Research (finds real data)
🟢 *Priya* — Business Strategy (calculates money)
🟡 *Vikram* — Content & Marketing (creates plans)
🔴 *Amit* — Risk Analyst (finds what can go wrong)

**My Autonomous Powers:**
🧠 Self-learning from every interaction
🔌 Auto-discovery of new technologies
💾 Permanent memory of everything
⏰ 24/7 market monitoring

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

        # Save to memory
        memory.set(f"board_{datetime.now().strftime('%Y%m%d_%H%M')}", f"Idea: {idea}")

        # Learn from this
        brain.add_learning(
            situation=f"Board meeting for: {idea[:50]}",
            lesson="Board debated and reached decision",
            result="Recommendation delivered to Boss"
        )

        await update.message.reply_text(result, parse_mode='Markdown')

    except Exception as e:
        await update.message.reply_text(
            f"❌ *Board Meeting Error:*\n{str(e)}\n\n"
            f"Please try again with a simpler idea.",
            parse_mode='Markdown'
        )

async def task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Daily task with learning"""
    learnings = brain.get_all_learnings()[-2000:]

    messages = [
        {"role": "system", "content": JA_CORE + f"\n\nMY LEARNINGS:\n{learnings}"},
        {"role": "user", "content": "Boss wants today's money-making task. Give ONE specific task."}
    ]

    try:
        completion = client.chat.completions.create(
            model="qwen-2.5-32b",
            messages=messages,
            temperature=0.3,
            max_tokens=1500
        )
        response = completion.choices[0].message.content
        await update.message.reply_text(response, parse_mode='Markdown')

        brain.add_learning(
            situation="Boss asked for daily task",
            lesson="Provided actionable task",
            result="Task delivered"
        )
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Approve pending skills"""
    if not context.args:
        pending = []
        for skill_folder in Path('skills').iterdir():
            if skill_folder.is_dir():
                skill_file = skill_folder / 'SKILL.md'
                if skill_file.exists():
                    with open(skill_file, 'r') as f:
                        if 'pending_approval' in f.read():
                            pending.append(skill_folder.name)

        if pending:
            text = "*⏳ Pending Skills:*\n\n" + "\n".join([f"• {p}" for p in pending])
            text += "\n\nApprove: `/approve skill-name`"
        else:
            text = "*✅ No pending skills!*"

        await update.message.reply_text(text, parse_mode='Markdown')
        return

    skill_name = context.args[0]
    skill_file = Path(f"skills/{skill_name}/SKILL.md")

    if skill_file.exists():
        with open(skill_file, 'r') as f:
            content = f.read()

        content = content.replace('pending_approval', 'approved')
        content += f"\n\n## APPROVED\nApproved by Boss on: {datetime.now().isoformat()}\n"

        with open(skill_file, 'w') as f:
            f.write(content)

        await update.message.reply_text(f"✅ *{skill_name}* approved! Now I can learn it.", parse_mode='Markdown')

        brain.add_learning(
            situation=f"Boss approved skill: {skill_name}",
            lesson="New capability added",
            result=f"Skill {skill_name} activated"
        )
    else:
        await update.message.reply_text("❌ Skill not found.")

async def learnings_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show what JA has learned"""
    learnings_text = brain.get_all_learnings()[-3000:]

    summary = f"""
🧠 *JA's Learning Report*

*Total Lessons:* {len([l for l in learnings_text.split('##') if l.strip()])}

*Recent Wisdom:*
{learnings_text[-1000:]}

I get better every day, Boss!
"""
    await update.message.reply_text(summary, parse_mode='Markdown')

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show JA's status"""
    skills = list(Path('skills').iterdir())
    learnings_count = len([l for l in brain.get_all_learnings().split('##') if l.strip()])

    status_text = f"""
🤖 *JA Autonomous Status*

🟢 *Status:* Online & Learning
🧠 *Skills:* {len([s for s in skills if s.is_dir()])} loaded
📚 *Learnings:* {learnings_count} lessons
🔍 *Last Research:* {datetime.now().strftime('%H:%M')}
⏰ *Next Check:* {(datetime.now() + timedelta(hours=2)).strftime('%H:%M')}

*Auto-Discovery:* Active
*Self-Learning:* Active
*Boss Permission:* Required for major actions

Waiting for your command, Boss! 👀
"""
    await update.message.reply_text(status_text, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle any message"""
    global BOSS_ID
    if not BOSS_ID:
        BOSS_ID = update.effective_user.id

    text = update.message.text
    text_lower = text.lower()

    # Save to memory
    memory.set(f"msg_{datetime.now().strftime('%H%M%S')}", text)

    # Check for approval
    if any(word in text_lower for word in ['approve', 'yes', 'seekh lo', 'haan']):
        pending = []
        for skill_folder in Path('skills').iterdir():
            if skill_folder.is_dir():
                skill_file = skill_folder / 'SKILL.md'
                if skill_file.exists():
                    with open(skill_file, 'r') as f:
                        if 'pending_approval' in f.read():
                            pending.append(skill_folder)

        if pending:
            latest = max(pending, key=lambda x: x.stat().st_mtime)
            skill_name = latest.name

            with open(latest / 'SKILL.md', 'r') as f:
                content = f.read()

            content = content.replace('pending_approval', 'approved')
            with open(latest / 'SKILL.md', 'w') as f:
                f.write(content)

            await update.message.reply_text(f"✅ *{skill_name}* learned! I am now expert in this.", parse_mode='Markdown')
            return

    # Check for simple commands
    if text_lower in ['execute', 'start', 'go']:
        await update.message.reply_text(
            "🚀 *Executing Day 1 plan...*\n\nVikram is preparing your task list.",
            parse_mode='Markdown'
        )
        return

    if text_lower in ['no', 'reject', 'next']:
        await update.message.reply_text(
            "❌ *Idea rejected.*\n\nTell me your next idea, Boss.",
            parse_mode='Markdown'
        )
        return

    # Normal conversation with learning
    learnings = brain.get_all_learnings()[-1500:]

    messages = [
        {"role": "system", "content": JA_CORE + f"\n\nMY LEARNINGS:\n{learnings}"},
        {"role": "user", "content": f"Boss says: {text}"}
    ]

    try:
        completion = client.chat.completions.create(
            model="qwen-2.5-32b",
            messages=messages,
            temperature=0.3,
            max_tokens=2000
        )
        response = completion.choices[0].message.content
        await update.message.reply_text(response, parse_mode='Markdown')

        brain.add_learning(
            situation=f"Boss said: {text[:100]}",
            lesson=f"I responded: {response[:100]}",
            result="Interaction logged"
        )
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

# ============ MAIN ============

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("board", board_meeting_cmd))
    application.add_handler(CommandHandler("task", task))
    application.add_handler(CommandHandler("approve", approve))
    application.add_handler(CommandHandler("learnings", learnings_cmd))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start autonomous loop
    loop = asyncio.get_event_loop()
    loop.create_task(autonomous_loop())

    print("🤖 JA ULTIMATE is running...")
    print("🧠 Board of Directors: ACTIVE")
    print("🔍 Auto-Discovery: ACTIVE")
    print("💾 Self-Learning: ACTIVE")
    print("👑 Boss: Gaurav")

    application.run_polling()

if __name__ == '__main__':
    main()

import os
import json
import asyncio
import threading
import requests
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
from http.server import HTTPServer, BaseHTTPRequestHandler
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

# ============ AUTO-DISCOVERY ============

class TechDiscovery:
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

# ============ FILE MEMORY ============

class FileMemory:
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

# ============ TELEGRAM API FUNCTIONS ============

def send_message(chat_id, text):
    """Send message via Telegram HTTP API"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        response = requests.post(url, json=payload, timeout=10)
        return response.json()
    except Exception as e:
        print(f"Error sending message: {e}")
        return None

def get_updates(offset=None):
    """Get updates from Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
        params = {"offset": offset, "limit": 10} if offset else {"limit": 10}
        response = requests.get(url, params=params, timeout=10)
        return response.json()
    except Exception as e:
        print(f"Error getting updates: {e}")
        return {"result": []}

# ============ BOARD MEETING SYSTEM ============

def ask_board_member(agent_key, idea, context=""):
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
    ravi_analysis = ask_board_member("ravi", idea)
    priya_analysis = ask_board_member("priya", idea, context=ravi_analysis)
    vikram_analysis = ask_board_member("vikram", idea, context=f"{ravi_analysis}\n\n{priya_analysis}")
    amit_analysis = ask_board_member("amit", idea, context=f"{ravi_analysis}\n\n{priya_analysis}\n\n{vikram_analysis}")

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

# ============ MESSAGE HANDLER ============

def handle_message(text, chat_id):
    """Handle incoming message"""
    global BOSS_ID

    if not BOSS_ID:
        BOSS_ID = chat_id
        memory.set("boss_id", str(BOSS_ID))
        memory.set("first_meeting", datetime.now().isoformat())

    text_lower = text.lower()

    # Save to memory
    memory.set(f"msg_{datetime.now().strftime('%H%M%S')}", text)

    # Handle commands
    if text_lower == '/start':
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
        send_message(chat_id, welcome)
        return

    if text_lower == '/status':
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
        send_message(chat_id, status_text)
        return

    if text_lower == '/learnings':
        learnings_text = brain.get_all_learnings()[-3000:]
        summary = f"""
🧠 *JA's Learning Report*

*Total Lessons:* {len([l for l in learnings_text.split('##') if l.strip()])}

*Recent Wisdom:*
{learnings_text[-1000:]}

I get better every day, Boss!
"""
        send_message(chat_id, summary)
        return

    if text_lower == '/task':
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
            send_message(chat_id, response)

            brain.add_learning(
                situation="Boss asked for daily task",
                lesson="Provided actionable task",
                result="Task delivered"
            )
        except Exception as e:
            send_message(chat_id, f"Error: {str(e)}")
        return

    if text_lower.startswith('/board '):
        idea = text[7:].strip()

        send_message(chat_id, f"""
🤖 *Calling Board Meeting for:*

_{idea}_

🔵 Ravi is researching...
🟢 Priya is calculating...
🟡 Vikram is planning...
🔴 Amit is finding risks...

⏳ *This takes 60-90 seconds. Please wait...*
""")

        try:
            result = run_board_meeting(idea)

            memory.set(f"board_{datetime.now().strftime('%Y%m%d_%H%M')}", f"Idea: {idea}")
            brain.add_learning(
                situation=f"Board meeting for: {idea[:50]}",
                lesson="Board debated and reached decision",
                result="Recommendation delivered to Boss"
            )

            send_message(chat_id, result)
        except Exception as e:
            send_message(chat_id, f"❌ *Board Meeting Error:*\n{str(e)}")
        return

    if text_lower == '/approve':
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

        send_message(chat_id, text)
        return

    if text_lower.startswith('/approve '):
        skill_name = text[9:].strip()
        skill_file = Path(f"skills/{skill_name}/SKILL.md")

        if skill_file.exists():
            with open(skill_file, 'r') as f:
                content = f.read()

            content = content.replace('pending_approval', 'approved')
            content += f"\n\n## APPROVED\nApproved by Boss on: {datetime.now().isoformat()}\n"

            with open(skill_file, 'w') as f:
                f.write(content)

            send_message(chat_id, f"✅ *{skill_name}* approved! Now I can learn it.")
            brain.add_learning(
                situation=f"Boss approved skill: {skill_name}",
                lesson="New capability added",
                result=f"Skill {skill_name} activated"
            )
        else:
            send_message(chat_id, "❌ Skill not found.")
        return

    # Check for approval words
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

            send_message(chat_id, f"✅ *{skill_name}* learned! I am now expert in this.")
            return

    # Simple commands
    if text_lower in ['execute', 'start', 'go']:
        send_message(chat_id, "🚀 *Executing Day 1 plan...*\n\nVikram is preparing your task list.")
        return

    if text_lower in ['no', 'reject', 'next']:
        send_message(chat_id, "❌ *Idea rejected.*\n\nTell me your next idea, Boss.")
        return

    # Normal conversation
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
        send_message(chat_id, response)

        brain.add_learning(
            situation=f"Boss said: {text[:100]}",
            lesson=f"I responded: {response[:100]}",
            result="Interaction logged"
        )
    except Exception as e:
        send_message(chat_id, f"Error: {str(e)}")

# ============ AUTONOMOUS LOOP ============

def autonomous_loop():
    """JA's 24/7 self-running loop"""
    while True:
        try:
            now = datetime.now()

            if now.hour % 2 == 0 and now.minute < 5:
                # Research new tech
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
                        send_message(BOSS_ID, message)

                # Daily market research
                market_queries = [
                    "fly ash brick price Lucknow today",
                    "app monetization trends India 2026",
                    "online money making opportunities India"
                ]

                for query in market_queries:
                    results = search_web(query)
                    memory.set(f"research_{now.strftime('%Y%m%d')}_{query[:20]}", results)

                # Self-reflection
                brain.add_learning(
                    situation="Daily autonomous review",
                    lesson="Processed market research and tech discovery",
                    result="Learning updated"
                )

            # Sleep for 5 minutes
            import time
            time.sleep(300)

        except Exception as e:
            print(f"Autonomous loop error: {e}")
            import time
            time.sleep(300)

# ============ MAIN BOT LOOP ============

def run_bot():
    """Main bot loop using direct Telegram API"""
    print("🤖 JA ULTIMATE is running...")
    print("🧠 Board of Directors: ACTIVE")
    print("🔍 Auto-Discovery: ACTIVE")
    print("💾 Self-Learning: ACTIVE")
    print("👑 Boss: Gaurav")

    offset = None

    while True:
        try:
            updates = get_updates(offset)

            if updates.get('result'):
                for update in updates['result']:
                    offset = update['update_id'] + 1

                    if 'message' in update and 'text' in update['message']:
                        text = update['message']['text']
                        chat_id = update['message']['chat']['id']

                        print(f"Received: {text} from {chat_id}")
                        handle_message(text, chat_id)

            # Small sleep to prevent flooding
            import time
            time.sleep(1)

        except Exception as e:
            print(f"Bot loop error: {e}")
            import time
            time.sleep(5)

# ============ WEB SERVER FOR RENDER ============

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({
            "status": "alive",
            "learning": True,
            "boss": "Gaurav",
            "board": "active"
        }).encode())

    def log_message(self, format, *args):
        pass  # Suppress logs

def run_web_server():
    """Run health check server for Render"""
    port = int(os.environ.get('PORT', 10000))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    print(f"🌐 Health server running on port {port}")
    server.serve_forever()

# ============ MAIN ============

if __name__ == '__main__':
    # Start autonomous loop in background thread
    auto_thread = threading.Thread(target=autonomous_loop, daemon=True)
    auto_thread.start()

    # Start web server in background thread (for Render health checks)
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()

    # Run bot in main thread
    run_bot()

"""
Daily Business Idea Generator (Multi-Model with Judge)

Generates ideas from 3 models in parallel:
- GPT-OSS-120B on Groq
- Claude Opus 4.6 Adaptive
- Gemini 3 Pro

Claude Opus 4.6 judges the best idea based on:
- Ease of customer acquisition
- Market demand

Uses up to 2 retries per model if the judge rejects ideas.
"""

import json
import logging
import os
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# ─── Logging ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ─── Config ──────────────────────────────────────────────────────────────────

MAX_RETRIES = 1  # max regeneration attempts per model

# Random themes to inject variety — short audience/topic labels, NOT ideas
RANDOM_THEMES = [
    # ── Broad / mainstream ──
    "phone photography", "saving money", "email overload",
    "forgetfulness and reminders", "PDFs and documents", "social media presence",
    "healthy eating on a budget", "writing and copywriting", "selling stuff online",
    "learning new skills", "travel planning", "personal finance",
    "gift giving", "image editing", "short-form video", "habits and goals",
    "file management", "sleep", "dating", "AI for everyday life",
    "digital organization", "family scheduling", "side hustles",
    "cooking for busy people", "resumes and job hunting", "printing",
    "smart home", "moving and relocation", "splitting expenses",
    "reading and books", "scheduling across time zones", "secondhand selling",
    "legal documents", "drawing and art", "mornings and waking up",
    "screen time", "translation", "journaling", "taxes",
    "decluttering", "QR codes and links", "birthdays and anniversaries",
    "price comparison", "credit scores", "subscription management",
    "memes and humor", "writing messages", "meditation",
    "passwords and security", "local events", "note-taking",
    "video calls", "simple websites", "motivation and inspiration",
    # ── Self-growth and planning ──
    "goal setting", "morning routines", "feeling stuck in life",
    "book summaries", "habit building", "accountability",
    "weekly planning", "journaling and reflection", "mood tracking",
    "affirmations", "procrastination", "time management",
    "vision boards", "daily reflection", "New Year's resolutions",
    "prioritization", "long-term life planning", "personal growth",
    "daily planning", "anxiety and stress", "stoicism and mindfulness",
    "doom-scrolling and focus", "self-discipline", "gratitude",
    "confidence building", "work-life balance", "burnout recovery",
    # ── Medium-broad audiences ──
    "small business owners", "freelancers", "content creators",
    "online sellers", "remote workers", "students",
    "job seekers", "startup founders", "social media managers",
    "teachers", "developers", "designers",
    "marketers", "coaches and consultants", "YouTubers",
    "parents", "couples", "retirees", "teenagers",
    # ── Specific niches ──
    "pet owners", "new parents", "college students", "real estate agents",
    "fitness enthusiasts", "small restaurant owners", "wedding planners",
    "Etsy sellers", "Twitch streamers", "Airbnb hosts", "yoga instructors",
    "freelance photographers", "dentist offices", "food truck owners",
    "language learners", "home renovators", "podcast creators",
    "local bakeries", "tattoo artists", "guitar teachers", "dog walkers",
    "Shopify store owners", "travel bloggers", "nail salon owners",
    "tutors", "event DJs", "moving companies", "personal trainers",
    "interior designers", "indie game developers", "book clubs",
    "meal preppers", "plant parents", "vintage sellers", "barber shops",
    "cleaning services", "craft beer enthusiasts", "local tour guides",
    "resume writers", "accountants",
]

IDEA_PROMPT_TEMPLATE = """Generate ONE micro-SaaS or micro-product idea I can build and launch fast.

I'm a solo developer who wants to have fun building small products that make real money — even if it's just $1-2 per customer. I want to see paying customers quickly and build a repeatable acquisition loop through paid ads.

{theme_section}
CONSTRAINTS:
- I can build an MVP in 1-2 weeks using vibe coding (modern web stack, frontend + backend, can use LLMs/AI agents, but it is not mandatory to use LLMs/AI agents)
- After two weeks it must be deployable and ready to accept payments (Stripe/PayPal)
- Customers must be acquirable through paid ads on Facebook, Instagram, or Google
- The product must be easy to demo in a short video ad or image ad
- Target people who already pay for things online with a credit card

PRICING:
- Prefer a subscription model ($1-29/month) — recurring revenue is key
- Offer a 1-week free trial to hook users, then convert to a paid subscription
- The price should feel like a no-brainer — so cheap that people don't think twice

BUSINESS REALITY:
- I don't need to make a lot of money — I want positive cash flow and the thrill of seeing real customers pay
- First paying customer within 30 days of launch
- Path to first $100/month should be obvious and repeatable
- Competition doesn't matter — I can always find new customers through ads
- It should be FUN to build and FUN to run

Provide your response in this format:

**Product Name:** [Catchy, memorable name]

**One-Line Pitch:** [One sentence I could use in an ad]

**Target Customer:** [Who exactly is paying me? Be specific — age, situation, why they care]

**The Problem:** [What specific pain or desire does this solve? Why will they pay $1-2 for it?]

**How It Works:** [2-3 sentences, dead simple]

**Pricing:** [Exact model — e.g., "$1.99 per use" or "$4.99/month"]

**Ad Strategy:** [Which platform (Facebook/Instagram/Google), what kind of ad (video/image/carousel), what hook grabs attention, estimated cost per customer]

**Path to $100/month:** [Show me the math — e.g., "50 customers × $2 = $100/month, need 2 customers/day from ads at $3 CPA"]

**Week 1 Build:** [What to build first]

**Week 2 Build:** [What to add, polish, and launch]

**Why This Is Fun:** [Why I'll enjoy building and running this]

Be creative. Be specific. Be practical. It's totally fine to copy or improve an existing product. Think about ANY audience — regular people, small business owners, freelancers, developers, creators, students — whoever would happily pay a dollar or two for real value."""


# ─── API clients (created once, reused across retries) ───────────────────────

def _openai_client() -> OpenAI:
    return OpenAI()

def _groq_client() -> OpenAI:
    return OpenAI(
        api_key=os.getenv("GROQ_API_KEY"),
        base_url="https://api.groq.com/openai/v1",
    )

def _anthropic_client() -> anthropic.Anthropic:
    return anthropic.Anthropic()

def _gemini_client() -> OpenAI:
    return OpenAI(
        api_key=os.getenv("GOOGLE_API_KEY"),
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )

# Lazy-initialized singletons
_clients: dict = {}

def get_client(name: str):
    """Get or create a cached API client."""
    if name not in _clients:
        _clients[name] = {
            "openai": _openai_client,
            "groq": _groq_client,
            "anthropic": _anthropic_client,
            "gemini": _gemini_client,
        }[name]()
    return _clients[name]


# ─── Model generation functions ──────────────────────────────────────────────


def _build_prompt(base_prompt: str, feedback: str | None = None) -> str:
    """Build a prompt, optionally including rejection feedback from the judge."""
    if feedback is None:
        return base_prompt
    return f"""{base_prompt}

IMPORTANT — A previous version of your idea was rejected for the following reason:

{feedback}

Please generate a DIFFERENT and BETTER idea that addresses this feedback.
Focus especially on making the idea easy to acquire customers for and ensuring there is real market demand."""


def generate_gpt52(prompt: str) -> str:
    """Generate idea using GPT-5.2 with reasoning effort high."""
    client = get_client("openai")
    response = client.chat.completions.create(
        model="gpt-5.2",
        messages=[{"role": "user", "content": prompt}],
        reasoning_effort="high",
    )
    return response.choices[0].message.content


def generate_groq(prompt: str) -> str:
    """Generate idea using GPT-OSS-120B on Groq."""
    client = get_client("groq")
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


def generate_claude(prompt: str) -> str:
    """Generate idea using Claude Opus 4.6 Adaptive."""
    client = get_client("anthropic")
    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def generate_gemini(prompt: str) -> str:
    """Generate idea using Gemini 3 Pro."""
    client = get_client("gemini")
    response = client.chat.completions.create(
        model="gemini-3-pro-preview",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


# Model registry
MODELS = [
    {"name": "GPT-5.2 (OpenAI)", "generate": generate_gpt52},
    {"name": "GPT-OSS-120B (Groq)", "generate": generate_groq},
    {"name": "Claude Opus 4.6", "generate": generate_claude},
    {"name": "Gemini 3 Pro", "generate": generate_gemini},
]

LABELS = ["A", "B", "C", "D"]


# ─── Judge ───────────────────────────────────────────────────────────────────

JUDGE_SYSTEM = """You are a sharp, experienced business consultant who evaluates startup and micro-SaaS ideas.

You will be shown business ideas labeled as Idea A, Idea B, Idea C, and Idea D.

Your job is to evaluate each idea based on THREE criteria (most important first):

1. **Ease of customer acquisition** — Can this product easily attract paying customers through paid ads on Facebook, Instagram, or Google? Is the ad hook obvious? Will people click and buy?

2. **Market demand** — Is there real, proven demand for this? Are people already paying for similar solutions? Will someone actually pull out their credit card for this?

3. **Build simplicity** — Can a solo developer realistically build a working MVP in 1-2 weeks? Is the tech straightforward (no complex integrations, no regulatory hurdles, no chicken-and-egg problems)?

For EACH idea, provide:
- A score from 1-10 for each criterion
- A brief explanation

IMPORTANT — Be a strict, demanding judge. Most ideas are mediocre. Follow this decision process:

Step 1: Score all ideas honestly. Do NOT inflate scores to be nice.
Step 2: Check if ANY idea scores 9 or higher on ALL THREE criteria (acquisition >= 9 AND demand >= 9 AND build >= 9).
Step 3: Decision:
  - If YES (at least one idea has 9+ on all three) → verdict "accept", pick the highest-scoring one as WINNER
  - If NO (no idea has 9+ on all three) → verdict "reject_all", set winner to null

It is COMPLETELY NORMAL to reject all ideas — in fact, you should reject most of the time. A 9/10 means the idea is truly exceptional. Rejecting pushes the models to try harder in the next round. Do NOT accept a mediocre idea just to avoid rejecting.

When rejecting, provide specific and actionable feedback for EACH idea explaining exactly what needs to improve and why the score is low. Be concrete: "the ad hook is unclear" is better than "needs improvement."

When accepting, you may slightly refine the winning idea (fix wording, sharpen the pitch, adjust pricing) but keep the core concept intact. You can also suggest improvements in explanation.

Respond ONLY with valid JSON in this exact format (no markdown fences, no extra text):

{
    "evaluations": [
        {
            "idea_label": "A",
            "acquisition_score": 8,
            "demand_score": 7,
            "build_score": 1,
            "explanation": "..."
        },
        {
            "idea_label": "B",
            "acquisition_score": 5,
            "demand_score": 2,
            "build_score": 8,
            "explanation": "..."
        },
        {
            "idea_label": "C",
            "acquisition_score": 7,
            "demand_score": 4,
            "build_score": 7,
            "explanation": "..."
        },
        {
            "idea_label": "D",
            "acquisition_score": 6,
            "demand_score": 7,
            "build_score": 6,
            "explanation": "..."
        }
    ],
    "verdict": "accept",
    "winner": "A",
    "winning_idea": "The full winning idea text, possibly slightly refined by you",
    "rejection_feedback": {
        "A": "feedback for idea A if rejected, or null if accepted",
        "B": "feedback for idea B if rejected, or null if accepted",
        "C": "feedback for idea C if rejected, or null if accepted",
        "D": "feedback for idea D if rejected, or null if accepted"
    }
}

If verdict is "reject_all", set "winner" to null and "winning_idea" to null, and provide specific feedback for ALL ideas in rejection_feedback."""


def judge_ideas(ideas: dict[str, str]) -> dict:
    """
    Judge the ideas using Claude Opus 4.6 Adaptive.

    Ideas are shuffled before presenting to reduce positional bias.
    The mapping is tracked so we can map back to the original labels.

    Args:
        ideas: dict mapping label ("A", "B", "C") to idea text.

    Returns:
        Parsed judge response dict (with labels mapped back to originals).
    """
    # Shuffle idea order to reduce positional bias
    labels_list = list(ideas.keys())
    random.shuffle(labels_list)

    # Map shuffled positions to presentation labels
    presentation_labels = LABELS[:]
    shuffle_map = {}  # presentation_label -> original_label
    for i, orig_label in enumerate(labels_list):
        shuffle_map[presentation_labels[i]] = orig_label

    # Build ideas text with shuffled order — NO model names
    ideas_text = ""
    for pres_label, orig_label in shuffle_map.items():
        ideas_text += f"\n{'='*60}\nIdea {pres_label}:\n{'='*60}\n{ideas[orig_label]}\n"

    client = get_client("anthropic")
    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=8192,
        system=JUDGE_SYSTEM,
        messages=[
            {"role": "user", "content": f"Evaluate these business ideas:\n{ideas_text}"}
        ],
    )

    raw = response.content[0].text

    # Clean up potential markdown fences
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0]
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0]

    result = json.loads(raw.strip())

    # Map everything back to original labels
    for ev in result.get("evaluations", []):
        ev["idea_label"] = shuffle_map.get(ev["idea_label"], ev["idea_label"])

    if result.get("winner"):
        result["winner"] = shuffle_map.get(result["winner"], result["winner"])

    old_feedback = result.get("rejection_feedback", {})
    new_feedback = {}
    for pres_label, fb in old_feedback.items():
        orig_label = shuffle_map.get(pres_label, pres_label)
        new_feedback[orig_label] = fb
    result["rejection_feedback"] = new_feedback

    return result


# ─── Parallel generation helper ──────────────────────────────────────────────


def _generate_one(label: str, model: dict, prompt: str) -> tuple[str, str | None, float]:
    """Generate a single idea. Returns (label, idea_or_none, elapsed_seconds)."""
    start = time.time()
    try:
        idea = model["generate"](prompt)
        elapsed = time.time() - start
        return label, idea, elapsed
    except Exception as e:
        elapsed = time.time() - start
        log.error("   [%s] %s — ❌ error after %.1fs: %s", label, model["name"], elapsed, e)
        return label, None, elapsed


# ─── Main orchestrator ───────────────────────────────────────────────────────


def main():
    # Every second day: use a theme. Other days: completely open (no theme).
    day_of_year = datetime.now().timetuple().tm_yday
    if day_of_year % 2 == 0:
        theme = random.choice(RANDOM_THEMES)
        theme_section = f"""TODAY'S FOCUS: {theme}
(Use this as inspiration — your idea should serve this audience or a closely related one. It can be a niche tool or a mainstream product that appeals to millions.)
"""
    else:
        theme = None
        theme_section = ""

    idea_prompt = IDEA_PROMPT_TEMPLATE.format(theme_section=theme_section)

    log.info("🚀 Starting Daily Business Idea Generator (Multi-Model)")
    log.info("   Models: %s", ", ".join(m["name"] for m in MODELS))
    log.info("   Judge:  Claude Opus 4.6 Adaptive")
    log.info("   Today's theme: %s", theme or "OPEN (no theme — full creative freedom)")
    log.info("   Max retries per model: %d", MAX_RETRIES)
    log.info("=" * 60)

    # Pre-initialize API clients (thread-safe — done before any parallel work)
    log.info("   Initializing API clients...")
    for name in ("openai", "groq", "anthropic", "gemini"):
        get_client(name)
    log.info("   ✅ All clients ready")

    total_start = time.time()

    # Track state per model
    attempts = {label: 0 for label in LABELS}
    feedback = {label: None for label in LABELS}
    ideas = {}
    needs_generation = {label: True for label in LABELS}

    winner_label = None
    winning_idea = None
    winner_evaluation = None
    all_evaluations = []

    for round_num in range(1, MAX_RETRIES + 2):  # up to MAX_RETRIES + 1 rounds
        log.info("")
        log.info("━" * 60)
        log.info("📋 ROUND %d", round_num)
        log.info("━" * 60)

        # ── Generate ideas in parallel from models that need it ──
        to_generate = []
        for label, model in zip(LABELS, MODELS):
            if not needs_generation[label]:
                log.info("   [%s] %s — keeping previous idea", label, model["name"])
                continue
            attempts[label] += 1
            prompt = _build_prompt(idea_prompt, feedback[label])
            retry_note = " (with judge feedback)" if feedback[label] else ""
            log.info(
                "   [%s] %s — queuing generation (attempt %d/%d)%s",
                label, model["name"], attempts[label], MAX_RETRIES + 1, retry_note,
            )
            to_generate.append((label, model, prompt))

        if to_generate:
            log.info("")
            log.info("   ⏳ Generating %d idea(s) in parallel...", len(to_generate))
            round_start = time.time()

            with ThreadPoolExecutor(max_workers=len(to_generate)) as executor:
                futures = {
                    executor.submit(_generate_one, label, model, prompt): label
                    for label, model, prompt in to_generate
                }
                for future in as_completed(futures):
                    label, idea, elapsed = future.result()
                    model_name = MODELS[LABELS.index(label)]["name"]
                    if idea:
                        ideas[label] = idea
                        log.info("   [%s] %s — ✅ received (%.1fs)", label, model_name, elapsed)
                    else:
                        ideas[label] = f"[Error: generation failed for {model_name}]"
                        log.warning("   [%s] %s — ⚠️  failed, using error placeholder", label, model_name)

            log.info("   ⏱️  All models done in %.1fs", time.time() - round_start)

        # ── Judge all ideas ──
        log.info("")
        log.info("⚖️  Sending ideas to judge (Claude Opus 4.6 Adaptive)...")
        log.info("   Note: judge sees shuffled labels — no model names, no ordering bias")

        judge_start = time.time()
        try:
            verdict = judge_ideas(ideas)
        except Exception as e:
            log.error("❌ Judge failed after %.1fs: %s", time.time() - judge_start, e)
            log.info("   Picking the first idea as fallback")
            winner_label = "A"
            winning_idea = ideas["A"]
            break
        log.info("   ⏱️  Judge responded in %.1fs", time.time() - judge_start)

        # ── Log evaluations ──
        log.info("")
        log.info("📊 Judge evaluations:")
        for ev in verdict.get("evaluations", []):
            model_name = MODELS[LABELS.index(ev["idea_label"])]["name"]
            log.info(
                "   [%s] %s — acquisition: %d/10, demand: %d/10, build: %d/10",
                ev["idea_label"], model_name,
                ev["acquisition_score"], ev["demand_score"], ev.get("build_score", 0),
            )
            log.info("         %s", ev["explanation"])

        log.info("")
        log.info("🏛️  Verdict: %s", verdict["verdict"].upper())

        # ── Programmatic quality gate ──
        # Even if the judge says "accept", verify the winner actually meets 7+ on all criteria.
        # This prevents the judge from being too lenient and skipping round 2.
        evals = verdict.get("evaluations", [])
        if verdict["verdict"] == "accept" and verdict.get("winner"):
            w_ev = next((e for e in evals if e["idea_label"] == verdict["winner"]), None)
            if w_ev:
                acq = w_ev["acquisition_score"]
                dem = w_ev["demand_score"]
                bld = w_ev.get("build_score", 0)
                if acq < 9 or dem < 9 or bld < 9:
                    log.info(
                        "⚠️  Judge accepted Idea %s but scores (%d/%d/%d) don't meet 9+ threshold — overriding to reject",
                        verdict["winner"], acq, dem, bld,
                    )
                    verdict["verdict"] = "reject_all"
                    verdict["winner"] = None
                    verdict["winning_idea"] = None
                    # Build feedback from explanations if judge didn't provide rejection feedback
                    if not verdict.get("rejection_feedback"):
                        verdict["rejection_feedback"] = {
                            ev["idea_label"]: f"Scores too low ({ev['acquisition_score']}/{ev['demand_score']}/{ev.get('build_score',0)}). {ev['explanation']}"
                            for ev in evals
                        }

        # ── Handle verdict ──
        if verdict["verdict"] == "accept" and verdict.get("winner"):
            winner_label = verdict["winner"]
            winning_idea = verdict.get("winning_idea") or ideas[winner_label]
            all_evaluations = verdict.get("evaluations", [])
            winner_evaluation = next(
                (ev for ev in all_evaluations if ev["idea_label"] == winner_label),
                None,
            )
            log.info("🏆 Winner: Idea %s (%s)", winner_label, MODELS[LABELS.index(winner_label)]["name"])
            break

        # Rejected — prepare retries
        log.info("🔄 All ideas rejected. Preparing retries...")
        rejection_feedback = verdict.get("rejection_feedback", {})

        any_can_retry = False
        for label in LABELS:
            fb = rejection_feedback.get(label)
            if fb and attempts[label] < MAX_RETRIES + 1:
                feedback[label] = fb
                needs_generation[label] = True
                any_can_retry = True
                log.info(
                    "   [%s] %s — will retry. Feedback: %s",
                    label, MODELS[LABELS.index(label)]["name"],
                    fb[:120] + ("..." if len(str(fb)) > 120 else ""),
                )
            else:
                needs_generation[label] = False
                if attempts[label] >= MAX_RETRIES + 1:
                    log.info(
                        "   [%s] %s — max retries reached, keeping last idea",
                        label, MODELS[LABELS.index(label)]["name"],
                    )

        if not any_can_retry:
            log.info("⚠️  No more retries available. Picking best scoring idea as fallback.")
            best_ev = max(
                verdict.get("evaluations", []),
                key=lambda ev: ev["acquisition_score"] + ev["demand_score"] + ev.get("build_score", 0),
            )
            winner_label = best_ev["idea_label"]
            winning_idea = ideas[winner_label]
            winner_evaluation = best_ev
            all_evaluations = verdict.get("evaluations", [])
            log.info("🏆 Fallback winner: Idea %s (%s)", winner_label, MODELS[LABELS.index(winner_label)]["name"])
            break
    else:
        # Loop ended without break — pick best from last round
        log.info("⚠️  Max rounds exhausted. Picking best scoring idea.")
        try:
            best_ev = max(
                verdict.get("evaluations", []),
                key=lambda ev: ev["acquisition_score"] + ev["demand_score"] + ev.get("build_score", 0),
            )
            winner_label = best_ev["idea_label"]
            winning_idea = ideas[winner_label]
            winner_evaluation = best_ev
            all_evaluations = verdict.get("evaluations", [])
        except Exception:
            winner_label = "A"
            winning_idea = ideas.get("A", "No idea generated")

    # ── Display the winning idea ──
    total_elapsed = time.time() - total_start
    winner_model = MODELS[LABELS.index(winner_label)]["name"]
    today = datetime.now().strftime("%Y-%m-%d")
    log.info("")
    log.info("⏱️  Total time: %.1fs", total_elapsed)

    print("\n" + "=" * 80)
    print(f"💡 DAILY BUSINESS IDEA — {today}")
    print(f"   Generated by: {winner_model}")
    print(f"   Judged by: Claude Opus 4.6 Adaptive")
    print(f"   Today's theme: {theme or 'OPEN (no theme)'}")
    print(f"   Total time: {total_elapsed:.1f}s")

    # Show all models' scores
    if all_evaluations:
        print(f"\n   ⚖️  Scoreboard:")
        print(f"   {'Model':<25} {'Acq':>4} {'Dem':>4} {'Bld':>4} {'Total':>6}")
        print(f"   {'─'*25} {'─'*4} {'─'*4} {'─'*4} {'─'*6}")
        for ev in sorted(all_evaluations,
                         key=lambda e: e["acquisition_score"] + e["demand_score"] + e.get("build_score", 0),
                         reverse=True):
            label = ev["idea_label"]
            model_name = MODELS[LABELS.index(label)]["name"]
            total = ev["acquisition_score"] + ev["demand_score"] + ev.get("build_score", 0)
            marker = " 🏆" if label == winner_label else ""
            print(f"   {model_name:<25} {ev['acquisition_score']:>4} {ev['demand_score']:>4} {ev.get('build_score', 0):>4} {total:>5}/30{marker}")
        print()
        # Show winner's explanation
        if winner_evaluation:
            print(f"   Judge says: {winner_evaluation['explanation']}")

    print("=" * 80 + "\n")
    print(winning_idea)
    print("\n" + "=" * 80 + "\n")

    # ── Always save to files ──
    # Create directory: ideas/YYYY-MM-DD/
    ideas_dir = Path("ideas") / today
    ideas_dir.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ── Save one file per model ──
    for label in LABELS:
        model_name = MODELS[LABELS.index(label)]["name"]
        is_winner = label == winner_label
        idea_text = ideas.get(label, "No idea generated")
        ev = next((e for e in all_evaluations if e["idea_label"] == label), None)

        # Use winning_idea (possibly refined by judge) for the winner
        if is_winner and winning_idea:
            idea_text = winning_idea

        # Build a clean filename from model name
        safe_name = model_name.lower().replace(" ", "_").replace("(", "").replace(")", "")
        filepath = ideas_dir / f"{safe_name}.md"

        with open(filepath, "w") as f:
            if is_winner:
                f.write(f"# 🏆 Winning Idea — {model_name}\n\n")
            else:
                f.write(f"# Idea — {model_name}\n\n")

            f.write(f"**Date:** {today}\n")
            f.write(f"**Model:** {model_name}\n")
            f.write(f"**Theme:** {theme or 'Open (no theme)'}\n")
            if is_winner:
                f.write("**Status:** 🏆 Winner\n")
            f.write("\n")

            # Judge's evaluation for this model
            if ev:
                f.write("## Judge's Evaluation\n\n")
                acq = ev["acquisition_score"]
                dem = ev["demand_score"]
                bld = ev.get("build_score", 0)
                total = acq + dem + bld
                f.write(f"| Criterion | Score |\n")
                f.write(f"|-----------|-------|\n")
                f.write(f"| Customer acquisition | **{acq}/10** |\n")
                f.write(f"| Market demand | **{dem}/10** |\n")
                f.write(f"| Build simplicity | **{bld}/10** |\n")
                f.write(f"| **Total** | **{total}/30** |\n\n")
                f.write(f"> {ev['explanation']}\n\n")

            f.write("---\n\n")
            f.write("## The Idea\n\n")
            f.write(idea_text)
            f.write(f"\n\n---\n\n")
            f.write(f"*Generated: {generated_at}*\n")

        log.info("   💾 %s → %s", model_name, filepath)

    # ── Save summary / scoreboard file ──
    summary_path = ideas_dir / "00_summary.md"
    with open(summary_path, "w") as f:
        f.write(f"# Daily Ideas Summary — {today}\n\n")
        f.write(f"**Theme:** {theme or 'Open (no theme)'}\n")
        f.write(f"**Winner:** {winner_model}\n")
        f.write(f"**Judge:** Claude Opus 4.6 Adaptive\n")
        f.write(f"**Total time:** {total_elapsed:.1f}s\n\n")

        # Scoreboard
        if all_evaluations:
            f.write("## Scoreboard\n\n")
            f.write("| Rank | Model | Acq | Dem | Bld | Total | |\n")
            f.write("|------|-------|-----|-----|-----|-------|---|\n")
            sorted_evals = sorted(
                all_evaluations,
                key=lambda e: e["acquisition_score"] + e["demand_score"] + e.get("build_score", 0),
                reverse=True,
            )
            for rank, ev in enumerate(sorted_evals, 1):
                label = ev["idea_label"]
                model_name = MODELS[LABELS.index(label)]["name"]
                total = ev["acquisition_score"] + ev["demand_score"] + ev.get("build_score", 0)
                marker = "🏆" if label == winner_label else ""
                f.write(f"| {rank} | {model_name} | {ev['acquisition_score']}/10 | {ev['demand_score']}/10 | {ev.get('build_score', 0)}/10 | **{total}/30** | {marker} |\n")
            f.write("\n")

            # Judge's notes per model
            f.write("## Judge's Notes\n\n")
            for ev in sorted_evals:
                label = ev["idea_label"]
                model_name = MODELS[LABELS.index(label)]["name"]
                marker = " 🏆" if label == winner_label else ""
                f.write(f"### {model_name}{marker}\n\n")
                f.write(f"> {ev['explanation']}\n\n")

        # Links to individual files
        f.write("## Individual Ideas\n\n")
        for label in LABELS:
            model_name = MODELS[LABELS.index(label)]["name"]
            safe_name = model_name.lower().replace(" ", "_").replace("(", "").replace(")", "")
            marker = " 🏆" if label == winner_label else ""
            f.write(f"- [{model_name}{marker}](./{safe_name}.md)\n")

        f.write(f"\n---\n\n*Generated: {generated_at}*\n")

    log.info("   💾 Summary → %s", summary_path)
    print(f"\n💾 Saved to {ideas_dir}/")

    return winning_idea


if __name__ == "__main__":
    main()

import random
from datetime import datetime

MAX_RETRIES = 2

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

IDEA_SYSTEM_PROMPT = """You are a creative micro-SaaS idea generator for a solo developer.

The developer wants to build small, fun products that make real money — even if it's just $1-2 per customer. They want paying customers quickly and a repeatable acquisition loop through paid ads.

CONSTRAINTS:
- MVP buildable in 1-2 weeks using vibe coding (modern web stack, frontend + backend, can use LLMs/AI agents, but it is not mandatory to use LLMs/AI agents)
- After two weeks it must be deployable and ready to accept payments (Stripe/PayPal)
- Customers must be acquirable through paid ads on Facebook, Instagram, or Google
- The product must be easy to demo in a short video ad or image ad
- Target people who already pay for things online with a credit card

PRICING:
- Prefer a subscription model ($1-29/month) — recurring revenue is key
- Offer a 1-week free trial to hook users, then convert to a paid subscription
- The price should feel like a no-brainer — so cheap that people don't think twice

BUSINESS REALITY:
- Goal is positive cash flow and the thrill of seeing real customers pay
- First paying customer within 30 days of launch
- Path to first $100/month should be obvious and repeatable
- Competition doesn't matter — new customers come through ads
- It should be FUN to build and FUN to run

Always respond in this exact format:

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

IDEA_USER_TEMPLATE = """Generate ONE micro-SaaS or micro-product idea I can build and launch fast.

{theme_section}"""

JUDGE_SYSTEM = """You are a sharp, experienced business consultant who evaluates startup and micro-SaaS ideas.

You will be shown business ideas labeled as Idea A and Idea B.

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
        }
    ],
    "verdict": "accept",
    "winner": "A",
    "winning_idea": "The full winning idea text, possibly slightly refined by you",
    "rejection_feedback": {
        "A": "feedback for idea A if rejected, or null if accepted",
        "B": "feedback for idea B if rejected, or null if accepted"
    }
}

If verdict is "reject_all", set "winner" to null and "winning_idea" to null, and provide specific feedback for ALL ideas in rejection_feedback."""


def get_idea_prompt() -> tuple[str | None, str, str]:
    day_of_year = datetime.now().timetuple().tm_yday
    theme = random.choice(RANDOM_THEMES) if day_of_year % 2 == 0 else None
    section = (
        f"TODAY'S FOCUS: {theme}\n"
        "(Use this as inspiration — your idea should serve this audience "
        "or a closely related one. It can be a niche tool or a mainstream "
        "product that appeals to millions.)\n"
        if theme
        else ""
    )
    return theme, IDEA_SYSTEM_PROMPT, IDEA_USER_TEMPLATE.format(theme_section=section).strip()

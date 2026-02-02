"""
Business Idea Refiner - Iteratively refine ideas through multiple LLM iterations.

This module demonstrates how to use multiple LLM calls to progressively
refine and improve a business idea concept.
"""

from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()


def main():
    # Initialize OpenAI client (will use OPENAI_API_KEY from .env automatically)
    client = OpenAI()
    
    # First iteration: Select industry
    messages = [{"role": "user", "content": """You are a business consultant specializing in AI opportunities.

    Select ONE specific industry that meets ALL these criteria:
    1. Has clear, measurable operational inefficiencies
    2. A solo entrepreneur or small team can make significant impact
    3. Low barrier to entry - can acquire first clients relatively easily
    4. Repetitive tasks that could benefit from automation
    5. Currently relies heavily on human decision-making or manual processes

    Provide your response in this format:
    **Industry:** [Name]
    **Why it's suitable:** [2-3 sentences explaining why it meets the criteria]
    **Market size:** [Brief description of potential client base]

    Choose an industry that is NOT overly saturated with AI solutions already."""}]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )

    industry = response.choices[0].message.content

    print("Industry:")
    print(industry)
    print("\n" + "="*80 + "\n")

    # Second iteration: Identify pain point
    messages = [{"role": "user", "content": f"""Based on this industry selection:

    {industry}

    Now identify ONE specific pain-point that meets these criteria:
    1. Causes significant time loss or operational cost
    2. Involves repetitive decision-making or information gathering
    3. Currently solved inefficiently by humans
    4. Has measurable impact on business outcomes
    5. Would benefit from 24/7 autonomous operation

    Provide your response in this format:
    **Pain-point:** [Clear, concise description]
    **Current solution:** [How it's handled today]
    **Impact:** [Time/cost/quality impact on the business]
    **Why Agentic AI fits:** [1-2 sentences on why autonomous agents would excel here]

    Be specific and realistic - avoid generic problems."""}]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )

    pain_point = response.choices[0].message.content

    print("Pain point:")
    print(pain_point)
    print("\n" + "="*80 + "\n")

    # Third iteration: Design solution
    messages = [{"role": "user", "content": f"""Industry context:
    {industry}

    Pain-point identified:
    {pain_point}

    Design an Agentic AI solution that addresses this pain-point. Your solution must:
    1. Use autonomous agents that can make decisions and take actions
    2. Be technically feasible with current AI capabilities
    3. Provide clear ROI for potential clients
    4. Be implementable by a small team or solo developer
    5. Scale effectively as the business grows

    Provide your response in this format:
    **Solution name:** [Catchy, professional name]
    **How it works:** [3-4 sentences describing the agent workflow]
    **Key agent capabilities:** [Bullet list of 3-5 specific things the agent does]
    **Technology stack:** [High-level overview - LLMs, APIs, tools needed]
    **Value proposition:** [1-2 sentences on the measurable benefit to clients]
    **MVP approach:** [2-3 sentences on how to start small and validate]

    Be specific, practical, and actionable."""}]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )

    solution = response.choices[0].message.content

    print("Solution:")
    print(solution)


if __name__ == "__main__":
    main()

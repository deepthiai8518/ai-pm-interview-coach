from openai import OpenAI
import json
import random

client = None

def set_openai_client(api_key: str):
    """Set the OpenAI client"""
    global client
    client = OpenAI(api_key=api_key)

# Store conversations for context
conversation_store = {}

def get_pm_question(params: dict):
    """
    Generate open-ended AI PM interview question.
    params = {"level": "intermediate", "topic": "architecture"}
    """
    if not client:
        return {"error": "OpenAI client not initialized"}
    
    level = params.get("level", "intermediate")
    topic = params.get("topic", "ai_strategy")
    
    # Topic descriptions
    topic_map = {
        "ai_strategy": "AI Product Strategy & Vision - Building AI products, market fit, competitive positioning",
        "architecture": "AI Architecture & System Design - RAG systems, LLM orchestration, agentic patterns, vector databases",
        "evaluation": "AI Evaluation & Metrics - Model performance, user satisfaction, A/B testing, success metrics",
        "design_patterns": "AI Design Patterns - Prompt engineering, chain-of-thought, reflection loops, human-in-the-loop",
        "data_privacy": "Data Governance & Privacy - Compliance, PII handling, data pipelines, security",
        "product_execution": "Product Execution - Roadmapping, stakeholder management, tradeoffs, MVP scoping",
        "agents": "AI Agents & Orchestration - Multi-agent systems, tool use, agent design patterns",
        "ml_ops": "ML Ops & Infrastructure - Model deployment, monitoring, scaling, CI/CD for ML",
        "user_experience": "User Experience & UX - AI product design, user interaction patterns, trust building",
        "pricing": "Pricing & Monetization - AI business models, pricing strategies, cost optimization",
        "safety": "AI Safety & Ethics - Responsible AI, bias, fairness, alignment, guardrails",
        "competitive": "Competitive Analysis - Market positioning, competitor analysis, differentiation"
    }
    
    topic_name = topic_map.get(topic, topic)
    question_id = random.randint(1000, 9999)
    
    prompt = f"""Generate a realistic AI Product Manager interview question.

Topic: {topic_name}
Difficulty: {level}

Requirements:
1. Ask an open-ended question that requires reasoning, not just facts
2. Question should assess product thinking, not just technical knowledge
3. Should be something a real AI PM would face
4. Focus on decision-making, tradeoffs, and strategic thinking

Examples of good questions:
- "You're building a customer support chatbot. How would you decide between fine-tuning vs RAG?"
- "Your RAG system has 60% accuracy. Walk me through how you'd diagnose and improve it."
- "How would you evaluate if your AI feature is actually providing value to users?"

Return ONLY valid JSON:
{{
    "question": "Your open-ended question here",
    "evaluation_criteria": ["What to look for in answer 1", "What to look for 2", "What to look for 3"]
}}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a senior AI Product Manager conducting interviews. Generate realistic, thought-provoking questions."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
        )
        
        content = response.choices[0].message.content.strip()
        
        # Clean markdown
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        question_data = json.loads(content)
        question_data["id"] = question_id
        question_data["level"] = level
        question_data["topic"] = topic
        
        # Store question
        conversation_store[question_id] = {
            "question": question_data,
            "user_answer": None,
            "evaluation": None
        }
        
        return question_data
        
    except Exception as e:
        # Fallback question
        fallback_id = random.randint(1000, 9999)
        fallback = {
            "id": fallback_id,
            "question": "You're building a RAG system for internal company documentation. How would you approach evaluating whether it's working well?",
            "evaluation_criteria": [
                "Mentions both quantitative metrics (accuracy, latency) and qualitative measures (user satisfaction)",
                "Discusses retrieval quality vs generation quality",
                "Considers user context and different query types"
            ],
            "level": level,
            "topic": topic
        }
        conversation_store[fallback_id] = {
            "question": fallback,
            "user_answer": None,
            "evaluation": None
        }
        return fallback


def evaluate_pm_answer(params: dict):
    """
    Evaluate user's answer with detailed feedback and framework.
    params = {"id": 1234, "answer": "user's response"}
    """
    if not client:
        return {"error": "OpenAI client not initialized"}
    
    question_id = int(params["id"])
    user_answer = params["answer"]
    
    if question_id not in conversation_store:
        return {"error": f"Question not found. Please request a new question. (ID: {question_id})"}
    
    question_data = conversation_store[question_id]["question"]
    
    # Quality-based evaluation prompt (NOT word count based)
    eval_prompt = f"""You are a STRICT and HONEST evaluator for AI Product Manager interview answers.
Your job is to give accurate, helpful feedback based on QUALITY, not length.

**Question Asked:**
{question_data['question']}

**Candidate's Answer:**
{user_answer}

**Evaluation Criteria:**
{chr(10).join(f"- {c}" for c in question_data['evaluation_criteria'])}

---

**SCORING RUBRIC (Based on QUALITY, not word count):**

**Score 1 (Poor) - Answer fails to address the question:**
- "I don't know" or equivalent non-answers
- Completely off-topic or irrelevant response
- Shows fundamental misunderstanding of the concept
- Just restates the question without answering
- Random or incoherent response

**Score 2 (Below Average) - Answer attempts but fails:**
- Addresses the topic but not the specific question
- Extremely vague with no actionable content
- Mentions buzzwords without demonstrating understanding
- Incomplete thought that doesn't reach a conclusion
- Surface-level response with no depth

**Score 3 (Average) - Answer is acceptable but basic:**
- Answers the question but only covers obvious points
- Lacks specific examples, metrics, or concrete approaches
- Missing 1-2 key aspects from evaluation criteria
- Shows understanding but no differentiated thinking
- Would pass but not impress in an interview

**Score 4 (Good) - Answer demonstrates solid PM thinking:**
- Directly addresses all parts of the question
- Includes specific metrics, examples, or approaches
- Shows clear reasoning and structured thinking
- Considers tradeoffs or multiple perspectives
- Would perform well in a real interview

**Score 5 (Excellent) - Answer demonstrates senior-level mastery:**
- Comprehensive and well-structured response
- Demonstrates deep understanding with nuanced insights
- Includes concrete examples AND explains reasoning
- Proactively addresses edge cases or risks
- Shows business acumen alongside technical knowledge
- Would stand out in a competitive interview

---

**CRITICAL RULES FOR FEEDBACK:**

1. **DO NOT use word count as a scoring factor** - A concise 50-word answer with clear structure and specifics beats a rambling 200-word answer

2. **Score based on these qualities:**
   - RELEVANCE: Does it answer what was asked?
   - STRUCTURE: Is there a clear framework or approach?
   - SPECIFICITY: Are there concrete metrics, examples, or methods?
   - DEPTH: Does it show real understanding?
   - PM THINKING: Does it consider business, users, and technical aspects?

3. **For Score 1-2 answers:**
   - strong_points should be EMPTY [] unless there's a genuinely good element
   - DO NOT give fake praise like "Good effort" or "Attempted to answer"
   - Be honest about what's missing

4. **For all answers:**
   - missing_points should be SPECIFIC and ACTIONABLE
   - weak_areas should explain the actual problems
   - framework should be relevant and memorable
   - senior_pm_answer should model excellence

---

**CALIBRATION EXAMPLES:**

Example 1 - Score 1:
Q: "How would you measure success for a recommendation system?"
A: "I would look at the metrics"
Why: No specific metrics mentioned, no approach, doesn't demonstrate any PM knowledge

Example 2 - Score 2:
Q: "How would you measure success for a recommendation system?"
A: "I would track engagement and see if users like the recommendations by looking at click rates and maybe doing some surveys"
Why: Mentions relevant concepts (engagement, clicks, surveys) but extremely vague, no specific metrics or methodology

Example 3 - Score 3:
Q: "How would you measure success for a recommendation system?"
A: "I'd measure CTR on recommendations, track conversion rates, and monitor user retention. I'd also look at recommendation diversity to avoid filter bubbles."
Why: Good metrics mentioned, shows understanding, but lacks specificity on targets, methodology, or tradeoffs

Example 4 - Score 4:
Q: "How would you measure success for a recommendation system?"
A: "I'd establish a metrics hierarchy: 1) Business metrics like revenue per user and conversion rate, 2) Engagement metrics like CTR (target >5%) and time-to-first-click, 3) Quality metrics like recommendation diversity and coverage. I'd run A/B tests comparing against baseline, with guardrail metrics for user satisfaction to catch negative side effects."
Why: Structured approach, specific targets, considers multiple dimensions, mentions methodology (A/B tests) and tradeoffs (guardrails)

Example 5 - Score 5:
Q: "How would you measure success for a recommendation system?"
A: "I'd build a measurement framework across three layers: Business Impact (revenue lift, LTV changes, margin impact), User Value (task completion rate, return visits, NPS delta), and System Health (latency p95, coverage, cold-start performance). For methodology, I'd use interleaved experiments for faster iteration and A/B tests for final validation. Key tradeoff: optimizing for clicks vs. long-term satisfaction—I'd add guardrails for diversity and serendipity to prevent filter bubbles. For cold-start users, I'd separately track onboarding conversion. Success criteria: 10% revenue lift with no NPS degradation."
Why: Comprehensive framework, specific metrics with targets, clear methodology, proactively addresses tradeoffs and edge cases, shows senior-level systems thinking

---

Return ONLY valid JSON:
{{
    "score": <1-5>,
    "rating_label": "<Poor|Below Average|Average|Good|Excellent>",
    "strong_points": ["Specific strength from their answer"] OR [] if none exist,
    "missing_points": ["Specific thing they should have included 1", "Specific thing 2"],
    "weak_areas": ["Specific problem with their answer 1", "Specific problem 2"],
    "framework": {{
        "name": "MEMORABLE FRAMEWORK NAME",
        "acronym": "What each letter stands for",
        "steps": ["Step 1: specific action", "Step 2: specific action", "Step 3: specific action"]
    }},
    "senior_pm_answer": "A 3-4 sentence model answer showing how a senior PM would respond with specifics."
}}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert AI PM interviewer. Evaluate based on QUALITY and SUBSTANCE, not length. Be HONEST - never give false praise for poor answers. Your feedback should help candidates genuinely improve."},
                {"role": "user", "content": eval_prompt}
            ],
            temperature=0.3,
        )
        
        content = response.choices[0].message.content.strip()
        
        # Clean markdown
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        evaluation = json.loads(content)
        
        # GUARDRAIL: If score is 1-2, filter out fake praise from strong_points
        score = evaluation.get("score", 3)
        if score <= 2:
            strong_points = evaluation.get("strong_points", [])
            fake_praise_phrases = [
                "good effort", "attempted", "tried", "willingness", "engaged",
                "showed interest", "at least", "effort to", "brave", "honest",
                "courage", "acknowledge", "admitted", "recognize"
            ]
            filtered_strengths = []
            for point in strong_points:
                point_lower = point.lower()
                is_fake = any(phrase in point_lower for phrase in fake_praise_phrases)
                if not is_fake:
                    filtered_strengths.append(point)
            evaluation["strong_points"] = filtered_strengths
        
        # Store evaluation
        conversation_store[question_id]["user_answer"] = user_answer
        conversation_store[question_id]["evaluation"] = evaluation
        
        return evaluation
        
    except Exception as e:
        return {
            "error": f"Evaluation failed: {str(e)}",
            "score": 1,
            "rating_label": "Poor",
            "strong_points": [],
            "missing_points": ["Unable to evaluate - please try again"],
            "weak_areas": ["Evaluation error occurred"],
            "framework": {
                "name": "STAR Framework",
                "acronym": "Situation-Task-Action-Result",
                "steps": [
                    "Situation: Describe the context",
                    "Task: What was required",
                    "Action: What you did/would do",
                    "Result: Expected outcomes and metrics"
                ]
            },
            "senior_pm_answer": "A senior PM would structure their answer with clear context, specific actions, and measurable outcomes."
        }

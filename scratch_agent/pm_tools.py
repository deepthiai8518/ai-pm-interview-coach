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
        "product_execution": "Product Execution - Roadmapping, stakeholder management, tradeoffs, MVP scoping"
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
        
        # Store question with INTEGER key (consistent with question_id)
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
    
    # Convert to int for consistent key lookup
    question_id = int(params["id"])
    user_answer = params["answer"]
    
    if question_id not in conversation_store:
        return {"error": f"Question not found. Please request a new question. (ID: {question_id})"}
    
    question_data = conversation_store[question_id]["question"]
    
    # Comprehensive evaluation prompt
    eval_prompt = f"""
You are a STRICT evaluator for AI Product Manager interview answers.
You are calibrated to real interview standards where incomplete, vague, or unstructured answers do not pass.

Your job is NOT to encourage the candidate.
Your job is to judge whether this answer would pass a real AI PM interview round.

---

**Question Asked:**

{question_data['question']}

**Candidate's Answer:**

{user_answer}

---

**Evaluation Criteria:**

{chr(10).join(f"- {c}" for c in question_data['evaluation_criteria'])}

---

## STRICT EVALUATION PROCESS (FOLLOW IN ORDER)

### STEP 1: AUTOMATIC CAPS (APPLY FIRST — OVERRIDES EVERYTHING)

Apply these caps BEFORE judging quality.

### 1️⃣ INCOMPLETE ANSWERS → **Cap at 2**

An answer is INCOMPLETE if:
- It cuts off mid-sentence or mid-thought
- It is under ~50 words AND does not clearly address all parts of the question
- It restates the question without answering it
- It says what the candidate *would* do without actually doing it

### 2️⃣ PARTIAL ANSWERS → **Cap at 2**

An answer is PARTIAL if:
- The question is multi-part and only one part is addressed
- Key aspects are ignored (e.g., asked about trade-offs but none are mentioned)
- Metrics, users, or decisions are mentioned but not connected

### 3️⃣ VAGUE ANSWERS → **Cap at 3**

An answer is VAGUE if:
- It uses generic statements that apply to any AI problem
- It lacks concrete metrics, examples, decision rules, or trade-offs
- It relies on buzzwords without showing understanding

⚠️ NOTE ON WORD COUNT:
Answers under ~50 words are PRESUMED incomplete,
UNLESS they clearly address all required dimensions with specificity.
Word count alone does not determine quality.

---

## STEP 2: CONTENT QUALITY SCORING (WITHIN THE CAP)

Score based on reasoning quality, structure, and interview readiness.

### SCORING RUBRIC

- **1 = Poor**
  Fragmented, off-topic, incorrect, or shows misunderstanding

- **2 = Below Average**
  Partially correct but missing major components or depth

- **3 = Average**
  Complete and coherent, but lacks strong structure, specificity, or trade-offs

- **4 = Good**
  Well-structured, addresses all parts, includes concrete metrics/examples,
  shows clear reasoning and trade-off awareness

- **5 = Excellent**
  Senior PM-level answer:
  - Structured and prioritized
  - Explicit trade-offs and decision logic
  - Clear linkage between model metrics, user impact, and business outcomes
  - Actionable and interview-ready

---

## CALIBRATION EXAMPLES

- "I would look at the metrics and make a decision."
  → **Score 1** (vague, no substance)

- "I'd analyze engagement and satisfaction separately to find the root cause—"
  → **Score 2** (cuts off, incomplete)

- "I'd segment users by behavior type to see which groups drive satisfaction changes, then decide based on business importance."
  → **Score 3** (reasonable but lacks concrete metrics or thresholds)

- "I'd break engagement into clicks, add-to-cart, and purchases, and pair that with satisfaction by user segment. If high-value users show dissatisfaction, I'd pause rollout and iterate. I'd set a guardrail: no more than a 2% drop in satisfaction over two sprints."
  → **Score 4** (specific, complete, actionable)

---

## OUTPUT FORMAT (STRICT)

Return ONLY valid JSON. No explanations. No markdown. No extra text.

{
  "score": <1-5>,
  "rating_label": "<Poor|Below Average|Average|Good|Excellent>",
  "strong_points": ["Specific strength 1", "Specific strength 2"],
  "missing_points": ["What they should have included 1", "What they missed 2"],
  "weak_areas": ["Where reasoning was weak 1", "Area to improve 2"],
  "framework": {
    "name": "FRAMEWORK NAME",
    "acronym": "What each letter stands for",
    "steps": [
      "Step 1: ...",
      "Step 2: ...",
      "Step 3: ..."
    ],
    "application": "How to use this in interviews"
  },
  "senior_pm_answer": "A senior PM would..."
}}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # Use GPT-4 for better evaluation
            messages=[
                {"role": "system", "content": "You are an expert AI Product Manager interviewer providing detailed, constructive, and actionable feedback. Create memorable frameworks that candidates can use in future interviews."},
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
        
        # Store evaluation
        conversation_store[question_id]["user_answer"] = user_answer
        conversation_store[question_id]["evaluation"] = evaluation
        
        return evaluation
        
    except Exception as e:
        return {
            "error": f"Evaluation failed: {str(e)}",
            "score": 3,
            "rating_label": "Average",
            "strong_points": ["You provided a thoughtful response"],
            "missing_points": ["More specific details needed"],
            "weak_areas": ["Consider multiple perspectives"],
            "framework": {
                "name": "BASIC Framework",
                "acronym": "Business-Architecture-Safety-Impact-Costs",
                "steps": [
                    "Business: What's the business goal?",
                    "Architecture: What technical approach?",
                    "Safety: What could go wrong?",
                    "Impact: How to measure success?",
                    "Costs: What are the tradeoffs?"
                ],
                "application": "Use this to structure any AI PM answer"
            },
            "senior_pm_answer": "Consider the full context including business impact, technical feasibility, and user needs."
        }

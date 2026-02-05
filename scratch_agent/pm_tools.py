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
    eval_prompt = f"""You are evaluating an AI Product Manager candidate's interview answer.

**Question Asked:**
{question_data['question']}

**Candidate's Answer:**
{user_answer}

**Evaluation Criteria:**
{chr(10).join(f"- {c}" for c in question_data['evaluation_criteria'])}

Provide a comprehensive evaluation with:

1. **SCORE (1-5):**
   - 1 = Poor (misses key points, lacks understanding)
   - 2 = Below Average (surface-level, missing critical thinking)
   - 3 = Average (covers basics, lacks depth)
   - 4 = Good (solid reasoning, covers most criteria)
   - 5 = Excellent (comprehensive, shows senior PM thinking)

2. **STRONG POINTS:** What the candidate did well (be specific)

3. **MISSING POINTS:** Critical aspects they didn't mention or explore

4. **WEAK AREAS:** Where their reasoning could be stronger

5. **FRAMEWORK TO REMEMBER:** A clear, memorable framework for answering similar questions
   - Use acronyms or memorable structures (e.g., "METRICS", "SCOPE", "TRADE")
   - Make it actionable and easy to recall in interviews
   - Should be 3-5 key points they can use for this type of question

6. **SENIOR PM ANSWER:** What a strong answer would include (2-3 sentences)

Return ONLY valid JSON:
{{
    "score": 4,
    "rating_label": "Good",
    "strong_points": ["Specific strength 1", "Specific strength 2"],
    "missing_points": ["Critical point they missed 1", "Critical point 2"],
    "weak_areas": ["Area where reasoning could improve 1", "Area 2"],
    "framework": {{
        "name": "FRAMEWORK NAME",
        "acronym": "Each letter stands for...",
        "steps": [
            "Step 1: Do this",
            "Step 2: Then this",
            "Step 3: Finally this"
        ],
        "application": "How to apply this framework in interviews"
    }},
    "senior_pm_answer": "A senior PM would approach this by..."
}}"""

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

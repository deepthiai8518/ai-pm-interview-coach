import streamlit as st
import pandas as pd
from scratch_agent.pm_tools import get_pm_question, evaluate_pm_answer, set_openai_client

st.set_page_config(page_title="AI PM Interview Coach", layout="wide")

# Header
col1, col2 = st.columns([3, 1])
with col1:
    st.title("🎯 AI PM Interview Coach")
    st.caption("Master AI Product Management with 180 interview questions across 12 topics")

with col2:
    st.write("")  # Spacing

# API Key Input
st.markdown("---")
col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    api_key = st.text_input(
        "🔑 Enter your OpenAI API Key",
        type="password",
        key="api_key_input",
        help="Get your key at https://platform.openai.com/api-keys"
    )

with col2:
    st.markdown("**Don't have an API key?**")
    st.markdown("[Get free OpenAI API key →](https://platform.openai.com/api-keys)")

with col3:
    st.write("")

api_key_value = st.session_state.get("api_key_input", "")

if not api_key_value:
    st.warning("⚠️ Please enter your OpenAI API key above to begin. Your key is never stored or shared.")
    st.stop()

if "tools_initialized" not in st.session_state:
    set_openai_client(api_key_value)
    st.session_state.tools_initialized = True
    st.success("✅ API Connected! Ready to practice!")

# Topic definitions
TOPICS = {
    "ai_strategy": "🎯 AI Strategy & Vision",
    "architecture": "🏗️ RAG & Architecture",
    "evaluation": "📊 Evaluation & Metrics",
    "design_patterns": "🎨 Design Patterns",
    "data_privacy": "🔐 Privacy & Governance",
    "product_execution": "⚙️ Product Execution",
    "agents": "🤖 AI Agents & Orchestration",
    "ml_ops": "🔧 ML Ops & Infrastructure",
    "user_experience": "👥 User Experience & UX",
    "pricing": "💰 Pricing & Monetization",
    "safety": "🛡️ AI Safety & Ethics",
    "competitive": "⚔️ Competitive Analysis",
}

QUESTIONS_PER_TOPIC = 15

def get_score_color(score):
    """Return color and emoji for score"""
    if score >= 4:
        return "🟢", "#00AA00"
    elif score == 3:
        return "🟡", "#FFA500"
    else:
        return "🔴", "#DD0000"

# Initialize session state
if "messages_by_topic" not in st.session_state:
    st.session_state.messages_by_topic = {topic: [] for topic in TOPICS.keys()}

if "current_topic" not in st.session_state:
    st.session_state.current_topic = None

if "current_question_id" not in st.session_state:
    st.session_state.current_question_id = None

if "awaiting_answer" not in st.session_state:
    st.session_state.awaiting_answer = False

if "topic_progress" not in st.session_state:
    st.session_state.topic_progress = {topic: 0 for topic in TOPICS.keys()}

if "topic_answers" not in st.session_state:
    st.session_state.topic_answers = {topic: [] for topic in TOPICS.keys()}

if "topic_attempted" not in st.session_state:
    st.session_state.topic_attempted = {topic: 0 for topic in TOPICS.keys()}

if "topic_skipped" not in st.session_state:
    st.session_state.topic_skipped = {topic: 0 for topic in TOPICS.keys()}

if "topic_skipped_questions" not in st.session_state:
    st.session_state.topic_skipped_questions = {topic: [] for topic in TOPICS.keys()}

if "reviewing_skipped" not in st.session_state:
    st.session_state.reviewing_skipped = False

if "retry_mode" not in st.session_state:
    st.session_state.retry_mode = False

if "show_retry_buttons" not in st.session_state:
    st.session_state.show_retry_buttons = False

if "last_score" not in st.session_state:
    st.session_state.last_score = None

if "last_framework" not in st.session_state:
    st.session_state.last_framework = None

if "reviewing_answer_idx" not in st.session_state:
    st.session_state.reviewing_answer_idx = None

if "current_question_number" not in st.session_state:
    st.session_state.current_question_number = None

if "retry_question_id" not in st.session_state:
    st.session_state.retry_question_id = None

# NEW: Store the actual question text separately (not parsed from messages)
if "current_question_text" not in st.session_state:
    st.session_state.current_question_text = None

# SIDEBAR MENU
st.sidebar.header("📚 Topics")

for topic_key, topic_label in TOPICS.items():
    answered = len(st.session_state.topic_answers[topic_key])
    skipped = st.session_state.topic_skipped[topic_key]
    
    if st.sidebar.button(
        f"{topic_label}\n(✅ {answered} | ⏭️ {skipped})",
        key=f"sidebar_{topic_key}",
        use_container_width=True
    ):
        st.session_state.current_topic = topic_key
        st.session_state.awaiting_answer = False
        st.session_state.show_retry_buttons = False
        st.session_state.current_question_id = None
        st.session_state.retry_mode = False
        st.session_state.retry_question_id = None
        st.session_state.reviewing_answer_idx = None
        st.session_state.current_question_number = None
        st.session_state.current_question_text = None
        st.rerun()
    
    st.sidebar.progress(answered / QUESTIONS_PER_TOPIC, text=f"{answered}/{QUESTIONS_PER_TOPIC}")

st.sidebar.markdown("---")
if st.sidebar.button("🏠 Home", use_container_width=True):
    st.session_state.current_topic = None
    st.session_state.awaiting_answer = False
    st.session_state.reviewing_answer_idx = None
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption("Developed by **Deepthi**")

# MAIN CONTENT
if st.session_state.current_topic is None:
    # Home page
    st.markdown("""
    ## Welcome to Your AI PM Interview Coach! 🎓
    
    Practice **15 realistic interview questions** for each of 12 AI Product Management topics.
    
    ### How it works:
    1. **Select a topic** from the sidebar
    2. **Answer questions** (15 per topic)
    3. **Get detailed feedback** with scores, frameworks, and senior PM insights
    4. **Track progress** with color-coded scores
    
    ### Topics:
    """)
    
    col1, col2 = st.columns(2)
    topics_list = list(TOPICS.items())
    
    for i, (key, label) in enumerate(topics_list):
        with col1 if i % 2 == 0 else col2:
            st.write(f"• **{label}**")
    
    st.markdown("### Your Progress:")
    
    total_answered = sum(len(answers) for answers in st.session_state.topic_answers.values())
    total_questions = len(TOPICS) * QUESTIONS_PER_TOPIC
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Questions Answered", total_answered)
    with col2:
        st.metric("Total Questions", total_questions)
    with col3:
        st.metric("Completion", f"{int((total_answered/total_questions)*100)}%")
    with col4:
        completed = sum(1 for t in TOPICS.keys() if len(st.session_state.topic_answers[t]) >= QUESTIONS_PER_TOPIC)
        st.metric("Topics Completed", completed)
    
    # Analytics
    all_answers = []
    for answers in st.session_state.topic_answers.values():
        all_answers.extend(answers)
    
    if all_answers:
        st.markdown("---")
        st.subheader("📈 Performance Summary")
        
        all_scores = [a.get("score", 0) for a in all_answers]
        avg_score = sum(all_scores) / len(all_scores)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Average Score", f"{avg_score:.1f}/5")
        with col2:
            excellent = sum(1 for s in all_scores if s >= 4)
            st.metric("Excellent (4-5)", excellent)
        with col3:
            average = sum(1 for s in all_scores if s == 3)
            st.metric("Average (3)", average)
        with col4:
            needs_work = sum(1 for s in all_scores if s <= 2)
            st.metric("Needs Work (1-2)", needs_work)

else:
    # Topic page
    topic_key = st.session_state.current_topic
    topic_label = TOPICS[topic_key]
    answered = len(st.session_state.topic_answers[topic_key])
    messages = st.session_state.messages_by_topic[topic_key]
    
    # Header
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.header(topic_label)
    with col2:
        st.metric("✅ Answered", f"{answered}/15")
    with col3:
        skipped = st.session_state.topic_skipped[topic_key]
        st.metric("⏭️ Skipped", f"{skipped}")
    
    st.progress(answered / QUESTIONS_PER_TOPIC, text=f"Answered: {answered}/15 | Skipped: {skipped}/15")
    
    # Show answered questions
    if answered > 0:
        st.subheader("Your Answers (click to review):")
        answers = st.session_state.topic_answers[topic_key]
        
        cols_per_row = 5
        rows = (len(answers) + cols_per_row - 1) // cols_per_row
        
        for row in range(rows):
            cols = st.columns(cols_per_row, gap="small")
            for col_idx in range(cols_per_row):
                answer_idx = row * cols_per_row + col_idx
                if answer_idx < len(answers):
                    ans = answers[answer_idx]
                    score = ans.get("score", "N/A")
                    emoji, _ = get_score_color(score)
                    question_num = ans.get("question_number", answer_idx + 1)
                    
                    with cols[col_idx]:
                        is_selected = st.session_state.reviewing_answer_idx == answer_idx
                        if st.button(
                            f"{emoji} Q{question_num}\nScore: {score}/5",
                            key=f"review_q_{answer_idx}",
                            use_container_width=True,
                            type="primary" if is_selected else "secondary"
                        ):
                            st.session_state.reviewing_answer_idx = None if is_selected else answer_idx
                            st.rerun()
        
        # Review panel
        if st.session_state.reviewing_answer_idx is not None:
            idx = st.session_state.reviewing_answer_idx
            if idx < len(answers):
                ans = answers[idx]
                score = ans.get("score", "N/A")
                emoji, _ = get_score_color(score)
                question_num = ans.get("question_number", idx + 1)
                
                st.markdown("---")
                st.subheader(f"📋 Review: Question {question_num}")
                
                if st.button("✕ Close Review", key="close_review"):
                    st.session_state.reviewing_answer_idx = None
                    st.rerun()
                
                # ALWAYS show question
                st.markdown("### 📝 Question")
                question_text = ans.get("question_text", "")
                if question_text:
                    st.info(question_text)
                else:
                    st.warning("Question text not available")
                
                # ALWAYS show user's answer
                st.markdown("### 💬 Your Answer")
                user_answer = ans.get("answer", "")
                if user_answer:
                    st.warning(user_answer)
                else:
                    st.warning("Answer not available")
                
                # Evaluation header
                st.markdown(f"### {emoji} Evaluation: {score}/5 ({ans.get('rating', '')})")
                
                # Strong points - only show if there are actual strengths
                strong_points = ans.get("strong_points", [])
                if strong_points and len(strong_points) > 0:
                    st.markdown("**✅ Strong Points:**")
                    for point in strong_points:
                        st.write(f"• {point}")
                # If no strong points for poor scores, that's expected - don't show section
                
                # Missing points - always show
                missing_points = ans.get("missing_points", [])
                if missing_points:
                    st.markdown("**❌ Missing Points:**")
                    for point in missing_points:
                        st.write(f"• {point}")
                
                # Weak areas - always show
                weak_areas = ans.get("weak_areas", [])
                if weak_areas:
                    st.markdown("**⚠️ Areas to Develop:**")
                    for area in weak_areas:
                        st.write(f"• {area}")
                
                # How to Answer - step by step guidance
                how_to_answer = ans.get("how_to_answer", [])
                if how_to_answer:
                    st.markdown("**📝 How to Answer This Question:**")
                    for i, step in enumerate(how_to_answer, 1):
                        st.write(f"{i}. {step}")
                
                # Framework
                framework = ans.get("framework", {})
                if framework and isinstance(framework, dict):
                    st.markdown("**🎯 Framework:**")
                    fw_name = framework.get("name", "")
                    fw_steps = framework.get("steps", [])
                    if fw_name:
                        st.write(f"**{fw_name}**")
                    for i, step in enumerate(fw_steps, 1):
                        st.write(f"{i}. {step}")
                
                # Senior PM answer
                senior_answer = ans.get("senior_pm_answer", "")
                if senior_answer:
                    st.markdown("**💡 Senior PM Perspective:**")
                    st.write(senior_answer)
        
        st.markdown("---")
    
    # Skipped questions
    skipped_questions = st.session_state.topic_skipped_questions[topic_key]
    if skipped_questions:
        st.subheader(f"⏭️ Skipped Questions ({len(skipped_questions)})")
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("📋 Review Skipped", use_container_width=True, key="review_skipped_btn"):
                st.session_state.reviewing_skipped = True
                st.rerun()
        with col2:
            st.write(f"**{len(skipped_questions)} question(s) waiting**")
        
        if st.session_state.reviewing_skipped:
            for i, skipped_q in enumerate(skipped_questions):
                st.markdown(f"### Question {skipped_q['attempt_number']} (Skipped)")
                st.markdown(skipped_q["question_text"])
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"✅ Attempt", key=f"attempt_skipped_{i}", use_container_width=True):
                        st.session_state.current_question_id = skipped_q["question_id"]
                        st.session_state.current_question_number = skipped_q["attempt_number"]
                        st.session_state.current_question_text = skipped_q["question_text"]  # Store question text
                        st.session_state.awaiting_answer = True
                        st.session_state.reviewing_skipped = False
                        st.session_state.messages_by_topic[topic_key] = [{
                            "role": "assistant",
                            "content": f"**Question {skipped_q['attempt_number']}/15:**\n\n{skipped_q['question_text']}\n\n*Take your time and provide a thoughtful answer.*"
                        }]
                        st.rerun()
                with col2:
                    if st.button(f"🗑️ Remove", key=f"remove_skipped_{i}", use_container_width=True):
                        st.session_state.topic_skipped_questions[topic_key].pop(i)
                        st.session_state.topic_skipped[topic_key] -= 1
                        st.rerun()
                st.markdown("---")
    
    # Completed topic
    if answered >= QUESTIONS_PER_TOPIC:
        st.success("🎉 You've completed all 15 questions for this topic!")
        
        answers = st.session_state.topic_answers[topic_key]
        avg_score = sum(a.get("score", 0) for a in answers) / len(answers) if answers else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Average Score", f"{avg_score:.1f}/5")
        with col2:
            excellent = sum(1 for a in answers if a.get("score", 0) >= 4)
            st.metric("Excellent (4-5)", excellent)
        with col3:
            needs_work = sum(1 for a in answers if a.get("score", 0) <= 2)
            st.metric("Needs Work (1-2)", needs_work)
        
        if st.button("← Back to Topics"):
            st.session_state.current_topic = None
            st.rerun()
    else:
        # Show messages
        messages_to_show = messages[-4:] if len(messages) > 4 else messages
        for msg in messages_to_show:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        
        # Answer input
        if st.session_state.awaiting_answer:
            st.markdown("---")
            
            if not st.session_state.show_retry_buttons:
                # Show different label if in retry mode
                if st.session_state.retry_mode:
                    st.markdown("**🔄 Practice Answer (using framework):**")
                    st.caption("This is practice only - your original score is already recorded.")
                else:
                    st.markdown("**Your Answer:**")
                
                user_input = st.text_area(
                    "Type your answer here...",
                    key="answer_text_area",
                    height=150,
                    label_visibility="collapsed",
                    placeholder="Type your answer here..."
                )
                
                # Different buttons for retry mode vs normal mode
                if st.session_state.retry_mode:
                    # RETRY MODE
                    col_skip, col_submit = st.columns([1, 2])
                    
                    with col_skip:
                        if st.button("⏭️ Skip to Next Question", use_container_width=True, key="skip_retry_btn"):
                            st.session_state.retry_mode = False
                            st.session_state.retry_question_id = None
                            st.session_state.show_retry_buttons = False
                            st.session_state.current_question_id = None
                            st.session_state.current_question_number = None
                            st.session_state.current_question_text = None
                            st.session_state.awaiting_answer = False
                            st.session_state.last_score = None
                            st.session_state.last_framework = None
                            
                            current_attempted = st.session_state.topic_attempted[topic_key]
                            if current_attempted < QUESTIONS_PER_TOPIC:
                                with st.spinner("Loading next question..."):
                                    result = get_pm_question({"level": "intermediate", "topic": topic_key})
                                    question_text = result.get("question", "Error")
                                    question_id = result.get("id")
                                    
                                    st.session_state.topic_attempted[topic_key] += 1
                                    next_question_num = st.session_state.topic_attempted[topic_key]
                                    
                                    st.session_state.current_question_id = question_id
                                    st.session_state.current_question_number = next_question_num
                                    st.session_state.current_question_text = question_text  # Store question
                                    st.session_state.awaiting_answer = True
                                    
                                    st.session_state.messages_by_topic[topic_key] = [{
                                        "role": "assistant",
                                        "content": f"**Question {next_question_num}/15:**\n\n{question_text}\n\n*Take your time and provide a thoughtful answer.*"
                                    }]
                            st.rerun()
                    
                    with col_submit:
                        submit_disabled = not user_input or len(user_input.strip()) == 0
                        if st.button("📤 Submit Practice Answer", use_container_width=True, key="submit_practice_btn", disabled=submit_disabled, type="primary"):
                            st.session_state.messages_by_topic[topic_key].append({"role": "user", "content": user_input})
                            
                            with st.spinner("Evaluating your practice answer..."):
                                eval_result = evaluate_pm_answer({
                                    "id": st.session_state.retry_question_id,
                                    "answer": user_input
                                })
                                
                                score = eval_result.get("score", "N/A")
                                rating = eval_result.get("rating_label", "")
                                strong_points = eval_result.get("strong_points", [])
                                missing_points = eval_result.get("missing_points", [])
                                weak_areas = eval_result.get("weak_areas", [])
                                senior_perspective = eval_result.get("senior_pm_answer", "")
                                
                                # Build evaluation text - NO fake fallbacks
                                eval_sections = [f"## 📊 Practice Evaluation {get_score_color(score)[0]}"]
                                eval_sections.append(f"\n### Practice Score: **{score}/5** {f'({rating})' if rating else ''}")
                                eval_sections.append("\n*This is practice - your official score is already recorded.*")
                                
                                if strong_points:
                                    eval_sections.append("\n\n### ✅ Strong Points")
                                    for p in strong_points:
                                        eval_sections.append(f"\n• {p}")
                                
                                if missing_points:
                                    eval_sections.append("\n\n### ❌ Still Missing")
                                    for p in missing_points:
                                        eval_sections.append(f"\n• {p}")
                                
                                if weak_areas:
                                    eval_sections.append("\n\n### ⚠️ Areas to Develop")
                                    for a in weak_areas:
                                        eval_sections.append(f"\n• {a}")
                                
                                if senior_perspective:
                                    eval_sections.append(f"\n\n### 💡 Senior PM Perspective\n{senior_perspective}")
                                
                                eval_sections.append("\n\n---\n🎯 **Great practice!** Ready for the next question?")
                                
                                evaluation_text = "".join(eval_sections)
                                
                                st.session_state.messages_by_topic[topic_key].append({
                                    "role": "assistant",
                                    "content": evaluation_text
                                })
                                
                                st.session_state.retry_mode = False
                                st.session_state.retry_question_id = None
                                st.session_state.awaiting_answer = False
                                st.session_state.show_retry_buttons = True
                                st.session_state.last_score = 99  # Hide "Try Again" button
                                st.rerun()
                
                else:
                    # NORMAL MODE
                    col_skip, col_submit = st.columns([1, 2])
                    
                    with col_skip:
                        if st.button("⏭️ Skip", use_container_width=True, key="skip_btn"):
                            skipped_question_num = st.session_state.topic_attempted[topic_key]
                            
                            # Use stored question text instead of parsing
                            skipped_q_text = st.session_state.current_question_text or ""
                            
                            # Check if this question is already in the skipped list (re-skipping)
                            already_skipped = False
                            for sq in st.session_state.topic_skipped_questions[topic_key]:
                                if sq["question_id"] == st.session_state.current_question_id:
                                    already_skipped = True
                                    break
                            
                            # Only add to skipped list and increment counter if NOT already skipped
                            if not already_skipped:
                                st.session_state.topic_skipped_questions[topic_key].append({
                                    "question_id": st.session_state.current_question_id,
                                    "question_text": skipped_q_text,
                                    "attempt_number": skipped_question_num
                                })
                                st.session_state.topic_skipped[topic_key] += 1
                            
                            st.session_state.show_retry_buttons = False
                            st.session_state.current_question_id = None
                            st.session_state.current_question_number = None
                            st.session_state.current_question_text = None
                            st.session_state.awaiting_answer = False
                            st.session_state.retry_mode = False
                            
                            if messages and messages[-1]["role"] == "assistant":
                                st.session_state.messages_by_topic[topic_key].pop()
                            
                            st.rerun()
                    
                    with col_submit:
                        submit_disabled = not user_input or len(user_input.strip()) == 0
                        if st.button("📤 Submit Answer", use_container_width=True, key="submit_btn", disabled=submit_disabled, type="primary"):
                            st.session_state.messages_by_topic[topic_key].append({"role": "user", "content": user_input})
                            
                            # Use stored question text
                            question_text = st.session_state.current_question_text or ""
                            current_q_num = st.session_state.current_question_number or st.session_state.topic_attempted[topic_key]
                            
                            with st.spinner("Evaluating your answer..."):
                                eval_result = evaluate_pm_answer({
                                    "id": st.session_state.current_question_id,
                                    "answer": user_input
                                })
                                
                                score = eval_result.get("score", "N/A")
                                rating = eval_result.get("rating_label", "")
                                strong_points = eval_result.get("strong_points", [])
                                missing_points = eval_result.get("missing_points", [])
                                weak_areas = eval_result.get("weak_areas", [])
                                how_to_answer = eval_result.get("how_to_answer", [])
                                framework = eval_result.get("framework", {})
                                senior_perspective = eval_result.get("senior_pm_answer", "")
                                
                                emoji, _ = get_score_color(score)
                                
                                # Build evaluation text dynamically - NO fake fallbacks
                                eval_sections = [f"## 📊 Evaluation {emoji}"]
                                eval_sections.append(f"\n### Score: **{score}/5** {f'({rating})' if rating else ''}")
                                
                                # Only show Strong Points if there are actual strengths
                                if strong_points:
                                    eval_sections.append("\n\n### ✅ Strong Points")
                                    for p in strong_points:
                                        eval_sections.append(f"\n• {p}")
                                
                                # Always show Missing Points
                                if missing_points:
                                    eval_sections.append("\n\n### ❌ Missing Points")
                                    for p in missing_points:
                                        eval_sections.append(f"\n• {p}")
                                
                                # Always show Weak Areas
                                if weak_areas:
                                    eval_sections.append("\n\n### ⚠️ Areas to Develop")
                                    for a in weak_areas:
                                        eval_sections.append(f"\n• {a}")
                                
                                # How to Answer - step by step guidance
                                if how_to_answer:
                                    eval_sections.append("\n\n### 📝 How to Answer This Question")
                                    for i, step in enumerate(how_to_answer, 1):
                                        eval_sections.append(f"\n{i}. {step}")
                                
                                # Framework
                                if isinstance(framework, dict) and framework:
                                    fw_name = framework.get("name", "Framework")
                                    fw_steps = framework.get("steps", [])
                                    eval_sections.append(f"\n\n### 🎯 Framework to Remember\n**{fw_name}**")
                                    if fw_steps:
                                        for i, s in enumerate(fw_steps, 1):
                                            eval_sections.append(f"\n{i}. {s}")
                                
                                # Senior PM
                                if senior_perspective:
                                    eval_sections.append(f"\n\n### 💡 Senior PM Perspective\n{senior_perspective}")
                                
                                evaluation_text = "".join(eval_sections)
                                
                                st.session_state.messages_by_topic[topic_key].append({
                                    "role": "assistant",
                                    "content": evaluation_text
                                })
                                
                                st.session_state.last_score = score
                                
                                # Build framework text for retry
                                if isinstance(framework, dict) and framework:
                                    fw_name = framework.get("name", "Framework")
                                    fw_steps = framework.get("steps", [])
                                    fw_text = f"**{fw_name}**\n\n" + "\n".join([f"{i+1}. {s}" for i, s in enumerate(fw_steps)]) if fw_steps else f"**{fw_name}**"
                                else:
                                    fw_text = "Review the feedback above"
                                st.session_state.last_framework = fw_text
                                
                                st.session_state.retry_question_id = st.session_state.current_question_id
                                
                                # Store answer with ACTUAL question text
                                st.session_state.topic_answers[topic_key].append({
                                    "question_id": st.session_state.current_question_id,
                                    "question_number": current_q_num,
                                    "question_text": question_text,  # Now properly stored
                                    "answer": user_input,
                                    "score": score,
                                    "rating": rating,
                                    "strong_points": strong_points,
                                    "missing_points": missing_points,
                                    "weak_areas": weak_areas,
                                    "how_to_answer": how_to_answer,
                                    "framework": framework,
                                    "senior_pm_answer": senior_perspective
                                })
                                
                                # Remove from skipped if applicable
                                if st.session_state.current_question_number:
                                    skipped_list = st.session_state.topic_skipped_questions[topic_key]
                                    for i, sq in enumerate(skipped_list):
                                        if sq["question_id"] == st.session_state.current_question_id:
                                            skipped_list.pop(i)
                                            st.session_state.topic_skipped[topic_key] -= 1
                                            break
                                
                                st.session_state.current_question_id = None
                                st.session_state.current_question_number = None
                                st.session_state.current_question_text = None
                                st.session_state.awaiting_answer = False
                                st.session_state.show_retry_buttons = True
                                st.rerun()
        
        # Retry/Next buttons
        if st.session_state.show_retry_buttons and st.session_state.last_score is not None:
            st.markdown("---")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.session_state.last_score < 4:
                    if st.button("🔄 Practice With Framework", use_container_width=True):
                        st.session_state.messages_by_topic[topic_key].append({
                            "role": "assistant",
                            "content": f"""### 🔄 Practice Mode

Here's the framework to guide your answer:

{st.session_state.last_framework}

**Try answering again using this framework.**

*This is practice only - your official score ({st.session_state.last_score}/5) is already recorded.*"""
                        })
                        st.session_state.retry_mode = True
                        st.session_state.awaiting_answer = True
                        st.session_state.show_retry_buttons = False
                        st.rerun()
            
            with col2:
                if st.button("✓ Next Question", use_container_width=True, type="primary"):
                    st.session_state.show_retry_buttons = False
                    st.session_state.last_score = None
                    st.session_state.last_framework = None
                    st.session_state.current_question_id = None
                    st.session_state.current_question_number = None
                    st.session_state.current_question_text = None
                    st.session_state.awaiting_answer = False
                    st.session_state.retry_mode = False
                    st.session_state.retry_question_id = None
                    
                    current_attempted = st.session_state.topic_attempted[topic_key]
                    
                    if current_attempted < QUESTIONS_PER_TOPIC:
                        with st.spinner("Generating next question..."):
                            result = get_pm_question({"level": "intermediate", "topic": topic_key})
                            question_text = result.get("question", "Error")
                            question_id = result.get("id")
                            
                            st.session_state.topic_attempted[topic_key] += 1
                            next_question_num = st.session_state.topic_attempted[topic_key]
                            
                            st.session_state.current_question_id = question_id
                            st.session_state.current_question_number = next_question_num
                            st.session_state.current_question_text = question_text  # Store question
                            st.session_state.awaiting_answer = True
                            
                            st.session_state.messages_by_topic[topic_key] = [{
                                "role": "assistant",
                                "content": f"**Question {next_question_num}/15:**\n\n{question_text}\n\n*Take your time and provide a thoughtful answer.*"
                            }]
                    
                    st.rerun()
        
        else:
            # Auto-load next question
            if answered < QUESTIONS_PER_TOPIC and st.session_state.current_question_id is None and not st.session_state.retry_mode:
                with st.spinner("Loading question..."):
                    result = get_pm_question({"level": "intermediate", "topic": topic_key})
                    question_text = result.get("question", "Error")
                    question_id = result.get("id")
                    
                    st.session_state.topic_attempted[topic_key] += 1
                    current_question_num = st.session_state.topic_attempted[topic_key]
                    
                    st.session_state.current_question_id = question_id
                    st.session_state.current_question_number = current_question_num
                    st.session_state.current_question_text = question_text  # Store question text
                    st.session_state.awaiting_answer = True
                    
                    st.session_state.messages_by_topic[topic_key].append({
                        "role": "assistant",
                        "content": f"**Question {current_question_num}/15:**\n\n{question_text}\n\n*Take your time and provide a thoughtful answer.*"
                    })
                    st.rerun()

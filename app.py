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
    with st.expander("ℹ️ How it works", expanded=False):
        st.markdown("""
        1. **Enter your OpenAI API key** (one-time setup)
        2. **Choose a mode**: Structured Practice or Chat Mode
        3. **Answer questions** and get AI feedback
        4. **Track progress** across all topics
        """)

# API Key Input - Make it prominent
st.markdown("---")
col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    api_key = st.text_input(
        "🔑 Enter your OpenAI API Key",
        type="password",
        key="api_key_input",
        help="Get your key at https://platform.openai.com/api-keys (free $5 credit to start)"
    )

with col2:
    st.markdown("**Don't have an API key?**")
    st.markdown("[Get free OpenAI API key →](https://platform.openai.com/api-keys)")

with col3:
    st.write("")  # Spacing

api_key_value = st.session_state.get("api_key_input", "")

if not api_key_value:
    st.warning("⚠️ Please enter your OpenAI API key above to begin. Your key is never stored or shared.")
    st.stop()

if "tools_initialized" not in st.session_state:
    set_openai_client(api_key_value)
    st.session_state.tools_initialized = True
    st.success("✅ API Connected! Ready to practice!")

# Extended topic definitions
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
    else:  # 1 or 2
        return "🔴", "#DD0000"

# Initialize session state - SEPARATE MESSAGES PER TOPIC
if "messages_by_topic" not in st.session_state:
    st.session_state.messages_by_topic = {topic: [] for topic in TOPICS.keys()}

if "current_topic" not in st.session_state:
    st.session_state.current_topic = None

if "current_question_id" not in st.session_state:
    st.session_state.current_question_id = None

if "awaiting_answer" not in st.session_state:
    st.session_state.awaiting_answer = False

# Initialize topic progress tracking
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

if "retry_question_id" not in st.session_state:
    st.session_state.retry_question_id = None

if "retry_framework" not in st.session_state:
    st.session_state.retry_framework = None

if "show_retry_buttons" not in st.session_state:
    st.session_state.show_retry_buttons = False

if "last_score" not in st.session_state:
    st.session_state.last_score = None

if "last_framework" not in st.session_state:
    st.session_state.last_framework = None

# NEW: Track which answered question is being reviewed
if "reviewing_answer_idx" not in st.session_state:
    st.session_state.reviewing_answer_idx = None

# NEW: Track current question number for proper display
if "current_question_number" not in st.session_state:
    st.session_state.current_question_number = None

# NEW: Chat mode state
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

if "react_agent" not in st.session_state:
    st.session_state.react_agent = None

# NEW: App mode - "structured" or "chat"
if "app_mode" not in st.session_state:
    st.session_state.app_mode = "structured"

# ============================================
# MODE SELECTION - TABS AT THE TOP
# ============================================
st.markdown("---")
mode_col1, mode_col2, mode_col3 = st.columns([1, 1, 2])

with mode_col1:
    if st.button("📋 Structured Practice", use_container_width=True, 
                 type="primary" if st.session_state.app_mode == "structured" else "secondary"):
        st.session_state.app_mode = "structured"
        st.rerun()

with mode_col2:
    if st.button("💬 Chat Mode (ReAct)", use_container_width=True,
                 type="primary" if st.session_state.app_mode == "chat" else "secondary"):
        st.session_state.app_mode = "chat"
        # Initialize ReAct agent if not already done
        if st.session_state.react_agent is None:
            from scratch_agent.pm_bot import get_pm_bot
            st.session_state.react_agent = get_pm_bot(api_key_value)
        st.rerun()

with mode_col3:
    if st.session_state.app_mode == "structured":
        st.info("**Structured Mode**: Guided practice with progress tracking")
    else:
        st.info("**Chat Mode**: Natural conversation powered by ReAct agent")

st.markdown("---")

# ============================================
# CHAT MODE (ReAct Agent)
# ============================================
if st.session_state.app_mode == "chat":
    st.header("💬 Chat Mode - ReAct Agent")
    st.caption("Have a natural conversation with your AI interview coach. Ask for questions, get feedback, and discuss topics freely.")
    
    # Show architecture info
    with st.expander("🔍 How ReAct Chat Mode Works", expanded=False):
        st.markdown("""
        **ReAct (Reasoning + Acting) Pattern:**
        
        Unlike Structured Mode where the app controls the flow, Chat Mode uses an autonomous agent that:
        
        1. **Reasons** about your message to understand intent
        2. **Decides** which tool to use (or none)
        3. **Acts** by calling the appropriate tool
        4. **Observes** the result and reasons again
        5. **Responds** with a natural answer
        
        **Available Tools:**
        - `get_pm_question` - Generate interview questions
        - `evaluate_pm_answer` - Evaluate your answers
        
        **Try saying:**
        - "Give me a hard RAG architecture question"
        - "I want to practice AI strategy"
        - "What topics can I practice?"
        - After answering: "How could I improve that answer?"
        """)
    
    # Display chat history
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask for a question, submit an answer, or chat about PM topics..."):
        # Add user message to history
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get agent response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = st.session_state.react_agent.run(prompt)
                    st.markdown(response)
                    st.session_state.chat_messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.chat_messages.append({"role": "assistant", "content": error_msg})
    
    # Clear chat button
    st.markdown("---")
    if st.button("🗑️ Clear Chat History"):
        st.session_state.chat_messages = []
        # Reinitialize agent to clear its context
        from scratch_agent.pm_bot import get_pm_bot
        st.session_state.react_agent = get_pm_bot(api_key_value)
        st.rerun()
    
    # Quick action buttons
    st.markdown("### Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🎯 AI Strategy Question", use_container_width=True):
            prompt = "Give me an AI strategy interview question"
            st.session_state.chat_messages.append({"role": "user", "content": prompt})
            with st.spinner("Generating question..."):
                response = st.session_state.react_agent.run(prompt)
                st.session_state.chat_messages.append({"role": "assistant", "content": response})
            st.rerun()
    
    with col2:
        if st.button("🏗️ RAG Architecture Question", use_container_width=True):
            prompt = "Give me a RAG architecture interview question"
            st.session_state.chat_messages.append({"role": "user", "content": prompt})
            with st.spinner("Generating question..."):
                response = st.session_state.react_agent.run(prompt)
                st.session_state.chat_messages.append({"role": "assistant", "content": response})
            st.rerun()
    
    with col3:
        if st.button("📊 Evaluation & Metrics Question", use_container_width=True):
            prompt = "Give me an evaluation and metrics interview question"
            st.session_state.chat_messages.append({"role": "user", "content": prompt})
            with st.spinner("Generating question..."):
                response = st.session_state.react_agent.run(prompt)
                st.session_state.chat_messages.append({"role": "assistant", "content": response})
            st.rerun()

# ============================================
# STRUCTURED MODE (Original App)
# ============================================
else:
    # SIDEBAR MENU
    st.sidebar.header("📚 Topics")

    for topic_key, topic_label in TOPICS.items():
        answered = len(st.session_state.topic_answers[topic_key])
        attempted = st.session_state.topic_attempted[topic_key]
        skipped = st.session_state.topic_skipped[topic_key]
        
        # Show progress with button - always allow switching topics
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
            st.session_state.reviewing_answer_idx = None
            st.session_state.current_question_number = None
            st.rerun()
        
        # Show progress bar and attempted count
        st.sidebar.progress(answered / QUESTIONS_PER_TOPIC, text=f"{answered}/{QUESTIONS_PER_TOPIC}")
        if attempted > 0:
            st.sidebar.caption(f"✅ {answered} answered | ⏭️ {skipped} skipped")

    st.sidebar.markdown("---")
    if st.sidebar.button("🏠 Home", use_container_width=True):
        st.session_state.current_topic = None
        st.session_state.awaiting_answer = False
        st.session_state.reviewing_answer_idx = None
        st.rerun()

    # MAIN CONTENT
    if st.session_state.current_topic is None:
        # Home page
        st.markdown("""
        ## Welcome to Your AI PM Interview Coach! 🎓
        
        This coach helps you master AI Product Management by asking **15 realistic interview questions for each topic**.
        
        ### How it works:
        1. **Select a topic** from the left sidebar
        2. **Answer interview questions** (15 per topic)
        3. **Get detailed feedback** with scores, frameworks, and senior PM insights
        4. **Track your progress** with color-coded scores
        
        ### Topics to Master:
        • **AI Strategy & Vision** - Building AI products, market fit, competitive positioning
        • **RAG & Architecture** - System design, orchestration, agentic patterns
        • **Evaluation & Metrics** - Performance, user satisfaction, success metrics
        • **Design Patterns** - Prompt engineering, reasoning loops, human-in-the-loop
        • **Privacy & Governance** - Compliance, security, data handling
        • **Product Execution** - Roadmapping, stakeholder management, tradeoffs
        • **AI Agents & Orchestration** - Multi-agent systems, agent design patterns
        • **ML Ops & Infrastructure** - Model deployment, monitoring, scaling
        • **User Experience & UX** - AI product design, user interaction patterns
        • **Pricing & Monetization** - AI business models, pricing strategies
        • **AI Safety & Ethics** - Responsible AI, bias, fairness, alignment
        • **Competitive Analysis** - Market positioning, competitor analysis
        
        ### Your Progress:
        """)
        
        # Show overall progress
        total_answered = sum(len(answers) for answers in st.session_state.topic_answers.values())
        total_questions = len(TOPICS) * QUESTIONS_PER_TOPIC
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Questions Answered", total_answered)
        with col2:
            st.metric("Total Questions", total_questions)
        with col3:
            st.metric("Completion %", f"{int((total_answered/total_questions)*100)}%")
        with col4:
            st.metric("Topics Completed", sum(1 for t in TOPICS.keys() if len(st.session_state.topic_answers[t]) >= QUESTIONS_PER_TOPIC))
        
        # Analytics Dashboard
        st.subheader("📈 Analytics Dashboard")
        
        # Calculate statistics
        all_answers = []
        topic_stats = {}
        
        for topic_key, topic_label in TOPICS.items():
            answers = st.session_state.topic_answers[topic_key]
            all_answers.extend(answers)
            
            if answers:
                scores = [a.get("score", 0) for a in answers]
                avg_score = sum(scores) / len(scores)
                excellent = sum(1 for s in scores if s >= 4)
                good = sum(1 for s in scores if s == 3)
                needs_work = sum(1 for s in scores if s <= 2)
                
                topic_stats[topic_label] = {
                    "avg": avg_score,
                    "excellent": excellent,
                    "good": good,
                    "needs_work": needs_work,
                    "total": len(answers)
                }
        
        # Top metrics row
        if all_answers:
            col1, col2, col3, col4, col5 = st.columns(5)
            
            all_scores = [a.get("score", 0) for a in all_answers]
            avg_overall = sum(all_scores) / len(all_scores)
            
            with col1:
                st.metric("Overall Average Score", f"{avg_overall:.2f}/5")
            with col2:
                excellent_count = sum(1 for s in all_scores if s >= 4)
                st.metric("Excellent Answers", excellent_count)
            with col3:
                good_count = sum(1 for s in all_scores if s == 3)
                st.metric("Average Answers", good_count)
            with col4:
                needs_work_count = sum(1 for s in all_scores if s <= 2)
                st.metric("Needs Work", needs_work_count)
            with col5:
                st.metric("Success Rate", f"{int((excellent_count/len(all_scores))*100)}%")
            
            st.markdown("---")
            
            # Topic Performance Heatmap
            st.subheader("Topic Performance Heatmap")
            
            # Create two columns for better layout
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Bar chart - Average score by topic
                topic_names = []
                topic_avgs = []
                topic_colors = []
                
                for topic_label in TOPICS.values():
                    if topic_label in topic_stats:
                        stats = topic_stats[topic_label]
                        topic_names.append(topic_label)
                        topic_avgs.append(stats["avg"])
                        
                        # Color based on score
                        if stats["avg"] >= 4:
                            topic_colors.append("🟢")
                        elif stats["avg"] >= 3:
                            topic_colors.append("🟡")
                        else:
                            topic_colors.append("🔴")
                
                if topic_names:
                    df = pd.DataFrame({
                        "Topic": topic_names,
                        "Average Score": topic_avgs,
                        "Performance": topic_colors
                    })
                    
                    # Sort by average score
                    df = df.sort_values("Average Score", ascending=True)
                    
                    st.bar_chart(df.set_index("Topic")["Average Score"], height=400)
                    
                    st.dataframe(df, use_container_width=True, hide_index=True)
            
            with col2:
                st.write("**Score Distribution**")
                
                if all_scores:
                    score_dist = {
                        "5 - Outstanding": sum(1 for s in all_scores if s == 5),
                        "4 - Excellent": sum(1 for s in all_scores if s == 4),
                        "3 - Average": sum(1 for s in all_scores if s == 3),
                        "2 - Below Avg": sum(1 for s in all_scores if s == 2),
                        "1 - Poor": sum(1 for s in all_scores if s == 1),
                    }
                    
                    for label, count in score_dist.items():
                        if count > 0:
                            st.write(f"{label}: **{count}** answers")
            
            st.markdown("---")
            
            # Topics needing focus
            st.subheader("🎯 Recommended Focus Areas")
            
            # Find weakest topics
            weak_topics = []
            for topic_label, stats in topic_stats.items():
                if stats["avg"] < 3:  # Score below average
                    weak_topics.append((topic_label, stats["avg"], stats["needs_work"]))
            
            weak_topics.sort(key=lambda x: x[1])  # Sort by score
            
            if weak_topics:
                st.warning("**Topics to Focus On:**")
                for topic, avg_score, needs_work in weak_topics[:3]:
                    st.write(f"• **{topic}** - Average: {avg_score:.1f}/5 ({needs_work} answers need improvement)")
            else:
                st.success("**Great job!** All your topics are performing well! 🎉")
            
            st.markdown("---")
            
            # Progress over time (simple)
            st.subheader("📊 Progress Tracking")
            
            # Show questions answered per topic
            cols = st.columns(2)
            col_idx = 0
            
            for topic_key, topic_label in TOPICS.items():
                answered = len(st.session_state.topic_answers[topic_key])
                with cols[col_idx % 2]:
                    st.write(f"**{topic_label}**")
                    st.progress(answered / QUESTIONS_PER_TOPIC)
                    
                    # Show answered questions with scores
                    if answered > 0:
                        answers = st.session_state.topic_answers[topic_key]
                        scores = [a.get("score", 0) for a in answers]
                        avg = sum(scores) / len(scores)
                        
                        score_display = ""
                        for i, ans in enumerate(answers, 1):
                            score = ans.get("score", "N/A")
                            emoji, _ = get_score_color(score)
                            score_display += f"{emoji}"
                        
                        st.write(f"Scores: {score_display}")
                        st.write(f"Average: {avg:.1f}/5 | Answered: {answered}/{QUESTIONS_PER_TOPIC}")
                
                col_idx += 1
        
        else:
            st.info("📝 Start answering questions to see your analytics dashboard!")

    else:
        # Topic page
        topic_key = st.session_state.current_topic
        topic_label = TOPICS[topic_key]
        answered = len(st.session_state.topic_answers[topic_key])
        
        # Get messages for this topic
        messages = st.session_state.messages_by_topic[topic_key]
        
        # Header with progress
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        with col1:
            st.header(topic_label)
        with col2:
            st.metric("✅ Answered", f"{answered}")
        with col3:
            skipped = st.session_state.topic_skipped[topic_key]
            st.metric("⏭️ Skipped", f"{skipped}")
        with col4:
            attempted = st.session_state.topic_attempted[topic_key]
            st.metric("📊 Attempted", f"{attempted}/15")
        
        # Progress bar for answered questions
        st.progress(answered / QUESTIONS_PER_TOPIC, text=f"Answered: {answered}/15 | Skipped: {skipped}/15")
        
        # Show answered questions with scores - NOW CLICKABLE WITH CORRECT QUESTION NUMBERS
        if answered > 0:
            st.subheader("Your Answers (click to review):")
            answers = st.session_state.topic_answers[topic_key]
            
            # Display in a responsive grid (5 items per row)
            cols_per_row = 5
            rows = (len(answers) + cols_per_row - 1) // cols_per_row
            
            for row in range(rows):
                cols = st.columns(cols_per_row, gap="small")
                for col_idx in range(cols_per_row):
                    answer_idx = row * cols_per_row + col_idx
                    if answer_idx < len(answers):
                        ans = answers[answer_idx]
                        score = ans.get("score", "N/A")
                        emoji, color = get_score_color(score)
                        
                        # Use stored question_number instead of answer_idx
                        question_num = ans.get("question_number", answer_idx + 1)
                        
                        with cols[col_idx]:
                            # Make it a clickable button
                            is_selected = st.session_state.reviewing_answer_idx == answer_idx
                            button_label = f"{emoji} Q{question_num}\nScore: {score}/5"
                            
                            if st.button(
                                button_label,
                                key=f"review_q_{answer_idx}",
                                use_container_width=True,
                                type="primary" if is_selected else "secondary"
                            ):
                                if st.session_state.reviewing_answer_idx == answer_idx:
                                    # Click again to close
                                    st.session_state.reviewing_answer_idx = None
                                else:
                                    st.session_state.reviewing_answer_idx = answer_idx
                                st.rerun()
            
            # Show review panel if an answer is selected
            if st.session_state.reviewing_answer_idx is not None:
                idx = st.session_state.reviewing_answer_idx
                if idx < len(answers):
                    ans = answers[idx]
                    score = ans.get("score", "N/A")
                    emoji, color = get_score_color(score)
                    question_num = ans.get("question_number", idx + 1)
                    
                    st.markdown("---")
                    st.subheader(f"📋 Review: Question {question_num}")
                    
                    # Close button
                    if st.button("✕ Close Review", key="close_review"):
                        st.session_state.reviewing_answer_idx = None
                        st.rerun()
                    
                    # Question
                    st.markdown("### 📝 Question")
                    st.info(ans.get("question_text", "Question not stored"))
                    
                    # Your answer
                    st.markdown("### 💬 Your Answer")
                    st.warning(ans.get("answer", "Answer not stored"))
                    
                    # Evaluation
                    st.markdown(f"### {emoji} Evaluation: {score}/5 ({ans.get('rating', '')})")
                    
                    # Strong points
                    strong_points = ans.get("strong_points", [])
                    if strong_points:
                        st.markdown("**✅ Strong Points:**")
                        for point in strong_points:
                            st.write(f"• {point}")
                    
                    # Missing points
                    missing_points = ans.get("missing_points", [])
                    if missing_points:
                        st.markdown("**❌ Missing Points:**")
                        for point in missing_points:
                            st.write(f"• {point}")
                    
                    # Weak areas
                    weak_areas = ans.get("weak_areas", [])
                    if weak_areas:
                        st.markdown("**⚠️ Areas to Develop:**")
                        for area in weak_areas:
                            st.write(f"• {area}")
                    
                    # Framework
                    framework = ans.get("framework", {})
                    if framework and isinstance(framework, dict):
                        st.markdown("**🎯 Framework to Remember:**")
                        fw_name = framework.get("name", "")
                        fw_acronym = framework.get("acronym", "")
                        fw_steps = framework.get("steps", [])
                        
                        if fw_name:
                            st.write(f"**{fw_name}** ({fw_acronym})")
                        for i, step in enumerate(fw_steps, 1):
                            st.write(f"{i}. {step}")
                    
                    # Senior PM answer
                    senior_answer = ans.get("senior_pm_answer", "")
                    if senior_answer:
                        st.markdown("**💡 Senior PM Perspective:**")
                        st.write(senior_answer)
                    
                    st.markdown("---")
            
            st.markdown("---")
        
        # Show skipped questions section if any exist
        skipped_questions = st.session_state.topic_skipped_questions[topic_key]
        if skipped_questions:
            st.markdown("---")
            st.subheader(f"⏭️ Skipped Questions ({len(skipped_questions)})")
            
            # Add button to review skipped questions
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("📋 Review Skipped", use_container_width=True, key="review_skipped_btn"):
                    st.session_state.reviewing_skipped = True
                    st.rerun()
            with col2:
                st.write(f"**{len(skipped_questions)} question{'s' if len(skipped_questions) > 1 else ''} waiting to be attempted**")
            
            # If in review mode, show interactive list
            if st.session_state.reviewing_skipped:
                st.info("📝 **Reviewing Skipped Questions** - Click 'Attempt' to answer a skipped question")
                
                for i, skipped_q in enumerate(skipped_questions):
                    with st.container():
                        st.markdown(f"### Question {skipped_q['attempt_number']} (Skipped)")
                        st.markdown(skipped_q["question_text"])
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button(f"✅ Attempt Question {skipped_q['attempt_number']}", key=f"attempt_skipped_{i}", use_container_width=True):
                                # Load this skipped question for answering
                                st.session_state.current_question_id = skipped_q["question_id"]
                                st.session_state.current_question_number = skipped_q["attempt_number"]
                                st.session_state.awaiting_answer = True
                                st.session_state.reviewing_skipped = False
                                
                                # Clear all messages and add only this question
                                st.session_state.messages_by_topic[topic_key] = [
                                    {
                                        "role": "assistant",
                                        "content": f"**Question {skipped_q['attempt_number']}/15:**\n\n{skipped_q['question_text']}\n\n*Take your time and provide a thoughtful answer.*"
                                    }
                                ]
                                
                                st.rerun()
                        
                        with col2:
                            if st.button(f"🗑️ Remove Q{skipped_q['attempt_number']}", key=f"remove_skipped_{i}", use_container_width=True):
                                # Remove from skipped list
                                st.session_state.topic_skipped_questions[topic_key].pop(i)
                                st.session_state.topic_skipped[topic_key] -= 1
                                st.rerun()
                        
                        st.markdown("---")
            else:
                # Show collapsed list
                for i, skipped_q in enumerate(skipped_questions):
                    with st.expander(f"Question {skipped_q['attempt_number']} (Skipped)", expanded=False):
                        st.markdown(skipped_q["question_text"])
        
        if answered >= QUESTIONS_PER_TOPIC:
            st.success("🎉 You've completed all 15 questions for this topic!")
            
            # Show summary stats
            col1, col2, col3 = st.columns(3)
            answers = st.session_state.topic_answers[topic_key]
            avg_score = sum(a.get("score", 0) for a in answers) / len(answers) if answers else 0
            
            with col1:
                st.metric("Average Score", f"{avg_score:.1f}/5")
            with col2:
                excellent = sum(1 for a in answers if a.get("score", 0) >= 4)
                st.metric("Excellent Answers (4-5)", excellent)
            with col3:
                needs_work = sum(1 for a in answers if a.get("score", 0) <= 2)
                st.metric("Needs Work (1-2)", needs_work)
            
            if st.button("← Back to Topics"):
                st.session_state.current_topic = None
                st.rerun()
        else:
            # Show chat history for THIS TOPIC ONLY - show last 2 messages (question + evaluation/answer)
            messages_to_show = messages[-4:] if len(messages) > 4 else messages  # Show last 4 messages max
            for msg in messages_to_show:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
            
            # Question handling
            if st.session_state.awaiting_answer:
                # Get answer from user (including retries)
                st.markdown("---")
                
                # Check if input should be disabled
                input_disabled = st.session_state.show_retry_buttons
                
                if not input_disabled:
                    # Show text area for answer
                    st.markdown("**Your Answer:**")
                    user_input = st.text_area(
                        "Type your answer here...",
                        key="answer_text_area",
                        height=150,
                        label_visibility="collapsed",
                        placeholder="Type your answer here... (Aim for 100+ words for a comprehensive response)"
                    )
                    
                    # Show Skip and Submit buttons side by side
                    col_skip, col_submit = st.columns([1, 2])
                    
                    with col_skip:
                        if st.button("⏭️ Skip", use_container_width=True, key="skip_btn"):
                            # The current question number is already in topic_attempted
                            skipped_question_num = st.session_state.topic_attempted[topic_key]
                            current_question_id = st.session_state.current_question_id
                            
                            # Extract JUST the question text (without "Question X/15:" prefix)
                            skipped_q_text = ""
                            if messages and messages[-1]["role"] == "assistant" and "Question" in messages[-1]["content"]:
                                full_text = messages[-1]["content"]
                                # Extract just the question part after "Question X/15:"
                                if ":" in full_text:
                                    parts = full_text.split(":", 1)
                                    if len(parts) > 1:
                                        skipped_q_text = parts[1].strip()
                                        skipped_q_text = skipped_q_text.replace("**", "").replace("*Take your time*", "").replace("*take your time*", "").strip()
                                else:
                                    skipped_q_text = full_text
                            
                            # Store the skipped question
                            st.session_state.topic_skipped_questions[topic_key].append({
                                "question_id": current_question_id,
                                "question_text": skipped_q_text,
                                "attempt_number": skipped_question_num
                            })
                            
                            # Reset UI state
                            st.session_state.show_retry_buttons = False
                            st.session_state.current_question_id = None
                            st.session_state.current_question_number = None
                            st.session_state.awaiting_answer = False
                            st.session_state.retry_mode = False
                            
                            # Remove the question from chat
                            if messages and messages[-1]["role"] == "assistant" and "Question" in messages[-1]["content"]:
                                st.session_state.messages_by_topic[topic_key].pop()
                            
                            # Increment skipped counter
                            st.session_state.topic_skipped[topic_key] += 1
                            
                            st.rerun()
                    
                    with col_submit:
                        submit_disabled = not user_input or len(user_input.strip()) == 0
                        if st.button("📤 Submit Answer", use_container_width=True, key="submit_btn", disabled=submit_disabled, type="primary"):
                            # Add to THIS TOPIC's messages
                            st.session_state.messages_by_topic[topic_key].append({"role": "user", "content": user_input})
                            
                            # Extract question text for storage
                            question_text = ""
                            if messages and messages[-1]["role"] == "assistant" and "Question" in messages[-1]["content"]:
                                full_text = messages[-1]["content"]
                                if ":" in full_text:
                                    parts = full_text.split(":", 1)
                                    if len(parts) > 1:
                                        question_text = parts[1].strip()
                                        question_text = question_text.replace("**", "").replace("*Take your time and provide a thoughtful answer.*", "").strip()
                            
                            # Get the current question number (use stored value or topic_attempted)
                            current_q_num = st.session_state.current_question_number or st.session_state.topic_attempted[topic_key]
                            
                            with st.spinner("Evaluating your answer..."):
                                eval_result = evaluate_pm_answer({
                                    "id": st.session_state.current_question_id,
                                    "answer": user_input
                                })
                                
                                # Extract evaluation
                                score = eval_result.get("score", "N/A")
                                rating = eval_result.get("rating_label", "")
                                
                                strong_points = eval_result.get("strong_points", [])
                                if strong_points and len(strong_points) > 0:
                                    strong_text = "\n".join([f"• {point}" for point in strong_points])
                                else:
                                    strong_text = "• You demonstrated honesty by acknowledging what you don't know"
                                
                                missing_points = eval_result.get("missing_points", [])
                                missing_text = "\n".join([f"• {point}" for point in missing_points]) if missing_points else "• Consider additional perspectives"
                                
                                weak_areas = eval_result.get("weak_areas", [])
                                weak_text = "\n".join([f"• {area}" for area in weak_areas]) if weak_areas else "• Continue developing your framework"
                                
                                framework = eval_result.get("framework", {})
                                if isinstance(framework, dict) and framework:
                                    fw_name = framework.get("name", "Framework")
                                    fw_acronym = framework.get("acronym", "")
                                    fw_steps = framework.get("steps", [])
                                    
                                    if fw_steps:
                                        fw_text = f"**{fw_name}** ({fw_acronym})\n\n" + "\n".join([f"{i+1}. {step}" for i, step in enumerate(fw_steps)])
                                    else:
                                        fw_text = f"**{fw_name}**"
                                else:
                                    fw_text = "Continue developing your PM framework"
                                
                                senior_perspective = eval_result.get("senior_pm_answer", "")
                                if not senior_perspective:
                                    senior_perspective = "A senior PM would take a holistic view considering business impact, technical feasibility, and user needs."
                                
                                # Get emoji and color for this score
                                emoji, _ = get_score_color(score)
                                
                                # Check if this is a retry
                                is_retry = st.session_state.retry_mode
                                
                                if is_retry:
                                    evaluation_text = f"""## 📊 Your Retry Evaluation {emoji}

### Score: **{score}/5** {f"({rating})" if rating else ""}

### ✅ Strong Points
{strong_text}

### ❌ Missing Points
{missing_text}

### ⚠️ Areas to Develop
{weak_text}

### 💡 Senior PM Perspective
{senior_perspective}

---

**How did you do?** Using the framework should have helped you cover more ground! 🎯"""
                                else:
                                    evaluation_text = f"""## 📊 Evaluation {emoji}

### Score: **{score}/5** {f"({rating})" if rating else ""}

### ✅ Strong Points
{strong_text}

### ❌ Missing Points
{missing_text}

### ⚠️ Areas to Develop
{weak_text}

### 🎯 Framework to Remember
{fw_text}

### 💡 Senior PM Perspective
{senior_perspective}"""
                                
                                # Add to THIS TOPIC's messages
                                st.session_state.messages_by_topic[topic_key].append({
                                    "role": "assistant",
                                    "content": evaluation_text
                                })
                                
                                # Store for button display
                                st.session_state.last_score = score
                                st.session_state.last_framework = fw_text
                                
                                # Only add to answers list if NOT a retry
                                if not is_retry:
                                    # Store FULL evaluation data for review WITH CORRECT QUESTION NUMBER
                                    st.session_state.topic_answers[topic_key].append({
                                        "question_id": st.session_state.current_question_id,
                                        "question_number": current_q_num,  # Store the actual question number
                                        "question_text": question_text,
                                        "answer": user_input,
                                        "score": score,
                                        "rating": rating,
                                        "strong_points": strong_points,
                                        "missing_points": missing_points,
                                        "weak_areas": weak_areas,
                                        "framework": framework,
                                        "senior_pm_answer": senior_perspective
                                    })
                                    
                                    # If this was a skipped question being answered, remove it from skipped list
                                    if st.session_state.current_question_number:
                                        skipped_list = st.session_state.topic_skipped_questions[topic_key]
                                        for i, sq in enumerate(skipped_list):
                                            if sq["question_id"] == st.session_state.current_question_id:
                                                skipped_list.pop(i)
                                                st.session_state.topic_skipped[topic_key] -= 1
                                                break
                                else:
                                    # For retries, add a note about the improvement
                                    st.session_state.messages_by_topic[topic_key].append({
                                        "role": "assistant",
                                        "content": f"*This was a practice retry. Your official score remains from your first attempt. Keep practicing! 💪*"
                                    })
                                    st.session_state.retry_mode = False
                                
                                st.session_state.current_question_id = None
                                st.session_state.current_question_number = None
                                st.session_state.awaiting_answer = False
                                st.session_state.show_retry_buttons = True
                                st.rerun()
                else:
                    # Input is disabled - show disabled text area
                    st.markdown("**Your Answer:**")
                    st.text_area(
                        "Answer submitted",
                        value="Answer submitted - see evaluation below",
                        key="answer_text_area_disabled",
                        height=100,
                        disabled=True,
                        label_visibility="collapsed"
                    )
            
            # Show buttons AFTER evaluation is displayed
            if st.session_state.show_retry_buttons and st.session_state.last_score is not None:
                st.markdown("---")
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.session_state.last_score < 4:
                        if st.button("🔄 Try Again With Framework", use_container_width=True):
                            # Add retry message to chat
                            st.session_state.messages_by_topic[topic_key].append({
                                "role": "assistant",
                                "content": f"""Great! Here's the framework to guide your answer:

{st.session_state.last_framework}

**Try answering the same question again, this time using the steps in the framework above:**

*Remember: This is a practice attempt. Your official score won't change, but you'll learn how to structure better answers!*"""
                            })
                            
                            st.session_state.retry_mode = True
                            st.session_state.awaiting_answer = True
                            st.session_state.show_retry_buttons = False
                            st.rerun()
                    else:
                        st.write("")  # Empty space for alignment
                
                with col2:
                    if st.button("✓ Move to Next Question", use_container_width=True):
                        # Reset state and automatically get next question
                        st.session_state.show_retry_buttons = False
                        st.session_state.last_score = None
                        st.session_state.last_framework = None
                        st.session_state.current_question_id = None
                        st.session_state.current_question_number = None
                        st.session_state.awaiting_answer = False
                        st.session_state.retry_mode = False
                        
                        # Get current attempted count BEFORE incrementing
                        current_attempted = st.session_state.topic_attempted[topic_key]
                        
                        # Check if there are more questions
                        if current_attempted < QUESTIONS_PER_TOPIC:
                            # Remove last 4 messages (question, answer, evaluation, notes) to show only new question
                            while len(st.session_state.messages_by_topic[topic_key]) > 0 and len(st.session_state.messages_by_topic[topic_key]) % 4 != 0:
                                st.session_state.messages_by_topic[topic_key].pop()
                            
                            # Automatically load next question
                            with st.spinner("Generating next question..."):
                                result = get_pm_question({"level": "intermediate", "topic": topic_key})
                                question_text = result.get("question", "Error")
                                question_id = result.get("id")
                                
                                # INCREMENT AFTER we know we're loading the next question
                                st.session_state.topic_attempted[topic_key] += 1
                                next_question_num = st.session_state.topic_attempted[topic_key]
                                
                                st.session_state.current_question_id = question_id
                                st.session_state.current_question_number = next_question_num
                                st.session_state.awaiting_answer = True
                                
                                # Add to THIS TOPIC's messages
                                st.session_state.messages_by_topic[topic_key].append({
                                    "role": "assistant",
                                    "content": f"**Question {next_question_num}/15:**\n\n{question_text}\n\n*Take your time and provide a thoughtful answer.*"
                                })
                        
                        st.rerun()
            
            else:
                # Not awaiting answer - auto-load next question
                if answered < QUESTIONS_PER_TOPIC and st.session_state.current_question_id is None:
                    # Auto-load the next question
                    with st.spinner("Loading question..."):
                        result = get_pm_question({"level": "intermediate", "topic": topic_key})
                        question_text = result.get("question", "Error")
                        question_id = result.get("id")
                        
                        # Increment attempt counter FIRST to get current question number
                        st.session_state.topic_attempted[topic_key] += 1
                        current_question_num = st.session_state.topic_attempted[topic_key]
                        
                        st.session_state.current_question_id = question_id
                        st.session_state.current_question_number = current_question_num
                        st.session_state.awaiting_answer = True
                        
                        # Add to THIS TOPIC's messages
                        st.session_state.messages_by_topic[topic_key].append({
                            "role": "assistant",
                            "content": f"**Question {current_question_num}/15:**\n\n{question_text}\n\n*Take your time and provide a thoughtful answer.*"
                        })
                        st.rerun()

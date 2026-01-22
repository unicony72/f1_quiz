import streamlit as st
import google.generativeai as genai
import json
import os
import re

# --- Page Config ---
st.set_page_config(
    page_title="F1 Racing Genius Quiz",
    page_icon="🏎️",
    layout="centered"
)

# --- Functions ---
def generate_f1_quiz(api_key, topic, difficulty_level, year):
    # Configure Gemini API
    genai.configure(api_key=api_key)
    
    model_name = 'gemini-2.5-flash'
    model = genai.GenerativeModel(model_name, generation_config={"response_mime_type": "application/json"})
    
    difficulty_guide = ""
    if difficulty_level == "Rookie (입문)":
        difficulty_guide = "Easy questions for beginners. Focus on famous drivers, teams, and basic rules."
    elif difficulty_level == "Driver (중급)":
        difficulty_guide = "Medium difficulty. Specific stats, historical events, track details, and technology."
    else: # World Champion
        difficulty_guide = "Very Hard. Obscure records, specific year details, technical regulations, and deep history."

    # Handle Random Topic
    if "랜덤" in topic:
        topic_instruction = "Mix questions from various categories: Drivers, History, Technology, Circuits, and Rules."
    else:
        topic_instruction = topic

    year_instruction = f"Focus on events and facts from the {year} F1 season." if year != "All Time (전체 연도)" else "Include questions from all F1 seasons."

    prompt = f"""
    You are an F1 (Formula 1) Expert and Commentator. You are creating a quiz for a 12-year-old fan who loves F1 history, drivers, and technology.
    
    **Task**: Create a fun and challenging F1 Quiz Set.
    
    **Parameters**:
    - **Topic**: {topic_instruction}
    - **Year**: {year_instruction}
    - **Difficulty**: {difficulty_guide}
    - **Format**: 5 Multiple Choice Questions.
    
    **Requirements**:
    1. **Context/Intro**: Start with a "Did you know?" style short paragraph related to the topic. It should be interesting and educational (approx 3-5 sentences).
    2. **Questions**: Create 5 multiple-choice questions.
       - Make them fun and engaging.
       - Ensure options are plausible.
    3. **Language**: **Korean (한국어)**. The content must be in Korean, friendly and exciting for a 12-year-old.
    4. **Explanation**: Provide a clear explanation for the correct answer.
    
    **Output Format**:
    Return ONLY a valid JSON object with the following structure:
    {{
        "title": "Quiz Title (e.g., 'Senna vs Prost', 'The 2021 Season')",
        "intro": "Interesting intro text...",
        "questions": [
            {{
                "question": "Question text...",
                "options": ["1. Option A", "2. Option B", "3. Option C", "4. Option D"],
                "answer": "1",
                "explanation": "Explanation text..."
            }}
        ]
    }}
    """

    try:
        response = model.generate_content(prompt)
        text_response = response.text
        
        # Clean up JSON string
        if "```json" in text_response:
            text_response = text_response.split("```json")[1].split("```")[0]
        elif "```" in text_response:
            text_response = text_response.split("```")[1].split("```")[0]
            
        text_response = re.sub(r',\s*]', ']', text_response)
        text_response = re.sub(r',\s*}', '}', text_response)
        
        return json.loads(text_response)
    except Exception as e:
        return {"error": str(e)}

# --- Constants ---
TOPICS = [
    "🎲 랜덤 믹스 (Random Mix - All Topics)",
    "전설적인 드라이버 (Legends: Senna, Schumacher, etc.)",
    "현역 드라이버 (Current Grid: Verstappen, Hamilton, etc.)",
    "F1 역사와 기록 (History & Records)",
    "F1 기술과 규칙 (Tech & Regulations)",
    "서킷과 그랑프리 (Circuits & Grand Prix)",
    "드라마틱한 순간들 (Dramatic Moments & Rivalries)"
]

YEARS = ["All Time (전체 연도)"] + [str(year) for year in range(2025, 1949, -1)]

# --- Session State ---
if 'quiz_data' not in st.session_state:
    st.session_state.quiz_data = None
if 'quiz_graded' not in st.session_state:
    st.session_state.quiz_graded = False
if 'is_generating' not in st.session_state:
    st.session_state.is_generating = False

def start_generation():
    st.session_state.is_generating = True

# --- Main UI ---
st.title("🏎️ F1 Racing Genius Quiz")
st.markdown("F1의 역사, 기술, 전설적인 드라이버들에 대해 얼마나 알고 있나요? 당신의 지식을 테스트해보세요!")

# --- Sidebar / Settings ---
with st.container():
    st.markdown("### 🔧 레이스 설정 (Race Setup)")
    
    # API Key Handling
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    else:
        api_key = st.text_input("Google Gemini API Key", type="password")
        if not api_key:
            st.warning("API 키를 입력하거나 .streamlit/secrets.toml에 설정해주세요.")
            st.stop()

    col1, col2 = st.columns(2)
    with col1:
        selected_year = st.selectbox("연도 선택 (Year)", YEARS, disabled=st.session_state.is_generating)
        topic = st.selectbox("주제 선택 (Topic)", TOPICS, disabled=st.session_state.is_generating)
    with col2:
        difficulty = st.select_slider(
            "난이도 (Difficulty)",
            options=["Rookie (입문)", "Driver (중급)", "World Champion (상급)"], 
            value="Driver (중급)",
            disabled=st.session_state.is_generating
        )
    
    if st.session_state.is_generating:
        st.button("🚦 생성 중... (Pit Stop)", disabled=True, type="primary", use_container_width=True)
    else:
        st.button("🏁 레이스 시작 (Start Quiz)", on_click=start_generation, type="primary", use_container_width=True)

# --- Generation Logic ---
if st.session_state.is_generating:
    with st.spinner("엔진 예열 중... F1 데이터를 분석하고 있습니다! 🏎️💨"):
        result = generate_f1_quiz(api_key, topic, difficulty, selected_year)
        if "error" in result:
            st.error(f"Engine Failure! 오류가 발생했습니다: {result['error']}")
        else:
            st.session_state.quiz_data = result
            st.session_state.quiz_graded = False
        st.session_state.is_generating = False
        st.rerun()

# --- Quiz Display ---
if st.session_state.quiz_data:
    data = st.session_state.quiz_data
    
    st.divider()
    st.subheader(f"🏆 {data.get('title', 'F1 Quiz')}")
    
    # Intro Box
    st.info(f"💡 **Did You Know?**\n\n{data.get('intro', '')}")
    
    questions = data.get('questions', [])
    user_answers = {}
    
    with st.form("f1_quiz_form"):
        for idx, q in enumerate(questions):
            st.markdown(f"**Q{idx+1}. {q['question']}**")
            
            # Options
            choice = st.radio(
                f"Question {idx+1}", 
                q['options'], 
                index=None, 
                key=f"q_{idx}",
                label_visibility="collapsed"
            )
            user_answers[idx] = choice
            st.write("") # Spacer
            
        submitted = st.form_submit_button("🏁 체커기 받기 (Finish Race)")
        
        if submitted:
            if len(user_answers) < len(questions) or any(v is None for v in user_answers.values()):
                st.warning("아직 완주하지 못했습니다! 모든 문제를 풀어주세요.")
            else:
                st.session_state.quiz_graded = True
                st.rerun()

    # --- Results ---
    if st.session_state.quiz_graded:
        st.divider()
        st.subheader("📊 레이스 결과 (Race Results)")
        
        score = 0
        total = len(questions)
        
        for idx, q in enumerate(questions):
            user_choice = user_answers.get(idx)
            # Extract numbers "1" from "1. Answer"
            user_num = user_choice.split('.')[0].strip() if user_choice else ""
            correct_num = str(q['answer']).split('.')[0].strip()
            
            if user_num == correct_num:
                score += 1
                
        # Podium Logic
        percentage = (score / total) * 100
        if percentage == 100:
            st.balloons()
            st.success(f"🥇 **P1! 폴 투 윈!** (점수: {score}/{total}) - 완벽해요!")
        elif percentage >= 80:
            st.success(f"🥈 **포디움 피니시!** (점수: {score}/{total}) - 훌륭한 레이스였습니다.")
        elif percentage >= 60:
            st.info(f"🥉 **포인트 획득!** (점수: {score}/{total}) - 잘했습니다.")
        else:
            st.warning(f"🔧 **피트인 필요!** (점수: {score}/{total}) - 더 연습해보세요!")
            
        # Explanations
        with st.expander("📝 상세 해설 보기 (Telemetry Data)", expanded=True):
            for idx, q in enumerate(questions):
                correct_num = str(q['answer']).split('.')[0].strip()
                user_choice = user_answers.get(idx)
                user_num = user_choice.split('.')[0].strip() if user_choice else ""
                
                if user_num == correct_num:
                    st.markdown(f"✅ **Q{idx+1}: 정답!**")
                else:
                    st.markdown(f"❌ **Q{idx+1}: 오답** (당신의 선택: {user_num} / 정답: {correct_num})")
                
                st.markdown(f"**해설**: {q['explanation']}")
                st.markdown("---")

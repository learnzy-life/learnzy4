import streamlit as st
import pandas as pd
import time
import altair as alt
from datetime import datetime

# Google Sheets CSV URL
SHEET_URL = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vR4BK9IQmKNdiw3Gx_BLj_3O_uAKmt4SSEwmqzGldFu0DhMnKQ4QGOZZQ1AsY-6AbbHgAGjs5H_gIuV/pub?output=csv'

# Session state management
def init_session():
    required_states = {
        'authenticated': False,
        'test_started': False,
        'current_question': 0,
        'user_answers': {},
        'username': None,
        'start_time': None,
        'questions': []
    }
    for key, value in required_states.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session()

# Data loading with validation
@st.cache_data(ttl=3600)
def load_valid_questions():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = df.columns.str.strip()
        
        valid_questions = []
        required_columns = [
            'Question ID', 'Question Text', 'Option A', 'Option B',
            'Option C', 'Option D', 'Correct Answer', 'Subject', 'Topic',
            'Sub- Topic', 'Difficulty Level', 'Question Type', 'Cognitive Level'
        ]
        
        # Validate columns
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            st.error(f"Missing columns: {', '.join(missing_cols)}")
            return []
        
        # Validate each question
        for _, row in df.iterrows():
            options = [
                str(row['Option A']).strip(),
                str(row['Option B']).strip(),
                str(row['Option C']).strip(),
                str(row['Option D']).strip()
            ]
            
            # Check for valid question structure
            if (all(options) and len(options) == 4 and 
                row['Correct Answer'].strip().upper() in ['A', 'B', 'C', 'D']):
                valid_questions.append(row.to_dict())
        
        if len(valid_questions) < len(df):
            st.warning(f"Skipped {len(df)-len(valid_questions)} invalid/malformed questions")
        
        return valid_questions
        
    except Exception as e:
        st.error(f"Data loading failed: {str(e)}")
        return []

# Authentication
def authenticate():
    with st.form("auth"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if username == "user1" and password == "password1":
                st.session_state.authenticated = True
                st.session_state.username = username
                st.session_state.questions = load_valid_questions()
            else:
                st.error("Invalid credentials")
# Previous imports and functions remain the same...

def analyze_time_management():
    total_time = sum(ans['time_taken'] for ans in st.session_state.user_answers.values())
    total_minutes = total_time / 60
    ideal_time = len(st.session_state.questions) * 2 * 60  # 2 minutes per question
    ideal_minutes = ideal_time / 60
    
    with st.expander("⏱️ Time Management Analysis", expanded=True):
        # Overall Time Metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("Test Duration", f"{ideal_minutes:.0f} min")
        col2.metric("Your Time", f"{total_minutes:.1f} min")
        col3.metric("Difference", 
                   f"{(total_minutes - ideal_minutes):.1f} min",
                   delta="Over" if total_minutes > ideal_minutes else "Under")
        
        # Time summary
        st.write(f"""
        > You took {total_minutes:.1f} minutes to complete the test, which is 
        {abs(total_minutes - ideal_minutes):.1f} minutes {'more' if total_minutes > ideal_minutes else 'less'} 
        than the ideal time.
        """)
        
        # Create time analysis dataframe
        time_data = []
        for q in st.session_state.questions:
            ans = st.session_state.user_answers.get(q['Question ID'], {})
            time_data.append({
                'Question': f"Q{q['Question ID']}",
                'Subject': q['Subject'],
                'Your Time': ans.get('time_taken', 0) / 60,  # Convert to minutes
                'Ideal Time': 2,  # 2 minutes per question
                'Time Ratio': (ans.get('time_taken', 0) / 60) / 2
            })
        
        time_df = pd.DataFrame(time_data)
        
        # Altair Chart
        base = alt.Chart(time_df).encode(
            x='Question:O',
            color='Subject:N'
        )
        
        bars = base.mark_bar().encode(
            y='Your Time:Q',
            tooltip=['Question', 'Subject', 'Your Time', 'Ideal Time']
        )
        
        ideal_line = base.mark_line(color='red').encode(
            y='Ideal Time:Q'
        )
        
        st.altair_chart((bars + ideal_line).properties(
            width=600,
            height=400,
            title='Time Spent per Question vs Ideal Time'
        ))
        
        # Analyze slow and quick questions
        slow_questions = time_df[time_df['Time Ratio'] > 1.5]
        quick_questions = time_df[time_df['Time Ratio'] < 0.75]
        
        if not slow_questions.empty:
            st.warning("""
            ### Slow Questions
            You spent significantly more time than ideal on these questions:
            """)
            st.dataframe(slow_questions[['Question', 'Subject', 'Your Time', 'Ideal Time']])
            
        if not quick_questions.empty:
            st.info("""
            ### Quick Questions
            You answered these questions much faster than the ideal time:
            """)
            st.dataframe(quick_questions[['Question', 'Subject', 'Your Time', 'Ideal Time']])

def analyze_topics():
    with st.expander("📚 Topic & Subtopic Analysis", expanded=True):
        # Subject Overview
        subjects = pd.DataFrame([
            {
                'Subject': q['Subject'],
                'Correct': 1 if st.session_state.user_answers.get(q['Question ID'], {}).get('selected') == 
                          q['Correct Answer'].strip().upper() else 0,
                'Total': 1
            }
            for q in st.session_state.questions
        ]).groupby('Subject').agg({
            'Correct': 'sum',
            'Total': 'sum'
        }).reset_index()
        
        subjects['Accuracy'] = (subjects['Correct'] / subjects['Total'] * 100).round(1)
        subjects['Mastery'] = subjects['Accuracy'].apply(lambda x: 
            "NEET Ready" if x >= 80 else "On the Path" if x >= 50 else "Needs Improvement")
        
        for _, subj in subjects.iterrows():
            col1, col2 = st.columns([3, 1])
            col1.progress(subj['Accuracy'] / 100)
            col2.metric(
                subj['Subject'],
                f"{subj['Correct']}/{subj['Total']}",
                f"{subj['Accuracy']}%"
            )
            st.write(f"Status: **{subj['Mastery']}**")
        
        # Topic Distribution
        topics_df = pd.DataFrame([
            {
                'Subject': q['Subject'],
                'Topic': q['Topic'],
                'Correct': 1 if st.session_state.user_answers.get(q['Question ID'], {}).get('selected') == 
                          q['Correct Answer'].strip().upper() else 0,
                'Time': st.session_state.user_answers.get(q['Question ID'], {}).get('time_taken', 0),
                'Total': 1
            }
            for q in st.session_state.questions
        ]).groupby(['Subject', 'Topic']).agg({
            'Correct': 'sum',
            'Time': 'mean',
            'Total': 'sum'
        }).reset_index()
        
        topics_df['Accuracy'] = (topics_df['Correct'] / topics_df['Total'] * 100).round(1)
        topics_df['Avg Time (min)'] = (topics_df['Time'] / 60).round(1)
        
        for subject in topics_df['Subject'].unique():
            st.subheader(f"{subject} Topics")
            subject_topics = topics_df[topics_df['Subject'] == subject]
            st.dataframe(subject_topics[['Topic', 'Accuracy', 'Avg Time (min)', 'Total']])

def analyze_deep_insights():
    with st.expander("🔍 Deep Insights", expanded=True):
        tabs = st.tabs(["Difficulty", "Question Types", "Cognitive Levels", "Combined Analysis"])
        
        with tabs[0]:
            difficulty_analysis = pd.DataFrame([
                {
                    'Difficulty': q['Difficulty Level'],
                    'Correct': 1 if st.session_state.user_answers.get(q['Question ID'], {}).get('selected') == 
                              q['Correct Answer'].strip().upper() else 0,
                    'Total': 1
                }
                for q in st.session_state.questions
            ]).groupby('Difficulty').agg({
                'Correct': 'sum',
                'Total': 'sum'
            }).reset_index()
            
            difficulty_analysis['Accuracy'] = (difficulty_analysis['Correct'] / difficulty_analysis['Total'] * 100).round(1)
            
            for _, diff in difficulty_analysis.iterrows():
                st.metric(
                    f"{diff['Difficulty']} Questions",
                    f"{diff['Accuracy']}%",
                    f"{diff['Correct']}/{diff['Total']}"
                )
        
        with tabs[1]:
            question_types = pd.DataFrame([
                {
                    'Type': q['Question Type'],
                    'Correct': 1 if st.session_state.user_answers.get(q['Question ID'], {}).get('selected') == 
                              q['Correct Answer'].strip().upper() else 0,
                    'Total': 1
                }
                for q in st.session_state.questions
            ]).groupby('Type').agg({
                'Correct': 'sum',
                'Total': 'sum'
            }).reset_index()
            
            question_types['Accuracy'] = (question_types['Correct'] / question_types['Total'] * 100).round(1)
            st.bar_chart(question_types.set_index('Type')['Accuracy'])
        
        with tabs[2]:
            cognitive_analysis = pd.DataFrame([
                {
                    'Level': q['Cognitive Level'],
                    'Correct': 1 if st.session_state.user_answers.get(q['Question ID'], {}).get('selected') == 
                              q['Correct Answer'].strip().upper() else 0,
                    'Total': 1
                }
                for q in st.session_state.questions
            ]).groupby('Level').agg({
                'Correct': 'sum',
                'Total': 'sum'
            }).reset_index()
            
            cognitive_analysis['Accuracy'] = (cognitive_analysis['Correct'] / cognitive_analysis['Total'] * 100).round(1)
            
            for _, level in cognitive_analysis.iterrows():
                st.progress(level['Accuracy'] / 100)
                st.write(f"**{level['Level']}**: {level['Accuracy']}%")

def generate_improvement_plan():
    with st.expander("🚀 Improvement Plan", expanded=True):
        # Identify weak areas
        topics_analysis = pd.DataFrame([
            {
                'Subject': q['Subject'],
                'Topic': q['Topic'],
                'Subtopic': q['Sub- Topic'],
                'Difficulty': q['Difficulty Level'],
                'Correct': 1 if st.session_state.user_answers.get(q['Question ID'], {}).get('selected') == 
                          q['Correct Answer'].strip().upper() else 0,
                'Total': 1
            }
            for q in st.session_state.questions
        ]).groupby(['Subject', 'Topic', 'Subtopic', 'Difficulty']).agg({
            'Correct': 'sum',
            'Total': 'sum'
        }).reset_index()
        
        topics_analysis['Accuracy'] = (topics_analysis['Correct'] / topics_analysis['Total'] * 100).round(1)
        weak_topics = topics_analysis[topics_analysis['Accuracy'] < 70].sort_values('Accuracy')
        
        if not weak_topics.empty:
            st.write("### Top 5 Areas to Focus On")
            for i, topic in weak_topics.head().iterrows():
                with st.container():
                    st.write(f"**{i+1}. {topic['Subject']}: {topic['Topic']} - {topic['Subtopic']}**")
                    st.write(f"Current Accuracy: {topic['Accuracy']}%")
                    st.write("Suggested Resources:")
                    st.write("- 📚 Practice Set: 10 questions on this topic")
                    st.write("- 🎥 Watch concept video (15 mins)")
                    st.write("- 📝 Review key formulas and concepts")

def show_results():
    st.balloons()
    st.title("📊 Comprehensive Analysis Report")
    
    # Call all analysis functions
    analyze_time_management()
    analyze_topics()
    analyze_deep_insights()
    generate_improvement_plan()
    
    if st.button("Retake Test 🔄"):
        st.session_state.clear()
        init_session()
        st.rerun()

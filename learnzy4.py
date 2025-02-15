import streamlit as st
import pandas as pd
import altair as alt
import time
import unicodedata
from datetime import datetime

# ================== Configuration ==================
MOCKS = {
    'Mock Test 1': {'gid': '848132391'},
    'Mock Test 2': {'gid': '610172732'},
    'Mock Test 3': {'gid': '1133755197'},
    'Mock Test 4': {'gid': '690484996'},
    'Mock Test 5': {'gid': '160639837'}
}

COLUMN_MAPPING = {
    'question_number': ['qno', 'number', 'qnum'],
    'question_text': ['question', 'text'],
    'option_a': ['a', 'opt1'],
    'option_b': ['b', 'opt2'],
    'option_c': ['c', 'opt3'],
    'option_d': ['d', 'opt4'],
    'correct_answer': ['answer', 'correct'],
    'subject': ['sub', 'category'],
    'topic': ['chapter', 'unit'],
    'subtopic': ['subchapter', 'module'],
    'difficulty_level': ['difficulty', 'complexity'],
    'question_structure': ['type', 'qtype'],
    'blooms_taxonomy': ['bloom', 'taxonomy'],
    'priority_level': ['priority', 'weightage'],
    'time_to_solve': ['time', 'duration', 'benchmark'],
    'key_concept': ['concept', 'key'],
    'common_pitfalls': ['pitfalls', 'mistakes']
}

# ================== Helper Functions ==================
def normalize_text(text):
    """Normalize text for consistent matching"""
    text = unicodedata.normalize('NFKD', str(text).strip().lower())
    return ''.join([c for c in text if not unicodedata.combining(c)]).replace(' ', '_')

def map_columns(df_columns):
    """Map actual columns to standardized names with fuzzy matching"""
    column_map = {}
    for col in df_columns:
        normalized = normalize_text(col)
        matched = False
        for standard, aliases in COLUMN_MAPPING.items():
            variants = [normalize_text(v) for v in [standard] + aliases]
            if normalized in variants:
                column_map[col] = standard
                matched = True
                break
        if not matched:
            column_map[col] = col  # Keep original if no match
    return column_map

# ================== Data Loading ==================
@st.cache_data(show_spinner="⏳ Loading test data...")
def load_mock_data(gid):
    try:
        url = f"https://docs.google.com/spreadsheets/d/e/2PACX-1vQvDpDbBzkcr1-yuTXAfYHvV6I0IzWHnU7SFF1ogGBK-PBIru25TthrwVJe3WiqTYchBoCiSyT0V1PJ/pub?output=csv&gid={gid}"
        df = pd.read_csv(url)
        
        # Normalize columns
        column_map = map_columns(df.columns)
        df = df.rename(columns=column_map)
        
        # Convert critical columns
        if 'time_to_solve' in df.columns:
            df['time_to_solve'] = pd.to_numeric(df['time_to_solve'], errors='coerce').fillna(30)
            
        return df.to_dict('records')
    except Exception as e:
        st.error(f"🚨 Data loading failed: {str(e)}")
        return None

# ================== Analysis Sections ==================
def time_management_section(data):
    """⏱ Time Management Analysis Section"""
    try:
        st.header("⏱ Time Management Analysis")
        
        # Calculate time metrics
        total_time = sum(ans.get('time_taken', 0) for ans in st.session_state.user_answers.values())
        benchmark_time = sum(q.get('time_to_solve', 0) for q in data)
        
        # Metrics Row
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Your Total Time", f"{total_time//60}m {int(total_time%60)}s")
        with col2:
            st.metric("Recommended Time", f"{benchmark_time//60}m {int(benchmark_time%60)}s")
        with col3:
            delta = total_time - benchmark_time
            st.metric("Difference", 
                      f"{abs(delta)//60}m {int(abs(delta)%60)}s", 
                      delta="Under" if delta < 0 else "Over")
        
        # Time Comparison Chart
        chart_data = []
        for q in data:
            q_time = st.session_state.user_answers.get(q['question_number'], {}).get('time_taken', 0)
            chart_data.extend([
                {'Question': q['question_number'], 'Subject': q.get('subject', 'General'),
                 'Time Type': 'Your Time', 'Seconds': q_time},
                {'Question': q['question_number'], 'Subject': q.get('subject', 'General'),
                 'Time Type': 'Recommended', 'Seconds': q.get('time_to_solve', 0)}
            ])
        
        chart = alt.Chart(pd.DataFrame(chart_data)).mark_bar().encode(
            x=alt.X('Question:O', title="Question Number"),
            y=alt.Y('sum(Seconds):Q', title="Time (seconds)"),
            color='Time Type:N',
            column='Subject:N'
        ).properties(width=80, height=200)
        
        st.altair_chart(chart)
        
    except Exception as e:
        st.error(f"Error in time analysis: {str(e)}")

def topic_analysis_section(data):
    """📚 Topic-wise Performance Section"""
    try:
        st.header("📚 Topic & Subtopic Analysis")
        
        # Calculate topic stats
        topic_stats = {}
        for q in data:
            topic = q.get('topic', 'Unknown')
            subtopic = q.get('subtopic', 'Unknown')
            key = f"{topic}||{subtopic}"
            
            if key not in topic_stats:
                topic_stats[key] = {
                    'correct': 0,
                    'total': 0,
                    'time_spent': 0,
                    'time_benchmark': 0
                }
            
            ans = st.session_state.user_answers.get(q['question_number'], {})
            topic_stats[key]['correct'] += 1 if ans.get('selected') == ans.get('correct') else 0
            topic_stats[key]['total'] += 1
            topic_stats[key]['time_spent'] += ans.get('time_taken', 0)
            topic_stats[key]['time_benchmark'] += q.get('time_to_solve', 0)
        
        # Display topic cards
        for key, stats in topic_stats.items():
            topic, subtopic = key.split('||')
            accuracy = (stats['correct'] / stats['total']) * 100
            time_diff = (stats['time_spent'] - stats['time_benchmark']) / stats['total']
            
            with st.expander(f"{topic} - {subtopic} ({accuracy:.1f}%)", expanded=True):
                col1, col2, col3 = st.columns([2,1,1])
                with col1:
                    st.markdown(f"**Accuracy**: {stats['correct']}/{stats['total']}")
                    st.progress(accuracy/100)
                with col2:
                    st.metric("Avg Time", f"{stats['time_spent']/stats['total']:.1f}s")
                with col3:
                    st.metric("Benchmark", f"{stats['time_benchmark']/stats['total']:.1f}s",
                             delta=f"{time_diff:.1f}s")
        
    except Exception as e:
        st.error(f"Error in topic analysis: {str(e)}")

def deep_insights_section(data):
    """🧠 Deep Cognitive Insights Section"""
    try:
        st.header("🧠 Deep Learning Insights")
        
        # Difficulty Analysis
        difficulty_stats = {'Easy': {'correct': 0, 'total': 0},
                           'Medium': {'correct': 0, 'total': 0},
                           'Hard': {'correct': 0, 'total': 0}}
        
        # Bloom's Taxonomy Analysis
        bloom_stats = {'Remember': 0, 'Understand': 0, 'Apply': 0, 'Analyze': 0}
        
        for q in data:
            # Difficulty analysis
            difficulty = q.get('difficulty_level', 'Medium').title()
            if difficulty not in difficulty_stats:
                difficulty = 'Medium'
            difficulty_stats[difficulty]['total'] += 1
            if st.session_state.user_answers.get(q['question_number'], {}).get('correct'):
                difficulty_stats[difficulty]['correct'] += 1
            
            # Bloom's taxonomy analysis
            bloom_level = q.get('blooms_taxonomy', 'Remember').title()
            bloom_stats[bloom_level] += 1
        
        # Display difficulty analysis
        with st.expander("📊 Difficulty Analysis", expanded=True):
            cols = st.columns(3)
            for i, (level, stats) in enumerate(difficulty_stats.items()):
                accuracy = (stats['correct'] / stats['total']) * 100 if stats['total'] >0 else 0
                cols[i].metric(f"{level} Questions", 
                              f"{stats['correct']}/{stats['total']}", 
                              f"{accuracy:.1f}%")
        
        # Display Bloom's taxonomy
        with st.expander("🧠 Cognitive Levels (Bloom's Taxonomy)", expanded=True):
            bloom_df = pd.DataFrame(list(bloom_stats.items()), columns=['Level', 'Count'])
            chart = alt.Chart(bloom_df).mark_arc().encode(
                theta='Count:Q',
                color='Level:N',
                tooltip=['Level', 'Count']
            ).properties(width=400, height=300)
            st.altair_chart(chart)
            
    except Exception as e:
        st.error(f"Error in deep insights: {str(e)}")

# ================== Main App Flow ==================
def main():
    st.set_page_config(page_title="ExamPrep Pro", layout="wide", page_icon="📚")
    
    # Initialize session state
    if 'test_selected' not in st.session_state:
        st.session_state.update({
            'test_selected': None,
            'data_loaded': None,
            'user_answers': {},
            'current_question': 0,
            'test_started': False
        })
    
    # Test selection screen
    if not st.session_state.test_selected:
        st.title("📚 ExamPrep Pro Mock Test Platform")
        cols = st.columns(3)
        with cols[1]:
            st.image("https://cdn-icons-png.flaticon.com/512/3135/3135810.png", width=150)
        
        for mock_name, mock_data in MOCKS.items():
            if st.button(f"📝 {mock_name}", key=f"mock_{mock_name}"):
                st.session_state.test_selected = mock_data['gid']
                st.session_state.data_loaded = load_mock_data(mock_data['gid'])
                st.rerun()
    
    # Test analysis screen
    else:
        data = st.session_state.data_loaded
        if not data:
            st.error("❌ Failed to load test data. Please select another test.")
            return
        
        st.title(f"📊 Test Analysis Report")
        
        # Main analysis sections
        time_management_section(data)
        topic_analysis_section(data)
        deep_insights_section(data)
        
        # Reset controls
        if st.button("🔄 Take Another Test"):
            st.session_state.clear()
            st.rerun()

if __name__ == "__main__":
    main()

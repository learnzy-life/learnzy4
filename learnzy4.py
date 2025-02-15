import streamlit as st
import pandas as pd
import time
import unicodedata

# ================== Configuration ==================
MOCKS = {
    'Mock Test 1': {'gid': '848132391'},
    'Mock Test 2': {'gid': '610172732'},
    'Mock Test 3': {'gid': '1133755197'},
    'Mock Test 4': {'gid': '690484996'},
    'Mock Test 5': {'gid': '160639837'}
}

COLUMN_MAPPING = {
    'question_number': ['qno', 'number'],
    'question_text': ['question'],
    'option_a': ['a'],
    'option_b': ['b'],
    'option_c': ['c'],
    'option_d': ['d'],
    'correct_answer': ['answer'],
    'subject': ['sub'],
    'topic': ['chapter'],
    'subtopic': ['subchapter'],
    'difficulty_level': ['difficulty'],
    'question_structure': ['type'],
    'blooms_taxonomy': ['bloom'],
    'priority_level': ['priority'],
    'time_to_solve': ['time', 'duration'],
    'key_concept': ['concept'],
    'common_pitfalls': ['pitfalls']
}

# ================== Helper Functions ==================
def normalize_text(text):
    return unicodedata.normalize('NFKD', str(text).lower().strip()).replace(' ', '_')

def map_columns(df_columns):
    column_map = {}
    for col in df_columns:
        normalized = normalize_text(col)
        for standard, aliases in COLUMN_MAPPING.items():
            if normalized in [normalize_text(a) for a in aliases + [standard]]:
                column_map[col] = standard
                break
        else:
            column_map[col] = col
    return column_map

# ================== Data Loading ==================
@st.cache_data(show_spinner=False)
def load_mock_data(gid):
    try:
        url = f"https://docs.google.com/spreadsheets/d/e/2PACX-1vQvDpDbBzkcr1-yuTXAfYHvV6I0IzWHnU7SFF1ogGBK-PBIru25TthrwVJe3WiqTYchBoCiSyT0V1PJ/pub?output=csv&gid={gid}"
        df = pd.read_csv(url)
        df = df.rename(columns=map_columns(df.columns))
        if 'time_to_solve' in df.columns:
            df['time_to_solve'] = pd.to_numeric(df['time_to_solve'], errors='coerce')
        return df.to_dict('records')
    except Exception as e:
        st.error(f"Data loading failed: {str(e)}")
        return None

# ================== Test Components ==================
def show_question():
    q = st.session_state.data_loaded[st.session_state.current_question]
    
    st.subheader(f"Question {st.session_state.current_question + 1}")
    st.markdown(f"**{q.get('question_text', 'Question text missing')}**")
    
    options = [
        q.get('option_a', 'Option A missing'),
        q.get('option_b', 'Option B missing'),
        q.get('option_c', 'Option C missing'),
        q.get('option_d', 'Option D missing')
    ]
    
    answer = st.radio("Select your answer:", options, key=f"q{st.session_state.current_question}")
    
    if st.button("Next ➡️"):
        # Save answer
        question_id = q.get('question_number', st.session_state.current_question)
        st.session_state.user_answers[question_id] = {
            'selected': answer,
            'correct': q.get('correct_answer', 'X'),
            'time_taken': time.time() - st.session_state.question_start_time
        }
        
        # Move to next question or finish
        if st.session_state.current_question < len(st.session_state.data_loaded) - 1:
            st.session_state.current_question += 1
            st.session_state.question_start_time = time.time()
            st.rerun()
        else:
            st.session_state.test_started = False
            st.rerun()

# ================== Main App Flow ==================
def main():
    st.set_page_config(page_title="ExamPrep Pro", layout="wide")
    
    # Initialize session state
    if 'current_question' not in st.session_state:
        st.session_state.update({
            'test_selected': None,
            'data_loaded': None,
            'test_started': False,
            'current_question': 0,
            'user_answers': {},
            'question_start_time': time.time()
        })
    
    # Test selection screen
    if not st.session_state.test_selected:
        st.title("📚 ExamPrep Pro")
        for mock_name, mock_data in MOCKS.items():
            if st.button(mock_name):
                st.session_state.test_selected = mock_data['gid']
                st.session_state.data_loaded = load_mock_data(mock_data['gid'])
                st.rerun()
    
    else:
        data = st.session_state.data_loaded
        if not data:
            st.error("Failed to load test data")
            return
        
        # Test taking flow
        if st.session_state.test_started:
            show_question()
        else:
            # Pre-test screen
            with st.expander("📝 Test Syllabus", expanded=True):
                st.write(f"Total Questions: {len(data)}")
                st.write(f"Subjects: {', '.join(set(str(q.get('subject', '')) for q in data)}")
                
                if st.button("🚀 Start Test"):
                    st.session_state.test_started = True
                    st.session_state.current_question = 0
                    st.session_state.user_answers = {}
                    st.session_state.question_start_time = time.time()
                    st.rerun()
            
            # Show analysis after completion
            if st.session_state.user_answers:
                st.title("📊 Analysis Report")
                st.write("Test analysis content goes here")
        
        if st.button("🔙 Return to Test Selection"):
            st.session_state.clear()
            st.rerun()

if __name__ == "__main__":
    main()

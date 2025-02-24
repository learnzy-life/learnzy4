# app.py
import streamlit as st
import pandas as pd
import altair as alt
import time
from datetime import datetime
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Tuple, Optional
import json

# Constants
MOCK_TEST_GIDS = {
    'diagnostic': '160639837',
    'mock1': '848132391',
    'mock2': '610172732',
    'mock3': '1133755197',
    'mock4': '690484996',
    'mock5': '1484362111'
}

class TestData:
    def __init__(self, gid: str):
        self.gid = gid
        self.questions = None
        self.answers = None
        self.total_questions = 40
        self.start_time = None
        self.time_per_question = {}
        self.last_question = None
        self.last_timestamp = None
        self.tags = {}
        self.current_question = 0
        
    def fetch_data(self) -> bool:
        """Fetch test data from Google Sheets."""
        base_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQtG0QdIu8N1BPgVHeYDArIRCwvMU7NmN_YUM3_UUwU2FkmMYhJTtDxoS2Lk7kX6LNJHnLlAdgLSWPx/pub?gid={}&single=true&output=csv"
        try:
            self.questions = pd.read_csv(base_url.format(self.gid))
            self.questions.columns = self.questions.columns.str.strip()
            self.answers = [None] * self.total_questions
            self.start_time = time.time()
            self.time_per_question = {i: 0 for i in range(self.total_questions)}
            return True
        except Exception as e:
            st.error(f"Error fetching data: {e}")
            return False

class Analytics:
    def __init__(self, test_data: TestData):
        self.test_data = test_data
        
    def calculate_score(self) -> Tuple[int, List[int]]:
        """Calculate test score and identify incorrect questions."""
        score = 0
        incorrect_indices = []
        correct_answers = self.test_data.questions['Correct Answer'].tolist()
        
        for i in range(self.test_data.total_questions):
            if self.test_data.answers[i] == correct_answers[i]:
                score += 4
            elif self.test_data.answers[i] is not None:
                score -= 1
                incorrect_indices.append(i)
                
        return score, incorrect_indices

    def generate_time_analysis(self) -> Dict:
        """Generate comprehensive time analysis."""
        time_data = {
            'total_time': sum(self.test_data.time_per_question.values()),
            'ideal_time': self.test_data.questions['Time to Solve (seconds)'].sum(),
            'time_per_subject': self._analyze_time_by_subject(),
            'time_efficiency': self._calculate_time_efficiency()
        }
        return time_data

    def _analyze_time_by_subject(self) -> Dict:
        """Analyze time spent per subject."""
        subject_time = {}
        for subject in self.test_data.questions['Subject'].unique():
            mask = self.test_data.questions['Subject'] == subject
            subject_questions = self.test_data.questions[mask]
            subject_time[subject] = {
                'total_time': sum(self.test_data.time_per_question[i] for i in subject_questions.index),
                'ideal_time': subject_questions['Time to Solve (seconds)'].sum()
            }
        return subject_time

    def _calculate_time_efficiency(self) -> Dict:
        """Calculate time efficiency metrics."""
        efficiencies = []
        slow_questions = []
        quick_questions = []
        
        for i in range(self.test_data.total_questions):
            actual_time = self.test_data.time_per_question[i]
            ideal_time = self.test_data.questions.iloc[i]['Time to Solve (seconds)']
            
            if actual_time > 0 and ideal_time > 0:
                efficiency = (ideal_time - actual_time) / ideal_time
                efficiencies.append(efficiency)
                
                if efficiency < -0.5:  # Took 50% longer than ideal
                    slow_questions.append(i)
                elif efficiency > 0.5:  # Took 50% less time than ideal
                    quick_questions.append(i)
        
        return {
            'average_efficiency': sum(efficiencies) / len(efficiencies) if efficiencies else 0,
            'std_efficiency': np.std(efficiencies) if efficiencies else 0,
            'slow_questions': slow_questions,
            'quick_questions': quick_questions
        }

class UI:
    def __init__(self):
        if 'page' not in st.session_state:
            st.session_state.page = "welcome"
        if 'test_data' not in st.session_state:
            st.session_state.test_data = None

    def render_welcome(self):
        st.title("Welcome to NEET Prep AI")
        st.write("Get ready to ace NEET 2025 with our AI-powered diagnostic and mock tests!")
        
        # Add progress bar
        st.markdown("""
            <style>
            .stProgress > div > div > div > div {
                background-color: #4CAF50;
            }
            </style>""", 
            unsafe_allow_html=True
        )
        progress_bar = st.progress(0)
        for i in range(100):
            time.sleep(0.01)
            progress_bar.progress(i + 1)
        
        if st.button("Let's Crack NEET 2025", key="start_button"):
            st.session_state.page = "main"

    def render_main_dashboard(self):
        st.title("Main Dashboard")
        
        tab1, tab2, tab3 = st.tabs(["Available Tests", "Your Progress", "Resources"])
        
        with tab1:
            st.write("### Mock Tests")
            cols = st.columns(5)
            for i, col in enumerate(cols, 1):
                with col:
                    st.write(f"Mock Test {i}")
                    st.write("🔒 Locked")
                    
            st.write("### Diagnostic Test")
            if st.button("Take Diagnostic Test"):
                st.session_state.page = "diagnostic_test"
                st.session_state.test_data = TestData(MOCK_TEST_GIDS['diagnostic'])
                
        with tab2:
            st.write("Your progress will appear here after completing tests.")
            
        with tab3:
            st.write("### Study Resources")
            st.write("- 📚 NCERT Notes")
            st.write("- 🎥 Video Lectures")
            st.write("- 📝 Practice Questions")

    def render_test(self):
        if st.session_state.test_data is None or not st.session_state.test_data.questions:
            if not st.session_state.test_data.fetch_data():
                return
            
        self._render_question()
        self._render_navigation()
        self._render_timer()

    def _render_question(self):
        test_data = st.session_state.test_data
        current = test_data.current_question
        
        # Update time for previous question
        current_time = time.time()
        if test_data.last_question is not None:
            time_spent = current_time - test_data.last_timestamp
            test_data.time_per_question[test_data.last_question] += time_spent
        test_data.last_question = current
        test_data.last_timestamp = current_time

        # Display question with enhanced UI
        st.write(f"### Question {current + 1} of {test_data.total_questions}")
        
        question_tab, reference_tab = st.tabs(["Question", "Reference Material"])
        
        with question_tab:
            st.write(test_data.questions.iloc[current]['Question Text'])
            options = [test_data.questions.iloc[current][f'Option {letter}'] for letter in 'ABCD']
            
            # Enhanced radio buttons
            for i, option in enumerate(options):
                col1, col2 = st.columns([0.1, 0.9])
                with col1:
                    selected = st.radio("", [option], key=f"option_{current}_{i}")
                with col2:
                    st.write(f"{chr(65+i)}. {option}")
                if selected:
                    test_data.answers[current] = option

        with reference_tab:
            st.write("No additional reference material for this question.")

    def _render_navigation(self):
        test_data = st.session_state.test_data
        current = test_data.current_question
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if current > 0 and st.button("⬅️ Previous"):
                test_data.current_question -= 1
        with col2:
            if current < test_data.total_questions - 1 and st.button("Next ➡️"):
                test_data.current_question += 1
        with col3:
            if st.button("📝 Submit Test"):
                st.session_state.page = "post_test_analysis"

    def _render_timer(self):
        test_data = st.session_state.test_data
        elapsed_time = time.time() - test_data.start_time
        minutes = int(elapsed_time // 60)
        seconds = int(elapsed_time % 60)
        
        # Progress bar for time
        progress = min(elapsed_time / 2400, 1.0)  # 40 minutes = 2400 seconds
        st.progress(progress)
        
        # Time display with color coding
        if elapsed_time >= 2400:
            st.error(f"⏰ Time's up! {minutes:02d}:{seconds:02d}")
        elif elapsed_time >= 1800:  # Last 10 minutes
            st.warning(f"⏰ Time remaining: {minutes:02d}:{seconds:02d}")
        else:
            st.info(f"⏰ Time elapsed: {minutes:02d}:{seconds:02d}")

    def render_post_test_analysis(self):
        st.title("Post-Test Analysis")
        test_data = st.session_state.test_data
        analytics = Analytics(test_data)
        score, incorrect_indices = analytics.calculate_score()

        st.write(f"### Your Score: {score}/160")
        st.write(f"**Incorrect Questions:** {len(incorrect_indices)}")

        for idx in incorrect_indices:
            st.write(f"#### Question {idx + 1}")
            st.write(test_data.questions.iloc[idx]['Question Text'])
            st.write(f"**Your Answer:** {test_data.answers[idx]}")
            st.write(f"**Correct Answer:** {test_data.questions.iloc[idx]['Correct Answer']}")
            
            # Error type and subjective tag selection
            col1, col2 = st.columns(2)
            with col1:
                error_type = st.selectbox(
                    "Error Type:",
                    ["Select", "Silly Mistake", "Forgot", "Not Prepared", "Other"],
                    key=f"error_{idx}"
                )
            with col2:
                subjective_tag = st.selectbox(
                    "Subjective Tag:",
                    ["Select", "Panicked", "Less Time", "Confused", "Other"],
                    key=f"subjective_{idx}"
                )
            
            test_data.tags[idx] = {
                "error_type": error_type,
                "subjective_tag": subjective_tag
            }
            st.write("---")

        if st.button("Proceed to Analytics"):
            st.session_state.page = "analytics"

    def render_analytics(self):
        st.title("Analytics Section")
        analytics = Analytics(st.session_state.test_data)
        time_analysis = analytics.generate_time_analysis()
        
        # Display analytics sections
        self._render_overview_section()
        self._render_time_management_section(time_analysis)
        self._render_subject_analysis()
        self._render_deep_insights()
        self._render_improvement_section()

def main():
    ui = UI()
    
    if st.session_state.page == "welcome":
        ui.render_welcome()
    elif st.session_state.page == "main":
        ui.render_main_dashboard()
    elif st.session_state.page == "diagnostic_test":
        ui.render_test()
    elif st.session_state.page == "post_test_analysis":
        ui.render_post_test_analysis()
    elif st.session_state.page == "analytics":
        ui.render_analytics()

if __name__ == "__main__":
    st.set_page_config(page_title="NEET Prep AI", layout="wide")
    main()

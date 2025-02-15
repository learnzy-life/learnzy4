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

# Your existing load_valid_questions and authenticate functions remain the same...

# Question display function
def display_question(q):
    try:
        st.subheader(f"Question {st.session_state.current_question + 1}/{len(st.session_state.questions)}")
        st.markdown(f"**{q['Question Text']}**")
        
        options = [
            str(q['Option A']).strip(),
            str(q['Option B']).strip(),
            str(q['Option C']).strip(),
            str(q['Option D']).strip()
        ]
        
        answer = st.radio("Choose answer:", options, key=f"q{st.session_state.current_question}")
        
        col1, col2 = st.columns([1, 5])
        if col1.button("Next ➡️"):
            try:
                selected_index = options.index(answer.strip())
                selected_option = chr(65 + selected_index)
            except ValueError:
                st.error("Invalid selection! Please choose a valid option.")
                return
            
            # Record answer and time
            st.session_state.user_answers[q['Question ID']] = {
                'selected': selected_option,
                'correct': q['Correct Answer'].strip().upper(),
                'time_taken': time.time() - st.session_state.start_time
            }
            
            # Move to next question or show results
            st.session_state.current_question += 1
            st.session_state.start_time = time.time()
            st.rerun()
            
    except Exception as e:
        st.error(f"Error displaying question: {str(e)}")
        st.session_state.current_question += 1
        st.rerun()

# Your existing analysis functions remain the same...

# Main app function
def main():
    st.title("AI-Powered Mock Test Platform 🚀")
    
    if not st.session_state.authenticated:
        authenticate()
    else:
        if not st.session_state.questions:
            st.error("No valid questions found. Check data source!")
        elif not st.session_state.test_started:
            st.header(f"Welcome {st.session_state.username}!")
            st.write(f"Total Questions: {len(st.session_state.questions)}")
            if st.button("Start Test 🚀"):
                st.session_state.test_started = True
                st.session_state.start_time = time.time()
                st.rerun()
        else:
            # Test in progress
            if st.session_state.current_question < len(st.session_state.questions):
                # Display progress bar
                progress = st.session_state.current_question / len(st.session_state.questions)
                st.progress(progress)
                
                # Display current question
                q = st.session_state.questions[st.session_state.current_question]
                display_question(q)
                
                # Show timer
                elapsed_time = time.time() - st.session_state.start_time
                st.info(f"Time spent on current question: {elapsed_time:.1f} seconds")
            else:
                # Show results when test is complete
                show_results()

if __name__ == "__main__":
    main()

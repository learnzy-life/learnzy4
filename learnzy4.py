import streamlit as st
import pandas as pd
import altair as alt
import time

# Function to fetch data from Google Sheet using GID
def fetch_data(gid):
    base_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQtG0QdIu8N1BPgVHeYDArIRCwvMU7NmN_YUM3_UUwU2FkmMYhJTtDxoS2Lk7kX6LNJHnLlAdgLSWPx/pub?gid={}&single=true&output=csv"
    url = base_url.format(gid)
    try:
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip()  # Clean column names to remove spaces
        return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

# Welcome Page
def welcome_page():
    st.title("Welcome to NEET Prep App")
    st.write("Get ready to ace NEET 2025 with our tailored diagnostic and mock tests!")
    if st.button("Let's Crack NEET 2025"):
        st.session_state.page = "main"

# Main Page
def main_page():
    st.title("Main Dashboard")
    st.write("### Available Tests")
    st.write("- **5 Mock Tests** (Currently Locked)")
    st.write("- **Diagnostic Test** (Available Now)")
    if st.button("Take Diagnostic Test"):
        st.session_state.page = "diagnostic_test"

# Diagnostic Test Page
def diagnostic_test_page():
    # Initialize session state variables if not already set
    if 'questions' not in st.session_state:
        st.session_state.questions = fetch_data(160639837)  # GID for Diagnostic Test
        if st.session_state.questions is not None:
            st.session_state.total_questions = len(st.session_state.questions)
            st.session_state.answers = [None] * st.session_state.total_questions
            st.session_state.current_question = 0
            st.session_state.start_time = time.time()
            st.session_state.time_per_question = {i: 0 for i in range(st.session_state.total_questions)}
            st.session_state.last_question = None
            st.session_state.last_timestamp = time.time()
        else:
            st.error("Unable to load questions. Please try again later.")
            return

    questions = st.session_state.questions
    current = st.session_state.current_question

    # Update time for previous question
    current_time = time.time()
    if st.session_state.last_question is not None:
        time_spent = current_time - st.session_state.last_timestamp
        st.session_state.time_per_question[st.session_state.last_question] += time_spent
    st.session_state.last_question = current
    st.session_state.last_timestamp = current_time

    # Display question
    st.write(f"### Question {current + 1} of {st.session_state.total_questions}")
    st.write(questions.iloc[current]['Question Text'])
    options = [questions.iloc[current][f'Option {letter}'] for letter in 'ABCD']
    if st.session_state.answers[current] is not None and st.session_state.answers[current] in options:
        default_index = options.index(st.session_state.answers[current])
    else:
        default_index = 0
    selected = st.radio("Select your answer:", options, index=default_index)
    st.session_state.answers[current] = selected

    # Navigation buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if current > 0 and st.button("Previous"):
            st.session_state.current_question -= 1
    with col2:
        if current < st.session_state.total_questions - 1 and st.button("Next"):
            st.session_state.current_question += 1
    with col3:
        if st.button("Submit Test"):
            # Update time for the last question
            current_time = time.time()
            time_spent = current_time - st.session_state.last_timestamp
            st.session_state.time_per_question[current] += time_spent
            st.session_state.page = "post_test_analysis"

    # Display elapsed time
    elapsed_time = current_time - st.session_state.start_time
    minutes = elapsed_time // 60
    seconds = elapsed_time % 60
    st.write(f"**Time Elapsed:** {minutes:.0f} minutes {seconds:.0f} seconds")
    if elapsed_time >= 2400:  # 40 minutes = 2400 seconds
        st.warning("Time's up! Please submit your test.")

# Post-Test Analysis Page
def post_test_analysis_page():
    st.title("Post-Test Analysis")
    questions = st.session_state.questions
    answers = st.session_state.answers
    correct_answers = questions['Correct Answer'].tolist()

    # Calculate score and identify incorrect questions
    score = 0
    incorrect_indices = []
    for i in range(st.session_state.total_questions):
        if answers[i] == correct_answers[i]:
            score += 4
        elif answers[i] is not None:
            score -= 1
            incorrect_indices.append(i)

    st.write(f"### Your Score: {score}/160")
    st.write(f"**Incorrect Questions:** {len(incorrect_indices)}")

    # Initialize tags if not already set
    if 'tags' not in st.session_state:
        st.session_state.tags = {i: {"error_type": "Select", "subjective_tag": "Select"} for i in incorrect_indices}

    error_types = ["Select", "Silly Mistake", "Forgot", "Not Prepared", "Other"]
    subjective_tags = ["Select", "Panicked", "Less Time", "Confused", "Other"]

    # Display incorrect questions with tagging options
    for idx in incorrect_indices:
        st.write(f"#### Question {idx + 1}")
        st.write(questions.iloc[idx]['Question Text'])
        st.write(f"**Your Answer:** {answers[idx]}")
        st.write(f"**Correct Answer:** {correct_answers[idx]}")
        error_type = st.selectbox("Error Type:", error_types, index=error_types.index(st.session_state.tags[idx]["error_type"]), key=f"error_{idx}")
        subjective_tag = st.selectbox("Subjective Tag:", subjective_tags, index=subjective_tags.index(st.session_state.tags[idx]["subjective_tag"]), key=f"subjective_{idx}")
        st.session_state.tags[idx] = {"error_type": error_type, "subjective_tag": subjective_tag}
        st.write("---")

    if st.button("Proceed to Analytics"):
        st.session_state.page = "analytics"

# Analytics Page
def analytics_page():
    st.title("Analytics Section")
    questions = st.session_state.questions
    answers = st.session_state.answers
    correct_answers = questions['Correct Answer'].tolist()
    time_per_question = st.session_state.time_per_question
    tags = st.session_state.tags if 'tags' in st.session_state else {}

    # Debugging: Print column names to verify
    st.write("Columns in questions DataFrame:", questions.columns.tolist())

    # Check if required columns are present
    required_columns = ['Subject', 'Time to Solve (seconds)', 'Difficulty Level', 'Topic']
    for col in required_columns:
        if col not in questions.columns:
            st.error(f"The '{col}' column is missing from the data. Please check the Google Sheet or data loading process.")
            return

    # 1. Overview of the Test
    st.header("1. Overview of the Test")
    correct_count = sum(1 for i in range(40) if answers[i] == correct_answers[i])
    accuracy = (correct_count / 40) * 100
    st.write(f"**Total Correct:** {correct_count}/40")
    st.write(f"**Accuracy:** {accuracy:.2f}%")
    total_time = sum(time_per_question.values())
    st.write(f"**Total Time Taken:** {total_time // 60:.0f} minutes {total_time % 60:.0f} seconds")

    # 2. Time Management
    st.header("2. Time Management")
    st.write("#### A. Overall Time Metrics")
    st.write(f"- **Test Duration Allowed:** 40 minutes")
    st.write(f"- **Your Total Time:** {total_time // 60:.0f} minutes {total_time % 60:.0f} seconds")
    ideal_time = questions['Time to Solve (seconds)'].sum()
    st.write(f"- **Ideal Total Time:** {ideal_time // 60:.0f} minutes {ideal_time % 60:.0f} seconds")
    if total_time > ideal_time:
        st.write(f"> You took {(total_time - ideal_time) // 60:.0f} minutes more than the ideal time.")
    else:
        st.write("> You finished faster than the ideal time. Great job!")

    st.write("#### B. Question-by-Question Time Analysis")
    time_data = pd.DataFrame({
        'Question': range(1, 41),
        'Your Time': [time_per_question[i] for i in range(40)],
        'Ideal Time': questions['Time to Solve (seconds)'],
        'Subject': questions['Subject']
    })
    chart = alt.Chart(time_data).mark_bar().encode(
        x='Question:N',
        y=alt.Y('Your Time:Q', title='Time (seconds)'),
        color=alt.Color('Subject:N', legend=alt.Legend(title="Subject")),
        tooltip=['Question', 'Your Time', 'Ideal Time', 'Subject']
    ).properties(width=600, height=400)
    st.altair_chart(chart)
    st.write("> This chart shows your time per question compared to the ideal time, segmented by subject.")

    st.write("#### C. Feedback on Slow and Quick Questions")
    slow_questions = [i + 1 for i in range(40) if time_per_question[i] > questions['Time to Solve (seconds)'][i] * 1.5]
    quick_questions = [i + 1 for i in range(40) if time_per_question[i] < questions['Time to Solve (seconds)'][i] * 0.75 and time_per_question[i] > 0]
    if slow_questions:
        st.write(f"> You were slower on questions: {', '.join(map(str, slow_questions))}. Practice timed drills to improve speed.")
    if quick_questions:
        st.write(f"> You rushed through questions: {', '.join(map(str, quick_questions))}. Double-check your answers to ensure accuracy.")

    # 3. Sub-topic and Topic-wise Analysis
    st.header("3. Sub-topic and Topic-wise Analysis")
    st.write("#### Subject-wise Overview")
    subjects = questions['Subject'].unique()
    for subject in subjects:
        subj_questions = questions[questions['Subject'] == subject]
        subj_answers = [answers[i] for i in subj_questions.index]
        subj_correct = [correct_answers[i] for i in subj_questions.index]
        subj_score = sum(4 if a == c else -1 if a is not None else 0 for a, c in zip(subj_answers, subj_correct))
        total_possible = len(subj_questions) * 4
        accuracy = (subj_score / total_possible) * 100 if total_possible > 0 else 0
        mastery = "NEET Ready" if accuracy >= 80 else "On the Path" if accuracy >= 50 else "Needs Improvement"
        st.write(f"- **{subject}**: {subj_score}/{total_possible} ({accuracy:.2f}%) - **{mastery}**")

    st.write("#### Topic Distribution")
    # Placeholder for pie chart (to be implemented)

    # 4. Deep Insights
    st.header("4. Deep Insights")
    st.write("#### Question Difficulty")
    difficulties = questions['Difficulty Level'].unique()
    for diff in difficulties:
        diff_questions = questions[questions['Difficulty Level'] == diff]
        diff_answers = [answers[i] for i in diff_questions.index]
        diff_correct = [correct_answers[i] for i in diff_questions.index]
        correct = sum(1 for a, c in zip(diff_answers, diff_correct) if a == c)
        total = len(diff_questions)
        acc = (correct / total * 100) if total > 0 else 0
        st.write(f"- **{diff}**: {correct}/{total} correct ({acc:.2f}%)")
    # Add more deep insights as needed

    # 5. Improvement and Resources
    st.header("5. Improvement and Resources")
    st.write("#### Top 5 Areas to Improve")
    topics = questions.groupby('Topic').apply(
        lambda x: (sum(1 for i in x.index if answers[i] == correct_answers[i]) / len(x)) * 100
    ).sort_values().head(5)
    for topic, acc in topics.items():
        st.write(f"- **{topic}**: Accuracy {acc:.2f}% - Practice more questions on this topic.")
    st.write("**Resources:** Explore practice sets and videos online for these topics.")

# Main Function to Control Page Flow
def main():
    if 'page' not in st.session_state:
        st.session_state.page = "welcome"

    if st.session_state.page == "welcome":
        welcome_page()
    elif st.session_state.page == "main":
        main_page()
    elif st.session_state.page == "diagnostic_test":
        diagnostic_test_page()
    elif st.session_state.page == "post_test_analysis":
        post_test_analysis_page()
    elif st.session_state.page == "analytics":
        analytics_page()

if __name__ == "__main__":
    main()

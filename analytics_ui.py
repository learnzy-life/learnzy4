import streamlit as st
import pandas as pd
import altair as alt

def show_analytics_page():
    st.title("📊 Detailed Analytics")
    
    questions = st.session_state.questions
    answers = st.session_state.answers
    correct_answers = questions['Correct Answer'].tolist()
    time_per_question = st.session_state.time_per_question
    tags = st.session_state.tags if 'tags' in st.session_state else {}

    # Validate required columns
    required_columns = ['Subject', 'Time to Solve (seconds)', 'Difficulty Level', 'Topic']
    for col in required_columns:
        if col not in questions.columns:
            st.error(f"Missing column: '{col}'. Check your data source.")
            return

    # 1. Overview of the Test
    st.subheader("1️⃣ Test Performance Summary")
    correct_count = sum(1 for i in range(40) if answers[i] == correct_answers[i])
    accuracy = (correct_count / 40) * 100
    st.metric("✅ Correct Answers", f"{correct_count}/40")
    st.metric("📊 Accuracy", f"{accuracy:.2f}%")
    
    total_time = sum(time_per_question.values())
    st.metric("⏳ Total Time Taken", f"{total_time // 60:.0f} min {total_time % 60:.0f} sec")

    # 2. Time Management Visualization
    st.subheader("2️⃣ Time Management Breakdown")
    
    time_data = pd.DataFrame({
        'Question': range(1, 41),
        'Your Time': [time_per_question[i] for i in range(40)],
        'Ideal Time': questions['Time to Solve (seconds)'],
        'Subject': questions['Subject']
    })

    chart = alt.Chart(time_data).mark_bar().encode(
        x='Question:N',
        y=alt.Y('Your Time:Q', title='Time Spent (seconds)'),
        color=alt.Color('Subject:N', legend=alt.Legend(title="Subject")),
        tooltip=['Question', 'Your Time', 'Ideal Time', 'Subject']
    ).interactive()

    st.altair_chart(chart, use_container_width=True)

    # 3. Subject-wise Performance
    st.subheader("3️⃣ Subject-Wise Performance")

    subject_data = time_data.groupby('Subject').agg(
        Total_Time=('Your Time', 'sum'),
        Avg_Time=('Your Time', 'mean'),
        Total_Questions=('Question', 'count')
    ).reset_index()

    st.dataframe(subject_data)

    # 4. Recommendations
    st.subheader("💡 Recommendations")
    if accuracy < 60:
        st.warning("Improve accuracy by reviewing incorrect answers.")
    if total_time > 2400:
        st.warning("Time management needs improvement. Try timed practice tests.")


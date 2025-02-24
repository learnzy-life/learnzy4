import streamlit as st
import pandas as pd
import altair as alt
import time
import openai

# Initialize OpenAI (add your API key)
from openai import OpenAI

client = OpenAI(
  api_key="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"
)

completion = client.chat.completions.create(
  model="gpt-4o-mini",
  store=True,
  messages=[
    {"role": "user", "content": "write a haiku about ai"}
  ]
)

print(completion.choices[0].message);


# --- Utility Functions ---
def fetch_data(gid):
    base_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQtG0QdIu8N1BPgVHeYDArIRCwvMV7NmN_YUM3_UUwU2FkmMYhJTtDxoS2Lk7kX6LNJHnLlAdgLSWPx/pub?gid={}&single=true&output=csv"
    try:
        df = pd.read_csv(base_url.format(gid))
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Data loading error: {str(e)}")
        return None

def generate_ai_insight(context, prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{
                "role": "system",
                "content": "You are a NEET preparation expert. Provide concise, actionable feedback."
            }, {
                "role": "user",
                "content": f"{context}\n\n{prompt}"
            }]
        )
        return response.choices[0].message.content
    except Exception as e:
        return "AI insights currently unavailable."

# --- Time Management Section ---
def time_management_section(questions, time_per_question):
    st.header("⏱ Time Management Analysis")
    
    # Calculate time metrics
    total_time = sum(time_per_question.values())
    ideal_time = questions['Time to Solve (seconds)'].sum()
    time_diff = total_time - ideal_time
    
    # AI-generated summary
    time_context = f"""
    Student took {total_time//60} minutes vs ideal {ideal_time//60} minutes.
    Difference: {abs(time_diff)//60} minutes {"over" if time_diff >0 else "under"}.
    """
    time_insight = generate_ai_insight(time_context, "Provide time management analysis for NEET preparation.")
    
    # Metrics columns
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Your Total Time", f"{total_time//60}min {total_time%60:.0f}sec")
    with col2:
        st.metric("Ideal Time", f"{ideal_time//60}min {ideal_time%60:.0f}sec")
    with col3:
        st.metric("Difference", f"{abs(time_diff)//60}min {abs(time_diff)%60:.0f}sec {'+' if time_diff>0 else '-'}")
    
    st.write(f"**AI Insight:** {time_insight}")
    
    # Enhanced time comparison chart
    time_data = pd.DataFrame({
        'Question': questions.index + 1,
        'Your Time': [time_per_question[i] for i in range(40)],
        'Ideal Time': questions['Time to Solve (seconds)'],
        'Subject': questions['Subject'],
        'Difficulty': questions['Difficulty Level']
    })
    
    chart = alt.Chart(time_data).transform_fold(
        ['Your Time', 'Ideal Time'],
        as_=['Type', 'Time']
    ).mark_bar().encode(
        x='Question:N',
        y='Time:Q',
        color=alt.Color('Type:N', scale=alt.Scale(range=['#1f77b4', '#2ca02c'])),
        tooltip=['Subject', 'Difficulty', 'Your Time', 'Ideal Time'],
        column='Subject:N'
    ).properties(width=200, height=200)
    
    st.altair_chart(chart)

# --- Deep Insights Section with AI ---
def deep_insights_section(questions, answers, correct_answers):
    st.header("🔍 Deep Learning Analysis")
    
    # --- Deep Insights Section with AI ---
def deep_insights_section(questions, answers, correct_answers):
    st.header("🔍 Deep Learning Analysis")
    
    # Difficulty analysis
    diff_analysis = questions.groupby('Difficulty Level').apply(
        lambda x: (sum(answers[i] == correct_answers[i] for i in x.index) / len(x)
    ).reset_index(name='Accuracy')
    
    # Bloom's Taxonomy analysis
    bloom_analysis = questions.groupby('Bloom’s Taxonomy').apply(
        lambda x: (sum(answers[i] == correct_answers[i] for i in x.index) / len(x)
    ).reset_index(name='Accuracy')  # Fixed missing parenthesis here
    
    # Generate AI insights
    insight_context = f"""
    Performance by Difficulty:\n{diff_analysis.to_string()}
    \nPerformance by Bloom's Level:\n{bloom_analysis.to_string()}
    """
    ai_insight = generate_ai_insight(insight_context, "Provide cognitive performance analysis for NEET preparation.")
    
    # Visualization
    col1, col2 = st.columns(2)
    with col1:
        st.altair_chart(alt.Chart(diff_analysis).mark_bar().encode(
            x='Difficulty Level',
            y='Accuracy',
            color='Difficulty Level'
        ))
    with col2:
        st.altair_chart(alt.Chart(bloom_analysis).mark_bar().encode(
            x='Bloom’s Taxonomy',
            y='Accuracy',
            color='Bloom’s Taxonomy'
        ))
    
    st.write(f"**Cognitive Insight:** {ai_insight}")

# --- Enhanced Improvement Section ---
def improvement_section(questions, answers, correct_answers):
    st.header("🚀 Improvement Plan")
    
    # Calculate weak areas
    weak_topics = questions.groupby('Topic').apply(
        lambda x: (sum(answers[i] != correct_answers[i] for i in x.index)/len(x)
    ).sort_values(ascending=False).head(5)
    
    # Generate AI recommendations
    topics_list = "\n".join([f"- {topic}: {score*100:.1f}% incorrect" 
                           for topic, score in weak_topics.items()])
    ai_recommendation = generate_ai_insight(
        f"Student needs help with:\n{topics_list}",
        "Create a 5-point NEET improvement plan"
    )
    
    # Display recommendations
    st.subheader("AI-Powered Action Plan")
    st.write(ai_recommendation)
    
    # Resource links
    st.subheader("Recommended Resources")
    for topic in weak_topics.index:
        with st.expander(f"📚 Resources for {topic}"):
            st.write(f"**Practice Questions:** [Link to {topic} questions](https://example.com)")
            st.write(f"**Video Lectures:** [Watch {topic} tutorials](https://example.com)")
            st.write(f"**Study Notes:** [Download {topic} notes](https://example.com)")

# --- Updated Analytics Page ---
def analytics_page():
    st.title("📈 Advanced Performance Analytics")
    
    # Load data from session state
    questions = st.session_state.questions
    answers = st.session_state.answers
    time_per_question = st.session_state.time_per_question
    correct_answers = questions['Correct Answer'].tolist()
    
    # Section 1: Time Management
    time_management_section(questions, time_per_question)
    
    # Section 2: Deep Insights
    deep_insights_section(questions, answers, correct_answers)
    
    # Section 3: Improvement Plan
    improvement_section(questions, answers, correct_answers)

# (Rest of the code remains similar with proper section imports)

import streamlit as st
import pandas as pd
from os import path
from json import load
from utils.local_store import LOCAL_STATE_PATH
from plotly import graph_objects as go

# Load tracking state from file if exists
if path.exists(LOCAL_STATE_PATH):
    with open(LOCAL_STATE_PATH, "r") as f:
        tracking_data = load(f)
        st.session_state.update(tracking_data)

st.title("📊 Replay Live Spread from CSV")

# --- Upload CSV ---
uploaded_file = st.file_uploader("Upload Your CSV File", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.subheader("📋 Data Preview")
    st.dataframe(df.head())
    event_name = df["event_name"].iloc[0] if "event_name" in df.columns else "Live Spread Replay"

    st.subheader("⚙️ Configure Plot Parameters")
    home_score = st.number_input("Home Team Final Score", value=0, step=1)
    away_score = st.number_input("Away Team Final Score", value=0, step=1)
    home_or_away = st.radio("Recorded team", ["home", "away"])
    initial_spread = st.number_input("Initial Spread", value=0.0, format="%.1f")

    if st.button("📈 Generate Graph"):
        # Calculate push line based on final score
        push_line = 0
        if home_or_away == "home":
            push_line = (home_score - away_score) * -1
        else:
            push_line = home_score - away_score

        # --- Plotting logic ---
        gplaceholder = st.empty()  # persistent container

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df["time_since_start"],
            y=df["spread"],
            mode='lines+markers',
            name='Live Spread',
            customdata=df[["price", "status"]],
            hovertemplate=(
                "<b>Time:</b> %{x}<br>"
                "<b>Spread:</b> %{y}<br>"
                "<b>Price:</b> %{customdata[0]}<br>"
                "<extra></extra>"
            )
        ))

        # Initial spread line
        fig.add_trace(go.Scatter(
            x=[df["time_since_start"].iloc[0], df["time_since_start"].iloc[-1]],
            y=[initial_spread, initial_spread],
            mode="lines",
            name="Initial Spread",
            line=dict(dash="dot", color="yellow"),
            hovertemplate="<b>Initial Spread:</b> %{y}<extra></extra>"
        ))

        # Push line from final score
        fig.add_trace(go.Scatter(
            x=[df["time_since_start"].iloc[0], df["time_since_start"].iloc[-1]],
            y=[push_line, push_line],
            mode="lines",
            name="Push Line",
            line=dict(dash="dash", color="green"),
            hovertemplate="<b>Push Line:</b> %{y}<extra></extra>"
        ))

        fig.add_annotation(
            x=df["time_since_start"].iloc[-1],  # rightmost point of the x-axis
            y=push_line,  # y-coordinate of the push line
            text="Bets above the push line are winning bets",
            showarrow=False,
            font=dict(size=12, color="green"),
            bgcolor="rgba(255,255,255,0.7)",  # optional semi-transparent background
            bordercolor="green",
            borderwidth=1,
            align="center"
        )

        fig.update_layout(
            title=f"Replay of {event_name} - {home_or_away.upper()}",
            xaxis_title="Time",
            yaxis_title="Spread",
            template="plotly_white",
            showlegend=True
        )

        gplaceholder.plotly_chart(fig, width='stretch')
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import re
from google import genai

# ===============================
# 🔑 ВСТАВЬ СЮДА СВОЙ КЛЮЧ
# ===============================
client = genai.Client(api_key="AIzaSyBAJ4SZa32qGpg8LlQOEDrNcXfOq4ksUnU")

# ===============================
# 🎨 ДИЗАЙН
# ===============================
st.set_page_config(page_title="AI Conflict Resolver", layout="centered")

st.markdown("""
<style>
.stApp { background-color: #FDF6E3; }
h1, h2, h3, p, span, label { color: #1D2671 !important; font-family: Arial; }
.stButton>button {
background-color: #1D2671 !important;
color: white !important;
border-radius: 10px;
height: 3em;
font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# ===============================
# 🧠 AI ФУНКЦИЯ (С ЗАЩИТОЙ)
# ===============================
@st.cache_data(show_spinner=False)
def ask_ai(conflict_text):

    if not conflict_text.strip():
        return None

    prompt = f"""
    Analyze this conflict:
    {conflict_text}

    Create a 2x2 payoff matrix.

    IMPORTANT:
    - Return ONLY valid JSON
    - Matrix format strictly:
      [[[3,3],[1,4]],[[4,1],[2,2]]]
    - Use numbers only

    Format:
    {{
        "players": ["Player1","Player2"],
        "strategies_p1": ["S1","S2"],
        "strategies_p2": ["T1","T2"],
        "matrix": [[[3,3],[1,4]],[[4,1],[2,2]]],
        "nash": ["S2","T2"],
        "pareto": ["S1","T1"],
        "analysis": "Short explanation"
    }}
    """

    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )

        text = response.text

        match = re.search(r'\{.*\}', text, re.DOTALL)
        if not match:
            return None

        data = json.loads(match.group())

        return data

    except Exception as e:
        if "429" in str(e):
            st.error("⏳ Превышен лимит Gemini. Подождите 1 минуту.")
        else:
            st.error(f"Ошибка AI: {e}")
        return None

# ===============================
# SESSION STATE
# ===============================
if "step" not in st.session_state:
    st.session_state.step = 1

# ===============================
# ЭТАП 1 — ВВОД
# ===============================
if st.session_state.step == 1:

    st.title("AI Conflict Resolver")
    conflict = st.text_area("Describe the conflict between two players")

    col1, col2, col3 = st.columns(3)

    if col1.button("🎮 Game"):

        result = ask_ai(conflict)

        if result:
            st.session_state.data = result
            st.session_state.step = 2
            st.rerun()
        else:
            st.warning("AI не смог создать игру. Попробуйте снова.")

    if col2.button("⚖ Nash Equilibrium"):

        result = ask_ai(conflict)

        if result:
            st.success(f"Nash Equilibrium: {result['nash']}")
            st.write(result["analysis"])

    if col3.button("🌍 Pareto Optimum"):

        result = ask_ai(conflict)

        if result:
            st.info(f"Pareto Optimal: {result['pareto']}")
            st.write(result["analysis"])

# ===============================
# ЭТАП 2 — МАТРИЦА
# ===============================
elif st.session_state.step == 2:

    if "data" not in st.session_state or st.session_state.data is None:
        st.error("Нет данных. Вернитесь назад.")
        st.stop()

    data = st.session_state.data

    st.subheader("Payoff Matrix")

    df = pd.DataFrame(
        data["matrix"],
        index=data["strategies_p1"],
        columns=data["strategies_p2"]
    )

    st.table(df)

    choice = st.radio("Choose your strategy:", data["strategies_p1"])

    if st.button("Confirm Choice"):
        st.session_state.choice = choice
        st.session_state.step = 3
        st.rerun()

# ===============================
# ЭТАП 3 — АНАЛИЗ
# ===============================
elif st.session_state.step == 3:

    data = st.session_state.data
    choice = st.session_state.choice

    opponent = data["nash"][1]

    st.write("You chose:", choice)
    st.write("AI chooses:", opponent)

    if choice == data["nash"][0]:
        st.success("✅ Это равновесие Нэша")
        score = 90
    else:
        st.error("❌ Это не равновесие Нэша")
        score = 40

    # График выгод
    flat = []
    for row in data["matrix"]:
        for cell in row:
            flat.append(cell[0])

    fig = px.bar(
        x=["O1","O2","O3","O4"],
        y=flat,
        color=flat,
        color_continuous_scale="Blues",
        title="Payoff Distribution (Player 1)"
    )

    st.plotly_chart(fig)

    if st.button("Final Analysis"):
        st.session_state.score = score
        st.session_state.step = 4
        st.rerun()

# ===============================
# ЭТАП 4 — ФИНАЛ
# ===============================
elif st.session_state.step == 4:

    data = st.session_state.data
    score = st.session_state.score

    st.subheader("Final Analysis")

    st.write("Nash:", data["nash"])
    st.write("Pareto:", data["pareto"])
    st.write(data["analysis"])

    gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={'text': "Strategic Score"},
        gauge={'axis': {'range': [0, 100]},
               'bar': {'color': "#1D2671"}}
    ))

    st.plotly_chart(gauge)

    if st.button("Start Over"):
        st.session_state.clear()
        st.rerun()


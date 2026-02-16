import streamlit as st
import pandas as pd
from openai import OpenAI
import json
import plotly.express as px

# Твой рабочий ключ OpenAI
client = OpenAI(api_key="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")

st.set_page_config(page_title="Nash Balance", layout="centered")

# Дизайн
st.markdown("""
    <style>
    .stApp { background-color: #FDFCEE; }
    h1, h2, h3, p { color: #1D2671 !important; }
    .stButton>button { background-color: #1D2671 !important; color: white !important; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

if 'step' not in st.session_state: st.session_state.step = 'welcome'

if st.session_state.step == 'welcome':
    st.title("Nash Balance AI 🤖")
    st.write("Стратегический анализ через ChatGPT")
    if st.button("НАЧАТЬ"):
        st.session_state.step = 'input'
        st.rerun()

elif st.session_state.step == 'input':
    problem = st.text_area("Опишите ситуацию:", height=150)
    if st.button("СОЗДАТЬ МОДЕЛЬ"):
        if problem:
            with st.spinner("ChatGPT вычисляет..."):
                try:
                    # ... внутри блока обработки нажатия кнопки ...
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "Ты эксперт по теории игр. Отвечай ТОЛЬКО на русском языке в формате JSON."},
                            {"role": "user", "content": f"Ситуация: {problem}. Создай игру 2x2. Ответь JSON: {{\"s1\":\"Стр1\",\"s2\":\"Стр2\",\"m\":[[\"(10,10)\",\"(0,15)\"],[\"(15,0)\",\"(5,5)\"]],\"nash\":\"описание\"}}"}
                        ],
                        response_format={ "type": "json_object" }
                    )
                    st.session_state.data = json.loads(response.choices[0].message.content)
                    st.session_state.step = 'result'
                    st.rerun()
                except Exception as e:
                    st.error(f"Ошибка: {e}")

elif st.session_state.step == 'result':
    d = st.session_state.data
    st.table(pd.DataFrame(d['m'], index=[d['s1'], d['s2']], columns=[d['s1'], d['s2']]))
    st.info(d['nash'])
    if st.button("В НАЧАЛО"):
        st.session_state.step = 'welcome'
        st.rerun()



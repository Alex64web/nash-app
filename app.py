import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from openai import OpenAI
import json

# Настройка клиента
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Стили
st.set_page_config(page_title="Conflict Resolver Pro", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #F5F5DC; }
    h1, h2, h3, p, label { color: #2C3E50 !important; }
    .stButton>button { background-color: #4682B4 !important; color: white !important; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

# Инициализация состояний
if 'step' not in st.session_state: st.session_state.step = 0
if 'history' not in st.session_state: st.session_state.history = []
if 'game_data' not in st.session_state: st.session_state.game_data = None

def get_ai_response(prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": "Ты эксперт по теории игр и геополитике. Отвечай только JSON."},
                      {"role": "user", "content": prompt}],
            response_format={ "type": "json_object" }
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        st.error(f"Ошибка ИИ: {e}")
        return None

# --- ЗАГОЛОВОК ---
st.title("🕊️ Conflict Analytics: Nash & Pareto")

# --- ПАНЕЛЬ ВВОДА ---
problem = st.text_area("Опишите конфликт (страны, логистика, ресурсы):", placeholder="Например: Спор двух стран за пролив и торговые пути...")

col1, col2, col3 = st.columns(3)

# КНОПКА 1: ИГРА (6 ЭТАПОВ)
if col1.button("🎮 НАЧАТЬ ИГРУ"):
    prompt = f"Ситуация: {problem}. Создай пошаговую игру на 6 этапов. Для текущего этапа 1 дай 2 варианта выбора для Игрока 1. Один ведет к Равновесию Нэша, другой нет. Опиши последствия для логистики. Ответ JSON: {{'stage':1, 'options':[{{'text':'вариант1','is_nash':true, 'impact':[8,4]}}, {{'text':'вариант2','is_nash':false, 'impact':[2,9]}}]}}"
    st.session_state.game_data = get_ai_response(prompt)
    st.session_state.step = 1
    st.session_state.history = []

# КНОПКА 2: РАВНОВЕСИЕ НЭША
if col2.button("📊 РАВНОВЕСИЕ НЭША"):
    res = get_ai_response(f"Дай подробный анализ Равновесия Нэша для: {problem}. Ответ JSON: {{'analysis':'текст'}}")
    st.info(res['analysis'])

# КНОПКА 3: ПАРЕТО ОПТИМУМ
if col3.button("💎 ПАРЕТО ОПТИМУМ"):
    res = get_ai_response(f"Найди Парето-оптимальное решение для: {problem}. Ответ JSON: {{'analysis':'текст'}}")
    st.success(res['analysis'])

# --- ИГРОВОЙ ПРОЦЕСС ---
if st.session_state.step > 0 and st.session_state.game_data:
    st.divider()
    st.subheader(f"Этап {st.session_state.step} из 6")
    
    data = st.session_state.game_data
    opts = data['options']
    
    # Выбор игрока
    for i, opt in enumerate(opts):
        if st.button(f"Выбрать: {opt['text']}", key=f"opt_{i}"):
            # Логика комментария
            comment = "✅ Это Равновесие Нэша!" if opt['is_nash'] else "❌ Это не Равновесие (рискованный или невыгодный шаг)."
            st.session_state.history.append({'step': st.session_state.step, 'impact': opt['impact'], 'comment': comment})
            
            if st.session_state.step < 6:
                st.session_state.step += 1
                # Загружаем следующий этап
                st.session_state.game_data = get_ai_response(f"Ситуация: {problem}. Предыдущий шаг был {opt['text']}. Дай 2 варианта для этапа {st.session_state.step}...")
                st.rerun()
            else:
                st.session_state.step = 7 # Конец

# --- ГРАФИКИ И АНАЛИЗ ---
if st.session_state.history:
    st.divider()
    st.subheader("Анализ динамики конфликта")
    
    # Подготовка данных для графика
    steps = [h['step'] for h in st.session_state.history]
    val1 = [h['impact'][0] for h in st.session_state.history]
    val2 = [h['impact'][1] for h in st.session_state.history]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=steps, y=val1, name="Ресурс Страны А", line=dict(color='#4682B4', width=4)))
    fig.add_trace(go.Scatter(x=steps, y=val2, name="Ресурс Страны Б", line=dict(color='#E97451', width=4)))
    fig.update_layout(title="Изменение ресурсов и логистики", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)
    
    for h in st.session_state.history:
        st.write(f"**Шаг {h['step']}:** {h['comment']}")

if st.session_state.step == 7:
    st.balloons()
    st.success("Игра завершена! Выше представлен полный анализ ваших решений.")
    if st.button("СБРОС"):
        st.session_state.step = 0
        st.rerun()


import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from openai import OpenAI
import json

# Прямой ввод ключа через секреты
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Настройка страницы
st.set_page_config(page_title="Conflict Resolver Pro", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #F5F5DC; }
    h1, h2, h3, p, label, .stMarkdown { color: #2C3E50 !important; }
    .stButton>button { background-color: #4682B4 !important; color: white !important; border-radius: 8px; width: 100%; }
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
            messages=[
                {"role": "system", "content": "Ты эксперт по теории игр. Отвечай ТОЛЬКО в формате JSON. Не пиши лишнего текста."},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" }
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        st.error(f"Ошибка связи с ИИ: {e}")
        return None

st.title("🕊️ Conflict Analytics: Nash & Pareto")

problem = st.text_area("Опишите конфликт (страны, логистика, ресурсы):", 
                       placeholder="Например: Спор из-за ресурсов или территориальный конфликт...")

col1, col2, col3 = st.columns(3)

# --- ИГРА ---
if col1.button("🎮 НАЧАТЬ ИГРУ"):
    st.session_state.step = 1
    st.session_state.history = []
    with st.spinner("Загрузка этапа 1..."):
        # Промпт с жестким условием для графиков
        prompt = f"""Ситуация: {problem}. Этап 1 из 3. Дай 2 варианта выбора. 
        ПРАВИЛО ДЛЯ ОЧКОВ (impact):
        1. Если вариант - Равновесие Нэша (is_nash: true), очки сторон должны быть ОДИНАКОВЫМИ (например [10, 10]), чтобы линии сошлись.
        2. Если вариант НЕ равновесие (is_nash: false), сделай ОГРОМНЫЙ РАЗРЫВ в очках (например [15, 2]), чтобы линии разошлись.
        JSON формат: {{'stage':1, 'options':[{{'text':'вариант1','is_nash':true, 'impact':[10,10]}}, {{'text':'вариант2','is_nash':false, 'impact':[15,2]}}]}}"""
        st.session_state.game_data = get_ai_response(prompt)
    st.rerun()

# --- РАВНОВЕСИЕ НЭША ---
if col2.button("📊 РАВНОВЕСИЕ НЭША"):
    if not problem:
        st.warning("Сначала опишите ситуацию!")
    else:
        with st.spinner("Анализ Нэша..."):
            nash_prompt = f"""Проанализируй конфликт: {problem}. Представь его как игру 2x2. JSON:
            {{ "p1_name": "Игрок 1", "p2_name": "Игрок 2", "strategies": ["А", "Б"],
               "m11": [10, 10], "m12": [0, 15], "m21": [15, 0], "m22": [5, 5], "explanation": "текст" }}"""
            res = get_ai_response(nash_prompt)
            if res:
                s1, s2 = res['strategies'][0], res['strategies'][1]
                p1, p2 = res['p1_name'], res['p2_name']
                matrix_data = { f"{p2}: {s1}": [str(res['m11']), str(res['m21'])], f"{p2}: {s2}": [str(res['m12']), str(res['m22'])] }
                df = pd.DataFrame(matrix_data, index=[f"{p1}: {s1}", f"{p1}: {s2}"])
                st.table(df)
                st.info(f"**Анализ:** {res['explanation']}")

# --- ПАРЕТО ---
if col3.button("💎 ПАРЕТО ОПТИМУМ"):
    with st.spinner("Поиск Парето..."):
        res = get_ai_response(f"Найди Парето-оптимальное решение для: {problem}. Отвечай текстом на русском. JSON: {{'analysis':'текст'}}")
        if res: st.success(res.get('analysis', 'Ошибка анализа'))

# Основная логика игры (3 этапа)
if 0 < st.session_state.step <= 3:
    if st.session_state.game_data and 'options' in st.session_state.game_data:
        st.divider()
        st.subheader(f"Этап {st.session_state.step} из 3")
        
        opts = st.session_state.game_data['options']
        c1, c2 = st.columns(2)
        for i, opt in enumerate(opts):
            with [c1, c2][i]:
                if st.button(opt['text'], key=f"btn_{st.session_state.step}_{i}"):
                    comment = "✅ Равновесие (Линии сошлись!)" if opt['is_nash'] else "❌ Не равновесие (Линии разошлись!)"
                    st.session_state.history.append({'step': st.session_state.step, 'impact': opt['impact'], 'comment': comment})
                    
                    if st.session_state.step < 3:
                        st.session_state.step += 1
                        with st.spinner("Подготовка следующего этапа..."):
                            new_prompt = f"""Ситуация: {problem}. Этап {st.session_state.step} из 3. Предыдущий выбор: {opt['text']}.
                            ДАЙ 2 ВАРИАНТА. ПРАВИЛО ОЧКОВ:
                            - is_nash: true -> impact [ОДИНАКОВЫЕ числа]
                            - is_nash: false -> impact [РАЗНЫЕ числа, разница > 10]
                            JSON: {{'options':[{{'text':'...','is_nash':true, 'impact':[20,20]}}, ...]}}"""
                            st.session_state.game_data = get_ai_response(new_prompt)
                        st.rerun()
                    else:
                        st.session_state.step = 4
                        st.rerun()

# --- ГРАФИК (сближение/расхождение) ---
if st.session_state.history:
    st.divider()
    st.subheader("Визуализация стратегии")
    
    steps = [f"Этап {h['step']}" for h in st.session_state.history]
    val_a = [h['impact'][0] for h in st.session_state.history]
    val_b = [h['impact'][1] for h in st.session_state.history]
    
    fig = go.Figure()
    # Линия Игрока А
    fig.add_trace(go.Scatter(x=steps, y=val_a, name="Выгода Стороны А", 
                             line=dict(color='#4682B4', width=4, shape='spline')))
    # Линия Игрока Б
    fig.add_trace(go.Scatter(x=steps, y=val_b, name="Выгода Стороны Б", 
                             line=dict(color='#E97451', width=4, shape='spline')))
    
    fig.update_layout(
        hovermode="x unified",
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(title="Уровень выгоды (баллы)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)

    for h in st.session_state.history:
        st.write(f"**{steps[h['step']-1]}:** {h['comment']}")

if st.session_state.step == 4:
    st.balloons()
    st.success("🎉 Игра окончена. Посмотрите на график: точки пересечения — это ваши успешные компромиссы.")
    if st.button("Начать заново"):
        st.session_state.step = 0
        st.rerun()

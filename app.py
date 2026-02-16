import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from openai import OpenAI
import json
import re

# Прямой ввод ключа (как мы договорились, это самый быстрый путь)
client = OpenAI(api_key="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")

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
                {"role": "system", "content": "Ты эксперт по теории игр. Отвечай ТОЛЬКО в формате JSON. Не пиши лишнего текста до или после JSON."},
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
                       placeholder="Например: Спор из-за обиды ребенка или территориальный конфликт...")

col1, col2, col3 = st.columns(3)

if col1.button("🎮 НАЧАТЬ ИГРУ"):
    st.session_state.step = 1
    st.session_state.history = []
    with st.spinner("Загрузка этапа 1..."):
        prompt = f"Ситуация: {problem}. Этап 1 из 6. Дай 2 варианта выбора. Один - равновесие Нэша, другой - нет. JSON формат: {{'stage':1, 'options':[{{'text':'вариант1','is_nash':true, 'impact':[8,4]}}, {{'text':'вариант2','is_nash':false, 'impact':[2,9]}}]}}"
        st.session_state.game_data = get_ai_response(prompt)
    st.rerun()

if col2.button("📊 РАВНОВЕСИЕ НЭША"):
    with st.spinner("Анализ Нэша..."):
        res = get_ai_response(f"Дай подробный анализ Равновесия Нэша для: {problem}. Ответ JSON: {{'analysis':'текст'}}")
        if res: st.info(res.get('analysis', 'Ошибка анализа'))

if col3.button("💎 ПАРЕТО ОПТИМУМ"):
    with st.spinner("Поиск Парето..."):
        res = get_ai_response(f"Найди Парето-оптимальное решение для: {problem}. Ответ JSON: {{'analysis':'текст'}}")
        if res: st.success(res.get('analysis', 'Ошибка анализа'))

# Основная логика игры
if st.session_state.step > 0 and st.session_state.step <= 6:
    if st.session_state.game_data and 'options' in st.session_state.game_data:
        st.divider()
        st.subheader(f"Этап {st.session_state.step} из 6")
        
        opts = st.session_state.game_data['options']
        
        c1, c2 = st.columns(2)
        for i, opt in enumerate(opts):
            with [c1, c2][i]:
                if st.button(opt['text'], key=f"btn_{st.session_state.step}_{i}"):
                    comment = "✅ Это Равновесие Нэша!" if opt['is_nash'] else "❌ Это не Равновесие."
                    st.session_state.history.append({'step': st.session_state.step, 'impact': opt['impact'], 'comment': comment})
                    
                    if st.session_state.step < 6:
                        st.session_state.step += 1
                        with st.spinner(f"Подготовка этапа {st.session_state.step}..."):
                            new_prompt = f"Ситуация: {problem}. Мы на этапе {st.session_state.step} из 6. Предыдущий выбор: {opt['text']}. Дай новые 2 варианта в формате JSON: {{'options':[{{'text':'...','is_nash':true, 'impact':[5,5]}}, ...]}}"
                            st.session_state.game_data = get_ai_response(new_prompt)
                        st.rerun()
                    else:
                        st.session_state.step = 7
                        st.rerun()
    else:
        st.warning("ИИ не смог сгенерировать варианты. Попробуйте нажать кнопку еще раз.")

# Графики и финал
if st.session_state.history:
    st.divider()
    # Отрисовка графика (Plotly)
    steps = [h['step'] for h in st.session_state.history]
    val_a = [h['impact'][0] for h in st.session_state.history]
    val_b = [h['impact'][1] for h in st.session_state.history]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=steps, y=val_a, name="Игрок А", line=dict(color='#4682B4', width=3)))
    fig.add_trace(go.Scatter(x=steps, y=val_b, name="Игрок Б", line=dict(color='#E97451', width=3)))
    st.plotly_chart(fig, use_container_width=True)

    for h in st.session_state.history:
        st.write(f"**Этап {h['step']}:** {h['comment']}")

if st.session_state.step == 7:
    st.success("🎉 Анализ завершен! Вы прошли все 6 этапов.")
    if st.button("Начать заново"):
        st.session_state.step = 0
        st.rerun()


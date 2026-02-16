import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from openai import OpenAI
import json

# Прямой ввод ключа
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

st.title("🕊️ Conflict Analytics: 3-Step Strategy")

problem = st.text_area("Опишите ситуацию:", placeholder="Например: Спор из-за ресурсов или логистики...")

col1, col2, col3 = st.columns(3)

if col1.button("🎮 НАЧАТЬ ИГРУ"):
    st.session_state.step = 1
    st.session_state.history = []
    with st.spinner("Загрузка этапа 1..."):
        # Изменили промпт на 3 этапа
        prompt = f"Ситуация: {problem}. Этап 1 из 3. Дай 2 варианта выбора. Один - равновесие Нэша, другой - нет. JSON: {{'stage':1, 'options':[{{'text':'вариант1','is_nash':true, 'impact':[8,4]}}, {{'text':'вариант2','is_nash':false, 'impact':[2,9]}}]}}"
        st.session_state.game_data = get_ai_response(prompt)
    st.rerun()

if col2.button("📊 РАВНОВЕСИЕ НЭША"):
    with st.spinner("Анализ Нэша..."):
        res = get_ai_response(f"Дай подробный анализ Равновесия Нэша для: {problem}. Отвечай текстом на русском языке.")
        if res:
            # Если ИИ вернул словарь, берем значение по ключу, если строку - выводим строку
            text = res.get('analysis') if isinstance(res, dict) else res
            st.info(f"### Анализ Равновесия Нэша\n{text}")

if col3.button("💎 ПАРЕТО ОПТИМУМ"):
    with st.spinner("Поиск Парето..."):
        res = get_ai_response(f"Найди Парето-оптимальное решение для: {problem}. Отвечай текстом на русском языке.")
        if res:
            text = res.get('analysis') if isinstance(res, dict) else res
            st.success(f"### Парето-оптимальный вариант\n{text}")

# Основная логика игры (теперь до 3)
if 0 < st.session_state.step <= 3:
    if st.session_state.game_data and 'options' in st.session_state.game_data:
        st.divider()
        st.subheader(f"Этап {st.session_state.step} из 3")
        
        opts = st.session_state.game_data['options']
        c1, c2 = st.columns(2)
        
        for i, opt in enumerate(opts):
            with [c1, c2][i]:
                if st.button(opt['text'], key=f"btn_{st.session_state.step}_{i}"):
                    comment = "✅ Равновесие Нэша" if opt['is_nash'] else "❌ Не равновесие"
                    st.session_state.history.append({'step': st.session_state.step, 'impact': opt['impact'], 'comment': comment})
                    
                    if st.session_state.step < 3: # Условие перехода теперь до 3
                        st.session_state.step += 1
                        with st.spinner(f"Подготовка этапа {st.session_state.step}..."):
                            new_prompt = f"Ситуация: {problem}. Этап {st.session_state.step} из 3. Предыдущий выбор: {opt['text']}. Дай 2 варианта JSON: {{'options':[{{'text':'...','is_nash':true, 'impact':[5,5]}}, ...]}}"
                            st.session_state.game_data = get_ai_response(new_prompt)
                        st.rerun()
                    else:
                        st.session_state.step = 4 # Финал наступает после 3-го шага
                        st.rerun()
    else:
        st.warning("Нажмите кнопку 'Начать игру'")

# Графики
if st.session_state.history:
    st.divider()
    steps = [h['step'] for h in st.session_state.history]
    val_a = [h['impact'][0] for h in st.session_state.history]
    val_b = [h['impact'][1] for h in st.session_state.history]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=steps, y=val_a, name="Выгода А", line=dict(color='#4682B4', width=3)))
    fig.add_trace(go.Scatter(x=steps, y=val_b, name="Выгода Б", line=dict(color='#E97451', width=3)))
    st.plotly_chart(fig, use_container_width=True)

    for h in st.session_state.history:
        st.write(f"**Этап {h['step']}:** {h['comment']}")

if st.session_state.step == 4:
    st.success("🎉 Анализ завершен! 3 этапа пройдены.")
    if st.button("Начать заново"):
        st.session_state.step = 0
        st.rerun()



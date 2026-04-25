import streamlit as st
import pandas as pd
from datetime import date

from db import init_db, upsert_record, get_all_records, get_last_7_days, delete_record
from summary import generate_summary

init_db()

st.set_page_config(page_title="FitMore", page_icon="💪", layout="centered")

st.markdown("""
<style>
html, body, [class*="css"] { font-family: 'Segoe UI', sans-serif; }
.block-container { padding-top: 2rem; max-width: 780px; }
.hero { text-align: center; padding: 1.5rem 0 0.5rem; }
.hero h1 { font-size: 2rem; font-weight: 700; margin: 0; }
.hero p  { color: #888; margin: 0.25rem 0 0; font-size: 0.95rem; }
.card {
    background: #1e1e2e;
    border: 1px solid #2e2e3e;
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
}
[data-testid="metric-container"] {
    background: #1e1e2e;
    border: 1px solid #2e2e3e;
    border-radius: 10px;
    padding: 0.75rem 1rem;
}
.stButton > button { border-radius: 8px; font-weight: 600; transition: opacity .15s; }
.stButton > button:hover { opacity: 0.85; }
.stTabs [data-baseweb="tab"] { font-size: 0.95rem; font-weight: 500; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <h1>💪 FitMore</h1>
  <p>健身记录助手 · 每天进步一点点</p>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["📝 添加记录", "📋 历史记录", "📊 7 天统计", "🤖 周总结"])

# ── Tab 1: 添加记录 ──────────────────────────────────────────────
with tab1:
    with st.form("record_form", border=False):
        col_a, col_b = st.columns([2, 1])
        with col_a:
            record_date = st.date_input("日期", value=date.today())
        with col_b:
            weight = st.number_input("体重 (kg)", min_value=0.0, max_value=300.0,
                                     step=0.1, format="%.1f", value=0.0)
        workout = st.text_area("🏋️ 训练内容", placeholder="例：深蹲 5×5，卧推 4×8，跑步 30 分钟", height=90)
        diet    = st.text_area("🥗 饮食内容", placeholder="例：早餐燕麦，午餐鸡胸肉米饭，晚餐沙拉", height=90)

        col_c, col_d = st.columns(2)
        with col_c:
            cal_burned = st.number_input("🔥 消耗热量 (kcal)", min_value=0, max_value=10000,
                                         step=10, value=0,
                                         help="运动消耗 + 基础代谢，不填写留 0")
        with col_d:
            cal_intake = st.number_input("🍽️ 摄入热量 (kcal)", min_value=0, max_value=10000,
                                         step=10, value=0,
                                         help="全天饮食总热量，不填写留 0")

        note = st.text_area("📌 备注", placeholder="可选", height=68)
        submitted = st.form_submit_button("💾 保存记录", use_container_width=True, type="primary")

    if submitted:
        upsert_record(
            record_date.isoformat(),
            weight if weight > 0 else None,
            workout.strip(),
            diet.strip(),
            note.strip(),
            cal_burned if cal_burned > 0 else None,
            cal_intake if cal_intake > 0 else None,
        )
        st.success(f"✅ {record_date} 的记录已保存")

# ── Tab 2: 历史记录 ──────────────────────────────────────────────
with tab2:
    rows = get_all_records()
    if not rows:
        st.info("暂无记录，去「添加记录」tab 开始吧。")
    else:
        if "confirm_delete" not in st.session_state:
            st.session_state.confirm_delete = None
        if "editing" not in st.session_state:
            st.session_state.editing = None

        for r in rows:
            d, w, workout_txt, diet_txt, note_txt, cb, ci = r
            with st.container():
                st.markdown('<div class="card">', unsafe_allow_html=True)
                col_title, col_edit, col_del = st.columns([5, 0.6, 0.6])
                with col_title:
                    header = f"**{d}**"
                    if w:
                        header += f"　⚖️ {w} kg"
                    if cb:
                        header += f"　🔥 消耗 {cb:.0f} kcal"
                    if ci:
                        header += f"　🍽️ 摄入 {ci:.0f} kcal"
                    st.markdown(header)
                with col_edit:
                    if st.button("✏️", key=f"edit_{d}", help="编辑此记录"):
                        st.session_state.editing = d if st.session_state.editing != d else None
                with col_del:
                    if st.button("🗑️", key=f"del_{d}", help="删除此记录"):
                        st.session_state.confirm_delete = d

                if st.session_state.editing != d:
                    if workout_txt:
                        st.markdown(f"🏋️ {workout_txt}")
                    if diet_txt:
                        st.markdown(f"🥗 {diet_txt}")
                    if note_txt:
                        st.caption(f"📌 {note_txt}")
                else:
                    with st.form(key=f"edit_form_{d}", border=False):
                        e_col1, e_col2 = st.columns(2)
                        with e_col1:
                            e_weight = st.number_input("体重 (kg)", min_value=0.0, max_value=300.0,
                                                       step=0.1, format="%.1f",
                                                       value=float(w) if w else 0.0)
                        with e_col2:
                            pass
                        e_workout = st.text_area("🏋️ 训练内容", value=workout_txt or "", height=80)
                        e_diet    = st.text_area("🥗 饮食内容", value=diet_txt or "", height=80)
                        e_col3, e_col4 = st.columns(2)
                        with e_col3:
                            e_burned = st.number_input("🔥 消耗热量 (kcal)", min_value=0, max_value=10000,
                                                       step=10, value=int(cb) if cb else 0)
                        with e_col4:
                            e_intake = st.number_input("🍽️ 摄入热量 (kcal)", min_value=0, max_value=10000,
                                                       step=10, value=int(ci) if ci else 0)
                        e_note = st.text_area("📌 备注", value=note_txt or "", height=60)
                        s_col1, s_col2 = st.columns(2)
                        with s_col1:
                            save_edit = st.form_submit_button("💾 保存修改", use_container_width=True, type="primary")
                        with s_col2:
                            cancel_edit = st.form_submit_button("取消", use_container_width=True)

                    if save_edit:
                        upsert_record(
                            d,
                            e_weight if e_weight > 0 else None,
                            e_workout.strip(),
                            e_diet.strip(),
                            e_note.strip(),
                            e_burned if e_burned > 0 else None,
                            e_intake if e_intake > 0 else None,
                        )
                        st.session_state.editing = None
                        st.rerun()
                    if cancel_edit:
                        st.session_state.editing = None
                        st.rerun()

                st.markdown("</div>", unsafe_allow_html=True)
                st.divider()

        if st.session_state.confirm_delete:
            target = st.session_state.confirm_delete
            st.warning(f"确认删除 **{target}** 的记录？此操作不可撤销。")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("确认删除", type="primary", use_container_width=True):
                    delete_record(target)
                    st.session_state.confirm_delete = None
                    st.rerun()
            with c2:
                if st.button("取消", use_container_width=True):
                    st.session_state.confirm_delete = None
                    st.rerun()

# ── Tab 3: 7 天统计 ──────────────────────────────────────────────
with tab3:
    rows7 = get_last_7_days()
    if not rows7:
        st.info("最近 7 天暂无记录。")
    else:
        workout_days = sum(1 for r in rows7 if r[2] and r[2].strip())
        diet_days    = sum(1 for r in rows7 if r[3] and r[3].strip())
        weights      = [r[1] for r in rows7 if r[1] is not None]
        start_w      = weights[0] if weights else None
        end_w        = weights[-1] if weights else None
        weight_change = round(end_w - start_w, 2) if (start_w and end_w) else None

        burned_list = [r[5] for r in rows7 if r[5] is not None]
        intake_list = [r[6] for r in rows7 if r[6] is not None]
        avg_burned  = round(sum(burned_list) / len(burned_list)) if burned_list else None
        avg_intake  = round(sum(intake_list) / len(intake_list)) if intake_list else None

        last_workout = next((r[2] for r in reversed(rows7) if r[2] and r[2].strip()), "无")

        c1, c2, c3 = st.columns(3)
        c1.metric("🏋️ 训练天数", f"{workout_days} 天", f"/ {len(rows7)} 天")
        c2.metric("🥗 饮食记录", f"{diet_days} 天", f"/ {len(rows7)} 天")
        c3.metric("📅 有记录天数", f"{len(rows7)} 天")

        st.markdown("")
        c4, c5, c6 = st.columns(3)
        c4.metric("起始体重", f"{start_w} kg" if start_w else "—")
        c5.metric("最新体重", f"{end_w} kg" if end_w else "—")
        if weight_change is not None:
            c6.metric("体重变化", f"{'+' if weight_change >= 0 else ''}{weight_change} kg",
                      delta=weight_change, delta_color="inverse" if weight_change > 0 else "normal")
        else:
            c6.metric("体重变化", "—")

        st.markdown("")
        c7, c8 = st.columns(2)
        c7.metric("🔥 日均消耗热量", f"{avg_burned} kcal" if avg_burned else "—")
        c8.metric("🍽️ 日均摄入热量", f"{avg_intake} kcal" if avg_intake else "—")
        if avg_burned and avg_intake:
            diff = avg_burned - avg_intake
            sign = "+" if diff >= 0 else ""
            st.caption(f"热量缺口（消耗 - 摄入）：{sign}{diff} kcal/天")

        st.markdown(f"**最近一次训练：** {last_workout}")

        if weights:
            weight_dates = [r[0] for r in rows7 if r[1] is not None]
            df_w = pd.DataFrame({"日期": weight_dates, "体重(kg)": weights}).set_index("日期")
            st.line_chart(df_w, height=180)

        if burned_list or intake_list:
            cal_dates   = [r[0] for r in rows7 if r[5] is not None or r[6] is not None]
            cal_data = {}
            if burned_list:
                cal_data["消耗(kcal)"] = [r[5] for r in rows7 if r[5] is not None]
            if intake_list:
                cal_data["摄入(kcal)"] = [r[6] for r in rows7 if r[6] is not None]
            # 用所有有热量数据的行
            cal_rows = [r for r in rows7 if r[5] is not None or r[6] is not None]
            df_cal = pd.DataFrame({
                "日期": [r[0] for r in cal_rows],
                "消耗(kcal)": [r[5] for r in cal_rows],
                "摄入(kcal)": [r[6] for r in cal_rows],
            }).set_index("日期")
            st.line_chart(df_cal, height=180)

# ── Tab 4: 周总结 ────────────────────────────────────────────────
with tab4:
    st.markdown("调用阿里云百炼 `qwen-plus` 生成个性化中文总结。")
    if st.button("✨ 生成本周总结", type="primary", use_container_width=True):
        with st.spinner("正在生成总结..."):
            rows7 = get_last_7_days()
            summary = generate_summary(rows7)
        st.markdown(summary)

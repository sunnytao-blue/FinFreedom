import json
from datetime import datetime

import streamlit as st

from models.datamodels import InputData, SimulationResult
from modules.input_module import render_sidebar, validate_input
from modules.calculator import run_simulation
from modules.display_module import render_dashboard
from modules.io_module import (
    load_config, save_config,
    build_result_json, export_csv, export_excel,
    default_input_data,
)


st.set_page_config(
    page_title="财务自由模拟评估",
    page_icon="💰",
    layout="wide",
)

# ======== Session State 初始化 ========
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.input_data = load_config()
    st.session_state.result = None

# ======== 主界面 ========
st.title("💰 财务自由模拟评估系统")
st.markdown("---")

# ======== 侧边栏输入 ========
with st.sidebar:
    input_data = render_sidebar()

# ======== 校验 ========
errors = validate_input(input_data)
if errors:
    for err in errors:
        st.error(err)
else:
    # 判断是否需要重新计算
    prev = st.session_state.input_data
    need_recalc = bool(
        st.session_state.result is None
        or st.session_state.pop("force_recalc", False)
        or input_data.to_dict() != prev.to_dict()
    )

    if need_recalc:
        st.session_state.input_data = input_data
        with st.spinner("正在模拟计算..."):
            st.session_state.result = run_simulation(input_data)
        save_config(input_data)

    # ======== 显示结果 ========
    result: SimulationResult | None = st.session_state.result
    if result is not None:
        render_dashboard(result, input_data)

        st.markdown("---")

        # 底部操作区
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            result_json = build_result_json(input_data, result)
            st.download_button(
                "💾 保存结果",
                data=result_json,
                file_name=f"评估结果_{datetime.now():%Y%m%d}.json",
                mime="application/json",
            )
        with col2:
            if result.years:
                csv_data = export_csv(result.years)
                st.download_button(
                    "📥 导出 CSV",
                    data=csv_data,
                    file_name=f"模拟明细_{datetime.now():%Y%m%d}.csv",
                    mime="text/csv",
                )
        with col3:
            if result.years:
                xlsx_data = export_excel(result.years)
                st.download_button(
                    "📥 导出 Excel",
                    data=xlsx_data,
                    file_name=f"模拟明细_{datetime.now():%Y%m%d}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
        with col4:
            uploaded = st.file_uploader("📂 加载结果", type=["json"], key="upload_result")
            if uploaded is not None:
                try:
                    data = json.load(uploaded)
                    st.session_state.input_data = InputData.from_dict(data["input"])
                    st.session_state.result = SimulationResult.from_dict(data["result"])
                    st.rerun()
                except (json.JSONDecodeError, KeyError, TypeError) as e:
                    st.error(f"文件格式错误: {e}")

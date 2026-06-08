import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from models.datamodels import SimulationResult, InputData, SimulationYear


def render_dashboard(result: SimulationResult, input_data: InputData):
    render_summary_card(result)
    render_charts(result)
    render_yearly_table(result.years)


def render_summary_card(result: SimulationResult):
    st.markdown("""
    <style>
        [data-testid="stMetricValue"] {
            font-size: 1.4rem;
        }
        [data-testid="stMetricLabel"] {
            font-size: 0.8rem;
        }
        [data-testid="stMetricDelta"] {
            font-size: 0.8rem;
        }
    </style>
    """, unsafe_allow_html=True)

    if result.years and result.is_financially_free:
        st.success("\u2705 恭喜！您已实现财务自由！")
    elif result.years:
        st.error("\u274C 财务自由未达成")
        st.metric(
            "最大资金缺口",
            f"{-result.shortfall_amount:,.0f} 元",
        )
        st.caption(f"缺口出现在 {result.shortfall_year} 年")
    else:
        st.info("\u2139 年龄已达到预期寿命，无需模拟。")
        nw = result.initial_net_worth
        status = "\u2705 财务自由" if nw >= 0 else "\u274C 未达成"
        st.metric("当前净资产", f"{nw:,.0f} 元")
        return

    total_years = len(result.years)
    cols = st.columns(6)
    cols[0].metric("初始净资产", f"{result.initial_net_worth:,.0f}")
    cols[1].metric("最终净资产", f"{result.final_net_worth:,.0f}")
    cols[2].metric("模拟年限", f"{total_years} 年")
    cols[3].metric("总收入", f"{result.total_income_all:,.0f}")
    cols[4].metric("总支出", f"{result.total_expense_all:,.0f}")
    cols[5].metric(
        "净现金流",
        f"{result.total_income_all - result.total_expense_all:,.0f}",
    )


def render_charts(result: SimulationResult):
    if not result.years:
        return

    col1, col2 = st.columns(2)

    with col1:
        df = pd.DataFrame([
            {"年份": y.year, "年末净资产（万）": y.net_worth_end / 10000}
            for y in result.years
        ])
        fig = px.line(df, x="年份", y="年末净资产（万）",
                      title="净资产趋势")
        fig.add_hline(y=0, line_dash="dash", line_color="red",
                      annotation_text="盈亏线")
        fig.update_layout(height=350)
        st.plotly_chart(fig, width="stretch")

    with col2:
        df = pd.DataFrame([
            {"年份": y.year, "收入（万）": y.total_income / 10000,
             "支出（万）": y.total_expense / 10000}
            for y in result.years
        ])
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df["年份"], y=df["收入（万）"],
                             name="收入", marker_color="green"))
        fig.add_trace(go.Bar(x=df["年份"], y=df["支出（万）"],
                             name="支出", marker_color="red"))
        fig.update_layout(barmode="group", title="年度收支对比", height=350)
        st.plotly_chart(fig, width="stretch")


def render_yearly_table(years: list[SimulationYear]):
    if not years:
        return

    st.subheader("\U0001F4CA 年度明细表")

    rows = []
    for y in years:
        rows.append({
            "年份": y.year,
            "年龄": y.person1_age,
            "配偶": y.person2_age if y.person2_age is not None else "\u2014",
            "生活支出": y.living_expense,
            "房贷支出": y.mortgage_expense,
            "车贷支出": y.car_loan_expense,
            "教育支出": y.education_expense,
            "意外支出": y.emergency_expense,
            "收入合计": y.total_income,
            "支出合计": y.total_expense,
            "净现金流": y.net_cashflow,
            "年初净资产": y.net_worth_start,
            "年末净资产": y.net_worth_end,
        })

    df = pd.DataFrame(rows)

    st.dataframe(
        df,
        width="stretch",
        height=350,
        column_config={
            "收入合计": st.column_config.NumberColumn(format="%.0f"),
            "支出合计": st.column_config.NumberColumn(format="%.0f"),
            "净现金流": st.column_config.NumberColumn(format="%.0f"),
            "年初净资产": st.column_config.NumberColumn(format="%.0f"),
            "年末净资产": st.column_config.NumberColumn(format="%.0f"),
        },
    )

    st.caption(f"共 {len(years)} 行，可用底部导出按钮下载完整明细")

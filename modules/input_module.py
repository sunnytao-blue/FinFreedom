import json
from datetime import datetime

import streamlit as st
from models.datamodels import (
    InputData, FamilyFinance, Income, EmergencyReserve, EconParams,
    Child, EducationStage,
)


def _get_defaults() -> InputData:
    if "input_data" in st.session_state and st.session_state.input_data is not None:
        return st.session_state.input_data
    from modules.io_module import default_input_data
    return default_input_data()


def render_sidebar() -> InputData:
    defaults = _get_defaults()

    st.header("\U0001F4CB 输入参数")

    # ======== 3.1.1 评估对象 ========
    with st.expander("评估对象", expanded=True):
        mode = st.selectbox(
            "评估模式", ["个人", "夫妻两人"],
            index=0 if defaults.evaluation_mode == "个人" else 1,
            key="input_mode",
        )
        your_age = st.number_input(
            "你的年龄", min_value=0, max_value=100,
            value=defaults.your_age, key="input_your_age",
        )
        spouse_age = None
        if mode == "夫妻两人":
            spouse_age = st.number_input(
                "配偶年龄", min_value=0, max_value=100,
                value=defaults.spouse_age if defaults.spouse_age else 35,
                key="input_spouse_age",
            )
        retirement_age = st.number_input(
            "预计退休年龄", min_value=0, max_value=100,
            value=defaults.retirement_age, key="input_ret_age",
        )
        life_expectancy = st.number_input(
            "预计人均寿命", min_value=0, max_value=120,
            value=defaults.life_expectancy, key="input_life_exp",
        )

    # ======== 3.1.2 资产与负债 ========
    with st.expander("资产与负债"):
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("资产")
            deposit = st.number_input(
                "存款（万元）", min_value=0.0, step=1.0, format="%.2f",
                value=float(defaults.finance.deposit) / 10000.0, key="fin_deposit",
            ) * 10000.0
            cash = st.number_input(
                "现金（万元）", min_value=0.0, step=1.0, format="%.2f",
                value=float(defaults.finance.cash) / 10000.0, key="fin_cash",
            ) * 10000.0
            fund_val = st.number_input(
                "基金市值（万元）", min_value=0.0, step=1.0, format="%.2f",
                value=float(defaults.finance.fund_value) / 10000.0, key="fin_fund",
            ) * 10000.0
            stock_val = st.number_input(
                "股票市值（万元）", min_value=0.0, step=1.0, format="%.2f",
                value=float(defaults.finance.stock_value) / 10000.0, key="fin_stock",
            ) * 10000.0
            property_val = st.number_input(
                "房产估值（万元）", min_value=0.0, step=1.0, format="%.2f",
                value=float(defaults.finance.property_value) / 10000.0, key="fin_property",
            ) * 10000.0
            car_val = st.number_input(
                "车辆估值（万元）", min_value=0.0, step=1.0, format="%.2f",
                value=float(defaults.finance.car_value) / 10000.0, key="fin_car",
            ) * 10000.0
            other_assets = st.number_input(
                "其他资产（万元）", min_value=0.0, step=1.0, format="%.2f",
                value=float(defaults.finance.other_assets) / 10000.0, key="fin_other_assets",
            ) * 10000.0
        with col2:
            st.subheader("负债")
            mortgage = st.number_input(
                "房贷余额（万元）", min_value=0.0, step=1.0, format="%.2f",
                value=float(defaults.finance.mortgage_balance) / 10000.0, key="fin_mortgage",
            ) * 10000.0
            car_loan = st.number_input(
                "车贷余额（万元）", min_value=0.0, step=1.0, format="%.2f",
                value=float(defaults.finance.car_loan_balance) / 10000.0, key="fin_car_loan",
            ) * 10000.0
            other_liab = st.number_input(
                "其他负债（万元）", min_value=0.0, step=1.0, format="%.2f",
                value=float(defaults.finance.other_liabilities) / 10000.0, key="fin_other_liab",
            ) * 10000.0

        finance = FamilyFinance(
            deposit=deposit, cash=cash, fund_value=fund_val,
            stock_value=stock_val, property_value=property_val,
            car_value=car_val, other_assets=other_assets,
            mortgage_balance=mortgage, car_loan_balance=car_loan,
            other_liabilities=other_liab,
        )
        st.caption(f"总资产: {finance.total_assets / 10000:,.2f} 万 | 总负债: {finance.total_liabilities / 10000:,.2f} 万 | 净资产: {finance.net_worth / 10000:,.2f} 万")

    # ======== 3.1.3 持续收入 ========
    with st.expander("持续收入"):
        salary = st.number_input(
            "工资收入（年）", min_value=0.0, step=1000.0, format="%.0f",
            value=float(defaults.income.salary_annual), key="inc_salary",
        )
        rental = st.number_input(
            "房租收入（年）", min_value=0.0, step=1000.0, format="%.0f",
            value=float(defaults.income.rental_annual), key="inc_rental",
        )
        dividend = st.number_input(
            "分红收入（年）", min_value=0.0, step=1000.0, format="%.0f",
            value=float(defaults.income.dividend_annual), key="inc_dividend",
        )
        other_inc = st.number_input(
            "其他收入（年）", min_value=0.0, step=1000.0, format="%.0f",
            value=float(defaults.income.other_annual), key="inc_other",
        )
        income = Income(
            salary_annual=salary, rental_annual=rental,
            dividend_annual=dividend, other_annual=other_inc,
        )
        st.caption(f"年收入合计: {income.total:,.0f}")

    # ======== 3.1.4 生活支出 ========
    with st.expander("生活支出"):
        monthly_expense = st.number_input(
            "月生活消费", min_value=0.0, step=100.0, format="%.0f",
            value=float(defaults.monthly_expense), key="exp_monthly",
        )

    # ======== 3.1.5 小孩抚养 ========
    with st.expander("小孩抚养"):
        children = _render_children(defaults.children)

    # ======== 3.1.6 意外预留 ========
    with st.expander("意外预留"):
        emergency_amount = st.number_input(
            "意外预留总额（万元）", min_value=0.0, step=1.0, format="%.2f",
            value=float(defaults.emergency_reserve.amount) / 10000.0, key="emerg_amount",
        ) * 10000.0
        emergency_mode = st.selectbox(
            "分摊方式", ["一次性扣除", "逐年均摊"],
            index=0 if defaults.emergency_reserve.mode == "一次性扣除" else 1,
            key="emerg_mode",
        )
        emergency = EmergencyReserve(amount=emergency_amount, mode=emergency_mode)

    # ======== 3.1.7 经济参数 ========
    with st.expander("经济参数"):
        infl_rate = st.number_input(
            "年化通胀率（%）", min_value=-5.0, max_value=20.0, step=0.1,
            value=defaults.params.inflation_rate * 100, key="param_infl",
        ) / 100.0
        asset_ret = st.number_input(
            "资产年化收益率（%）", min_value=-5.0, max_value=20.0, step=0.1,
            value=defaults.params.asset_return_rate * 100, key="param_asset",
        ) / 100.0
        params = EconParams(inflation_rate=infl_rate, asset_return_rate=asset_ret)

    # ======== 操作按钮 ========
    col1, col2 = st.columns(2)
    with col1:
        if st.button("\U0001F504 恢复默认值", help="将所有参数重置为出厂默认值"):
            from modules.io_module import default_input_data
            keys_to_keep = {"initialized", "sidebar_upload_key"}
            for key in list(st.session_state.keys()):
                if key not in keys_to_keep:
                    del st.session_state[key]
            st.session_state.input_data = default_input_data()
            st.session_state.result = None
            st.session_state.force_recalc = True
            st.rerun()
    with col2:
        if st.button("\U0001F522 重新计算"):
            st.session_state.result = None
            st.rerun()

    col1, col2 = st.columns(2)
    with col1:
        from modules.io_module import build_params_json
        params_json = build_params_json(st.session_state.input_data)
        st.download_button(
            "\U0001F4BE 保存参数",
            data=params_json,
            file_name=f"参数_{datetime.now():%Y%m%d}.json",
            mime="application/json",
            key="sidebar_save_params",
        )
    with col2:
        if "sidebar_upload_key" not in st.session_state:
            st.session_state.sidebar_upload_key = 0
        uploaded = st.file_uploader(
            "\U0001F4C2 加载参数", type=["json"],
            key=f"sidebar_load_{st.session_state.sidebar_upload_key}",
        )
        if uploaded is not None:
            try:
                data = json.load(uploaded)
                st.session_state.input_data = InputData.from_dict(data.get("input", data))
                st.session_state.result = None
                st.session_state.sidebar_upload_key += 1
                st.rerun()
            except Exception as e:
                st.error(f"加载失败: {e}")

    return InputData(
        evaluation_mode=mode,
        your_age=your_age,
        spouse_age=spouse_age,
        retirement_age=retirement_age,
        life_expectancy=life_expectancy,
        finance=finance,
        income=income,
        monthly_expense=monthly_expense,
        children=children,
        emergency_reserve=emergency,
        params=params,
    )


def _render_children(existing: list[Child]) -> list[Child]:
    children: list[dict] = []

    for i, child in enumerate(existing):
        with st.container():
            st.markdown(f"**小孩 {i + 1}**")
            col1, col2 = st.columns([4, 1])
            with col2:
                if st.button("\U0001F5D1", key=f"del_child_{i}"):
                    if 0 <= i < len(st.session_state.input_data.children):
                        del st.session_state.input_data.children[i]
                    st.rerun()

            age = st.number_input(
                "当前年龄", min_value=0, max_value=50,
                value=child.current_age, key=f"child_{i}_age",
            )

            # 学前
            pre_stage = child.education_stages[0] if len(child.education_stages) > 0 else EducationStage(
                name="学前", start_age=0, duration=6, annual_cost=0.0)
            c1, c2, c3 = st.columns(3)
            with c1:
                pre_start = st.number_input(
                    "学前起始年龄", min_value=0, max_value=30,
                    value=pre_stage.start_age, key=f"child_{i}_pre_start",
                )
            with c2:
                pre_dur = st.number_input(
                    "学前年限", min_value=1, max_value=20,
                    value=pre_stage.duration, key=f"child_{i}_pre_dur",
                )
            with c3:
                pre_cost = st.number_input(
                    "学前年费用", min_value=0.0, step=1000.0, format="%.0f",
                    value=float(pre_stage.annual_cost), key=f"child_{i}_pre_cost",
                )

            # 小学
            elem_stage = child.education_stages[1] if len(child.education_stages) > 1 else EducationStage(
                name="小学", start_age=6, duration=6, annual_cost=0.0)
            c1, c2, c3 = st.columns(3)
            with c1:
                elem_start = st.number_input(
                    "小学起始年龄", min_value=0, max_value=30,
                    value=elem_stage.start_age, key=f"child_{i}_elem_start",
                )
            with c2:
                elem_dur = st.number_input(
                    "小学年限", min_value=1, max_value=20,
                    value=elem_stage.duration, key=f"child_{i}_elem_dur",
                )
            with c3:
                elem_cost = st.number_input(
                    "小学年费用", min_value=0.0, step=1000.0, format="%.0f",
                    value=float(elem_stage.annual_cost), key=f"child_{i}_elem_cost",
                )

            # 中学
            mid_stage = child.education_stages[2] if len(child.education_stages) > 2 else EducationStage(
                name="中学", start_age=12, duration=6, annual_cost=0.0)
            c1, c2, c3 = st.columns(3)
            with c1:
                mid_start = st.number_input(
                    "中学起始年龄", min_value=0, max_value=30,
                    value=mid_stage.start_age, key=f"child_{i}_mid_start",
                )
            with c2:
                mid_dur = st.number_input(
                    "中学年限", min_value=1, max_value=20,
                    value=mid_stage.duration, key=f"child_{i}_mid_dur",
                )
            with c3:
                mid_cost = st.number_input(
                    "中学年费用", min_value=0.0, step=1000.0, format="%.0f",
                    value=float(mid_stage.annual_cost), key=f"child_{i}_mid_cost",
                )

            # 大学
            uni_stage = child.education_stages[3] if len(child.education_stages) > 3 else EducationStage(
                name="大学", start_age=18, duration=4, annual_cost=0.0)
            c1, c2, c3 = st.columns(3)
            with c1:
                uni_start = st.number_input(
                    "大学起始年龄", min_value=0, max_value=30,
                    value=uni_stage.start_age, key=f"child_{i}_uni_start",
                )
            with c2:
                uni_dur = st.number_input(
                    "大学年限", min_value=1, max_value=20,
                    value=uni_stage.duration, key=f"child_{i}_uni_dur",
                )
            with c3:
                uni_cost = st.number_input(
                    "大学年费用", min_value=0.0, step=1000.0, format="%.0f",
                    value=float(uni_stage.annual_cost), key=f"child_{i}_uni_cost",
                )

            sponsorship = st.number_input(
                "毕业后一次性赞助", min_value=0.0, step=1000.0, format="%.0f",
                value=float(child.graduation_sponsorship), key=f"child_{i}_sponsor",
            )

            stages = [
                EducationStage(name="学前", start_age=pre_start, duration=pre_dur, annual_cost=pre_cost),
                EducationStage(name="小学", start_age=elem_start, duration=elem_dur, annual_cost=elem_cost),
                EducationStage(name="中学", start_age=mid_start, duration=mid_dur, annual_cost=mid_cost),
                EducationStage(name="大学", start_age=uni_start, duration=uni_dur, annual_cost=uni_cost),
            ]
            children.append(Child(
                current_age=age,
                education_stages=stages,
                graduation_sponsorship=sponsorship,
            ))
            st.divider()

    if st.button("\u2795 添加小孩"):
        st.session_state.input_data.children.append(
            Child(current_age=0, education_stages=[
                EducationStage(name="学前", start_age=0, duration=6, annual_cost=50_000.0),
                EducationStage(name="小学", start_age=6, duration=6, annual_cost=100_000.0),
                EducationStage(name="中学", start_age=12, duration=6, annual_cost=100_000.0),
                EducationStage(name="大学", start_age=18, duration=7, annual_cost=100_000.0),
            ])
        )
        st.rerun()

    return children


def validate_input(data: InputData) -> list[str]:
    errors = []
    if data.your_age >= data.life_expectancy:
        errors.append("你的年龄不能大于或等于预期寿命")
    if data.your_age < 0:
        errors.append("你的年龄不能为负数")
    if data.evaluation_mode == "夫妻两人":
        if data.spouse_age is None:
            errors.append("夫妻模式下必须填写配偶年龄")
        elif data.spouse_age >= data.life_expectancy:
            errors.append("配偶年龄不能大于或等于预期寿命")
        elif data.spouse_age < 0:
            errors.append("配偶年龄不能为负数")
    if data.retirement_age < 0:
        errors.append("退休年龄不能为负数")
    if data.life_expectancy < 1:
        errors.append("预期寿命必须大于0")
    if data.monthly_expense < 0:
        errors.append("月生活消费不能为负数")
    if not (-0.05 <= data.params.inflation_rate <= 0.20):
        errors.append("通胀率超出合理范围（-5% ~ 20%）")
    if not (-0.05 <= data.params.asset_return_rate <= 0.20):
        errors.append("资产收益率超出合理范围（-5% ~ 20%）")
    return errors

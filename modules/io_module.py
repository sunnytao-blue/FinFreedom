import json
import os
import io
from datetime import datetime

import pandas as pd

from models.datamodels import (
    InputData, FamilyFinance, Income, EmergencyReserve, EconParams,
    Child, EducationStage, SimulationResult, SimulationYear,
)


import os as _os
CONFIG_PATH = _os.path.join(_os.path.expanduser("~"), ".finfreedom_config.json")


# ======== 默认值 ========
def default_input_data() -> InputData:
    return InputData(
        evaluation_mode="个人",
        your_age=35,
        spouse_age=35,
        retirement_age=60,
        life_expectancy=85,
        finance=FamilyFinance(
            deposit=500_000.0,
            cash=50_000.0,
            fund_value=50_000.0,
            stock_value=100_000.0,
            property_value=3_000_000.0,
            car_value=200_000.0,
            other_assets=100_000.0,
        ),
        income=Income(
            salary_annual=0.0,
            dividend_annual=150_000.0,
        ),
        monthly_expense=15_000.0,
        children=[
            Child(
                current_age=5,
                education_stages=[
                    EducationStage(name="学前", start_age=0, duration=6, annual_cost=50_000.0),
                    EducationStage(name="小学", start_age=6, duration=6, annual_cost=100_000.0),
                    EducationStage(name="中学", start_age=12, duration=6, annual_cost=100_000.0),
                    EducationStage(name="大学", start_age=18, duration=7, annual_cost=100_000.0),
                ],
                graduation_sponsorship=200_000.0,
            ),
        ],
        emergency_reserve=EmergencyReserve(amount=100_000.0, mode="一次性扣除"),
        params=EconParams(inflation_rate=0.02, asset_return_rate=0.02),
    )


# ======== 参数持久化 ========
def save_config(input_data: InputData, path: str = CONFIG_PATH):
    payload = {
        "version": "1.0",
        "save_time": datetime.now().isoformat(),
        "input": input_data.to_dict(),
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def load_config(path: str = CONFIG_PATH) -> InputData:
    if not os.path.exists(path):
        return default_input_data()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return InputData.from_dict(data.get("input", data))
    except (json.JSONDecodeError, KeyError, TypeError):
        return default_input_data()


# ======== 结果保存与加载 ========
def build_params_json(input_data: InputData) -> str:
    payload = {
        "version": "1.0",
        "save_time": datetime.now().isoformat(),
        "input": input_data.to_dict(),
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def build_result_json(input_data: InputData, result: SimulationResult) -> str:
    payload = {
        "version": "1.0",
        "save_time": datetime.now().isoformat(),
        "input": input_data.to_dict(),
        "result": result.to_dict(),
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def export_csv(years: list[SimulationYear]) -> bytes:
    rows = []
    for y in years:
        rows.append({
            "年份": y.year,
            "年龄": y.person1_age,
            "配偶年龄": y.person2_age if y.person2_age is not None else "",
            "工资收入": y.salary_income,
            "房租收入": y.rental_income,
            "分红收入": y.dividend_income,
            "其他收入": y.other_income,
            "收入合计": y.total_income,
            "生活支出": y.living_expense,
            "教育支出": y.education_expense,
            "意外支出": y.emergency_expense,
            "支出合计": y.total_expense,
            "净现金流": y.net_cashflow,
            "年初净资产": y.net_worth_start,
            "年末净资产": y.net_worth_end,
        })
    df = pd.DataFrame(rows)
    return df.to_csv(index=False).encode("utf-8-sig")


def export_excel(years: list[SimulationYear]) -> bytes:
    rows = []
    for y in years:
        rows.append({
            "年份": y.year,
            "年龄": y.person1_age,
            "配偶年龄": y.person2_age if y.person2_age is not None else "",
            "工资收入": y.salary_income,
            "房租收入": y.rental_income,
            "分红收入": y.dividend_income,
            "其他收入": y.other_income,
            "收入合计": y.total_income,
            "生活支出": y.living_expense,
            "教育支出": y.education_expense,
            "意外支出": y.emergency_expense,
            "支出合计": y.total_expense,
            "净现金流": y.net_cashflow,
            "年初净资产": y.net_worth_start,
            "年末净资产": y.net_worth_end,
        })
    df = pd.DataFrame(rows)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="模拟明细")
    return output.getvalue()

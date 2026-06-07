from datetime import datetime
from models.datamodels import InputData, SimulationResult, SimulationYear
from utils.helpers import calculate_education_expense


def run_simulation(input_data: InputData) -> SimulationResult:
    current_year = datetime.now().year

    # Step 1: 确定模拟年限
    min_age = input_data.your_age
    if input_data.evaluation_mode == "夫妻两人" and input_data.spouse_age is not None:
        min_age = min(min_age, input_data.spouse_age)
    total_years = input_data.life_expectancy - min_age

    # 边界：年龄已达到或超过预期寿命
    if total_years <= 0:
        nw = input_data.finance.net_worth
        return SimulationResult(
            years=[],
            is_financially_free=nw >= 0,
            shortfall_amount=min(0.0, nw),
            shortfall_year=None,
            total_income_all=0.0,
            total_expense_all=0.0,
            initial_net_worth=nw,
            final_net_worth=nw,
        )

    # Step 2: 初始化
    rate = input_data.params.inflation_rate
    asset_return = input_data.params.asset_return_rate
    net_worth = input_data.finance.net_worth
    yearly_rows: list[SimulationYear] = []

    # 意外预留
    emergency_annual = 0.0
    emergency_one_time = 0.0
    if input_data.emergency_reserve.mode == "逐年均摊" and total_years > 0:
        emergency_annual = input_data.emergency_reserve.amount / total_years
    else:
        emergency_one_time = input_data.emergency_reserve.amount

    # Step 3: 逐年模拟
    for t in range(total_years):
        year = current_year + t
        age1 = input_data.your_age + t
        age2 = (input_data.spouse_age + t) if input_data.spouse_age is not None else None

        inflate = (1 + rate) ** t

        # --- 收入计算 ---
        salary = input_data.income.salary_annual if age1 < input_data.retirement_age else 0.0
        rental = input_data.income.rental_annual
        dividend = input_data.income.dividend_annual
        other_inc = input_data.income.other_annual
        total_income = (salary + rental + dividend + other_inc) * inflate

        # --- 支出计算 ---
        living_exp = input_data.monthly_expense * 12 * inflate
        edu_exp = calculate_education_expense(input_data.children, age1, t) * inflate
        emerg_exp = emergency_one_time if (t == 0 and emergency_one_time > 0) else emergency_annual
        total_expense = living_exp + edu_exp + emerg_exp

        # --- 净资产 ---
        net_worth_start = net_worth
        net_cashflow = total_income - total_expense
        net_worth = net_worth * (1 + asset_return) + net_cashflow

        yearly_rows.append(SimulationYear(
            year=year, person1_age=age1, person2_age=age2,
            salary_income=salary * inflate,
            rental_income=rental * inflate,
            dividend_income=dividend * inflate,
            other_income=other_inc * inflate,
            total_income=total_income,
            living_expense=living_exp,
            education_expense=edu_exp,
            emergency_expense=emerg_exp,
            total_expense=total_expense,
            net_cashflow=net_cashflow,
            net_worth_start=net_worth_start,
            net_worth_end=net_worth,
        ))

    # Step 4: 判定结果
    min_net_worth = min(r.net_worth_end for r in yearly_rows)
    is_free = min_net_worth >= 0
    shortfall_amount = 0.0
    shortfall_year = None

    if not is_free:
        shortfall_amount = min_net_worth
        worst = min(yearly_rows, key=lambda r: r.net_worth_end)
        shortfall_year = worst.year

    return SimulationResult(
        years=yearly_rows,
        is_financially_free=is_free,
        shortfall_amount=shortfall_amount,
        shortfall_year=shortfall_year,
        total_income_all=sum(r.total_income for r in yearly_rows),
        total_expense_all=sum(r.total_expense for r in yearly_rows),
        initial_net_worth=input_data.finance.net_worth,
        final_net_worth=yearly_rows[-1].net_worth_end,
    )

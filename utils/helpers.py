from models.datamodels import Child, EducationStage


def inflation_factor(rate: float, years_elapsed: int) -> float:
    return (1 + rate) ** years_elapsed


def is_in_education_stage(child_age: int, stage_start: int, stage_duration: int) -> bool:
    return stage_start <= child_age < stage_start + stage_duration


def years_until_retirement(current_age: int, retirement_age: int) -> int:
    return max(0, retirement_age - current_age)


def format_currency(value: float) -> str:
    if abs(value) >= 1_0000_0000:
        return f"{value / 1_0000_0000:,.2f} 亿"
    elif abs(value) >= 1_0000:
        return f"{value / 1_0000:,.2f} 万"
    else:
        return f"{value:,.0f}"


def calculate_education_expense(children: list[Child], current_age: int, year_offset: int) -> float:
    total = 0.0
    for child in children:
        child_age_now = child.current_age + year_offset
        for stage in child.education_stages:
            if is_in_education_stage(child_age_now, stage.start_age, stage.duration):
                total += stage.annual_cost
                break
        if child.education_stages:
            last_stage = child.education_stages[-1]
            if child_age_now == last_stage.start_age + last_stage.duration:
                total += child.graduation_sponsorship
    return total

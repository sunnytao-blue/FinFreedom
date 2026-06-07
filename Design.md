# 财务自由模拟评估系统 — 设计文档 (Design)

## 1. 系统架构

### 1.1 整体架构

```
┌─────────────────────────────────────────────────┐
│                   app.py                        │
│  (Streamlit 入口：组装模块、管理 Session State)    │
└──────┬──────────┬──────────┬──────────┬──────────┘
       │          │          │          │
       ▼          ▼          ▼          ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ input_   │ │calcula-  │ │display_  │ │  io_     │
│ module   │ │tor       │ │module    │ │ module   │
│ .py      │ │.py       │ │.py       │ │ .py      │
│          │ │          │ │          │ │          │
│ 输入表单 │ │ 逐年模拟  │ │ 概览/图表│ │ JSON读写 │
│ 数据校验 │ │ 通胀调整  │ │ 明细表   │ │ CSV导出  │
│ 默认值   │ │ 判定逻辑  │ │          │ │ config   │
└────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘
     │            │            │            │
     └────────────┴────────────┴────────────┘
                          │
                    ┌─────┴─────┐
                    │  models/   │
                    │ datamodels │
                    └───────────┘
                          │
                    ┌─────┴─────┐
                    │  utils/   │
                    │ helpers   │
                    └───────────┘
```

### 1.2 数据流

```
用户修改输入表单
       │
       ▼
input_module 收集数据 → dict（输入参数）
       │
       ▼
写入 st.session_state["input_data"]
       │
       ▼
calculator.run(input_data)
       │
       ▼
返回 SimulationResult
       │
       ▼
写入 st.session_state["result"]
       │
       ▼
display_module 根据 result 渲染界面
       │
       ▼
io_module 处理保存/加载/导出
```

### 1.3 触发逻辑

Streamlit 的每次脚本重绘流程：

```
用户操作（修改表单/点击按钮）
       │
       ▼
app.py 从头执行
       │
       ├─ 1. 初始化 Session State（如不存在）
       │
       ├─ 2. io_module 加载 config.json → 预填表单
       │
       ├─ 3. input_module 渲染侧边栏表单
       │       └─ 用户输入 → 更新 session_state["input_data"]
       │
       ├─ 4. 判断是否需要重新计算
       │       └─ input_data 有变化 → 调用 calculator.run()
       │       └─ 无变化 → 使用缓存的 result
       │
       ├─ 5. display_module 渲染结果
       │
       └─ 6. io_module 渲染操作按钮
```

> 由于 Streamlit 每次交互都会从头运行整个脚本，需要利用 `st.session_state` 缓存输入和结果，避免重复计算。

---

## 2. Session State 设计

### 2.1 State 键定义

| 键名 | 类型 | 用途 | 初始化时机 |
|------|------|------|-----------|
| `"initialized"` | `bool` | 标记是否完成首次初始化 | 应用启动 |
| `"input_data"` | `InputData` | 当前所有输入数据 | 加载 config 后 |
| `"result"` | `SimulationResult` 或 `None` | 最新计算结果 | 每次计算后 |
| `"force_recalc"` | `bool` | 恢复默认值后强制重算标记 | 恢复默认值时 |
| `"sidebar_upload_key"` | `int` | 文件上传器刷新计数器 | 加载参数后 |

### 2.2 初始化代码结构

```python
def init_session_state():
    if "initialized" not in st.session_state:
        st.session_state.initialized = True
        st.session_state.input_data = load_config()
        st.session_state.result = None
        st.session_state.force_recalc = False
        st.session_state.sidebar_upload_key = 0
```

---

## 3. 模块详细设计

### 3.1 models/datamodels.py — 数据模型

使用 Python `@dataclass` 定义所有数据模型，支持序列化为 dict。

```python
from dataclasses import dataclass, field, asdict
from typing import Optional

@dataclass
class EducationStage:
    name: str              # "学前" / "小学" / "中学" / "大学"
    start_age: int
    duration: int
    annual_cost: float

@dataclass
class Child:
    current_age: int
    education_stages: list[EducationStage] = field(default_factory=list)
    graduation_sponsorship: float = 0.0

    # 注意：education_stages 的默认顺序为 学前(0) → 小学(1) → 中学(2) → 大学(3)，
    # 学前为第 0 个阶段，start_age=0, duration=6

    @property
    def total_education_years(self) -> int:
        return sum(s.duration for s in self.education_stages)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["education_stages"] = [asdict(s) for s in self.education_stages]
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "Child":
        stages = [EducationStage(**s) for s in data.pop("education_stages", [])]
        return cls(**data, education_stages=stages)

@dataclass
class Person:
    name: str                    # "本人" or "配偶"
    current_age: int
    retirement_age: int
    life_expectancy: int

@dataclass
class FamilyFinance:
    deposit: float = 0.0
    cash: float = 0.0
    fund_value: float = 0.0
    stock_value: float = 0.0
    property_value: float = 0.0
    car_value: float = 0.0
    other_assets: float = 0.0
    mortgage_balance: float = 0.0
    car_loan_balance: float = 0.0
    other_liabilities: float = 0.0

    @property
    def total_assets(self) -> float:
        return (self.deposit + self.cash + self.fund_value +
                self.stock_value + self.property_value +
                self.car_value + self.other_assets)

    @property
    def total_liabilities(self) -> float:
        return (self.mortgage_balance + self.car_loan_balance +
                self.other_liabilities)

    @property
    def net_worth(self) -> float:
        return self.total_assets - self.total_liabilities

@dataclass
class Income:
    salary_annual: float = 0.0
    rental_annual: float = 0.0
    dividend_annual: float = 0.0
    other_annual: float = 0.0

    @property
    def total(self) -> float:
        return self.salary_annual + self.rental_annual + self.dividend_annual + self.other_annual

@dataclass
class EmergencyReserve:
    amount: float = 0.0
    mode: str = "一次性扣除"    # "一次性扣除" or "逐年均摊"

@dataclass
class EconParams:
    inflation_rate: float = 0.02
    asset_return_rate: float = 0.02

@dataclass
class InputData:
    evaluation_mode: str                # "个人" or "夫妻两人"
    your_age: int
    spouse_age: Optional[int]
    retirement_age: int
    life_expectancy: int
    finance: FamilyFinance
    income: Income
    monthly_expense: float
    children: list[Child]
    emergency_reserve: EmergencyReserve
    params: EconParams

@dataclass
class SimulationYear:
    year: int
    person1_age: int
    person2_age: Optional[int]
    salary_income: float
    rental_income: float
    dividend_income: float
    other_income: float
    total_income: float
    living_expense: float
    education_expense: float
    emergency_expense: float
    total_expense: float
    net_cashflow: float
    net_worth_start: float
    net_worth_end: float

@dataclass
class SimulationResult:
    years: list[SimulationYear]
    is_financially_free: bool
    shortfall_amount: float
    shortfall_year: Optional[int]
    total_income_all: float
    total_expense_all: float
    initial_net_worth: float
    final_net_worth: float
```

#### 序列化工具

每个 dataclass 提供 `to_dict()` 和 `from_dict()` 类方法（或使用 `asdict()` + 递归反序列化），便于 JSON 存储。

---

### 3.2 modules/input_module.py — 输入模块

#### 3.2.1 核心函数

```python
def render_sidebar() -> InputData:
    """在侧边栏渲染所有输入表单，返回 InputData 对象。
    注意：由 app.py 在外层包裹 `with st.sidebar:` 调用。"""

    st.header("📋 输入参数")

    # 读取上次保存的值（从 session_state 或 config）
    defaults = st.session_state.input_data

    # ---------- 3.1.1 评估对象 ----------
    with st.expander("评估对象", expanded=True):
        mode = st.selectbox("评估模式", ["个人", "夫妻两人"],
                            index=0 if defaults.evaluation_mode == "个人" else 1)
        your_age = st.number_input("你的年龄", min_value=0, max_value=100,
                                   value=defaults.your_age)
        spouse_age = None
        if mode == "夫妻两人":
            spouse_age = st.number_input("配偶年龄", min_value=0, max_value=100,
                                         value=defaults.spouse_age or 35)
        retirement_age = st.number_input("预计退休年龄", min_value=0, max_value=100,
                                         value=defaults.retirement_age)
        life_expectancy = st.number_input("预计人均寿命", min_value=0, max_value=120,
                                          value=defaults.life_expectancy)

    # ---------- 3.1.2 资产与负债 ----------
    with st.expander("资产与负债"):
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("资产")
            deposit = st.number_input("存款", ...)
            cash = st.number_input("现金", ...)
            # ... 其余资产字段
        with col2:
            st.subheader("负债")
            mortgage = st.number_input("房贷余额", ...)
            # ... 其余负债字段

    # ---------- 3.1.3 持续收入 ----------
    with st.expander("持续收入"):
        # 工资、房租、分红、其他

    # ---------- 3.1.4 生活支出 ----------
    with st.expander("生活支出"):
        monthly_expense = st.number_input("月生活消费", ...)

    # ---------- 3.1.5 小孩抚养 ----------
    with st.expander("小孩抚养"):
        # 动态添加/删除小孩
        children = render_children_input(defaults.children)

    # ---------- 3.1.6 意外预留 ----------
    with st.expander("意外预留"):
        # 总额 + 分摊方式

    # ---------- 3.1.7 经济参数 ----------
    with st.expander("经济参数"):
        inflation = st.number_input("年化通胀率", ...)
        asset_return = st.number_input("资产年化收益率", ...)

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

    return InputData(...)
```

#### 3.2.2 小孩输入渲染

```python
def render_children_input(existing_children: list[Child]) -> list[Child]:
    """渲染动态小孩表单，支持添加/删除。
    通过直接修改 st.session_state.input_data.children 实现增删。"""
    children = []

    # 显示已有小孩
    for i, child in enumerate(existing_children):
        with st.container():
            st.markdown(f"**小孩 {i+1}**")
            age = st.number_input(f"当前年龄", key=f"child_{i}_age",
                                  value=child.current_age)
            # 教育阶段 ...
            # 删除按钮
            if st.button(f"删除小孩 {i+1}", key=f"del_child_{i}"):
                if 0 <= i < len(st.session_state.input_data.children):
                    del st.session_state.input_data.children[i]
                st.rerun()

    # 添加新小孩
    if st.button("➕ 添加小孩"):
        st.session_state.input_data.children.append(Child(current_age=0))
        st.rerun()

    return children
```

> 关键设计：通过直接修改 `st.session_state.input_data.children` 列表实现添加/删除，配合 `st.rerun()` 刷新 UI。

#### 3.2.3 数据校验

```python
def validate_input(data: InputData) -> list[str]:
    """校验输入数据，返回错误信息列表。空列表表示校验通过。"""
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
        errors.append("预期寿命必须大于 0")
    if data.monthly_expense < 0:
        errors.append("月生活消费不能为负数")
    if not (-0.05 <= data.params.inflation_rate <= 0.20):
        errors.append("通胀率超出合理范围（-5% ~ 20%），请检查")
    if not (-0.05 <= data.params.asset_return_rate <= 0.20):
        errors.append("资产收益率超出合理范围（-5% ~ 20%），请检查")
    # 资产/收入字段允许为 0 或负数（负债情况），不做强制校验
    return errors
```

---

### 3.3 modules/calculator.py — 计算引擎

#### 3.3.1 核心算法（伪代码）

```python
from datetime import datetime
from models.datamodels import InputData, SimulationResult, SimulationYear
from utils.helpers import calculate_education_expense

def run_simulation(input_data: InputData) -> SimulationResult:
    # Step 1: 确定模拟年限
    current_year = datetime.now().year
    min_age = input_data.your_age
    if input_data.evaluation_mode == "夫妻两人" and input_data.spouse_age:
        min_age = min(min_age, input_data.spouse_age)
    total_years = input_data.life_expectancy - min_age

    # 边界：年龄已达到或超过预期寿命，无需模拟
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
    net_worth = input_data.finance.net_worth
    yearly_rows = []

    # 意外预留
    emergency_annual = 0.0
    emergency_one_time = 0.0
    if input_data.emergency_reserve.mode == "逐年均摊":
        emergency_annual = input_data.emergency_reserve.amount / total_years
    else:
        emergency_one_time = input_data.emergency_reserve.amount

    # Step 3: 逐年模拟
    for t in range(total_years):
        year = current_year + t
        age1 = input_data.your_age + t
        age2 = (input_data.spouse_age + t) if input_data.spouse_age else None

        inflation_factor = (1 + input_data.params.inflation_rate) ** t

        # --- 收入计算 ---
        salary = input_data.income.salary_annual if age1 < input_data.retirement_age else 0.0
        rental = input_data.income.rental_annual
        dividend = input_data.income.dividend_annual
        other_inc = input_data.income.other_annual
        total_income = (salary + rental + dividend + other_inc) * inflation_factor

        # --- 支出计算 ---
        living_exp = input_data.monthly_expense * 12 * inflation_factor

        # 小孩教育（含通胀调整）
        edu_exp = calculate_education_expense(input_data.children, age1, t) * inflation_factor

        # 意外
        emerg_exp = emergency_one_time if (t == 0 and emergency_one_time > 0) else emergency_annual

        total_expense = living_exp + edu_exp + emerg_exp

        # --- 净资产 ---
        net_worth_start = net_worth   # 更新前捕获年初值
        net_cashflow = total_income - total_expense
        net_worth = net_worth * (1 + input_data.params.asset_return_rate) + net_cashflow

        # --- 记录 ---
        yearly_rows.append(SimulationYear(
            year=year, person1_age=age1, person2_age=age2,
            salary_income=salary * inflation_factor,
            rental_income=rental * inflation_factor,
            dividend_income=dividend * inflation_factor,
            other_income=other_inc * inflation_factor,
            total_income=total_income,
            living_expense=living_exp,
            education_expense=edu_exp,
            emergency_expense=emerg_exp,
            total_expense=total_expense,
            net_cashflow=net_cashflow,
            net_worth_start=net_worth_start,
            net_worth_end=net_worth
        ))

    # Step 4: 判定结果
    min_net_worth = min(r.net_worth_end for r in yearly_rows)
    is_free = min_net_worth >= 0
    shortfall_year = None
    shortfall_amount = 0.0
    if not is_free:
        shortfall_amount = min_net_worth
        # 找到第一个出现负值或最负的年份
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
        final_net_worth=yearly_rows[-1].net_worth_end if yearly_rows else 0
    )
```

#### 3.3.2 教育费用计算

```python
def calculate_education_expense(children: list[Child], current_age: int, year_offset: int) -> float:
    """计算某一年所有小孩的教育费用总和"""
    total = 0.0
    for child in children:
        child_age_now = child.current_age + year_offset
        for stage in child.education_stages:
            stage_end = stage.start_age + stage.duration
            if stage.start_age <= child_age_now < stage_end:
                total += stage.annual_cost
                break
        # 毕业赞助：仅在最后一个教育阶段结束当年一次性支付
        if child.education_stages:
            last_stage = child.education_stages[-1]
            if child_age_now == last_stage.start_age + last_stage.duration:
                total += child.graduation_sponsorship
    return total
```

---

### 3.4 modules/display_module.py — 显示模块

#### 3.4.1 核心函数

```python
import pandas as pd
import plotly.express as px
import streamlit as st

def render_dashboard(result: SimulationResult, input_data: InputData):
    """渲染主界面结果仪表盘"""

    # 1. 结果概览卡
    render_summary_card(result)

    # 2. 图表
    col1, col2 = st.columns(2)
    with col1:
        plot_net_worth_trend(result.years)
    with col2:
        plot_income_expense_bar(result.years)

    # 可选饼图
    with st.expander("收支构成分析"):
        plot_pie_charts(result, input_data)

    # 3. 年度明细表
    render_yearly_table(result.years)
```

#### 3.4.2 概览卡

```python
def render_summary_card(result: SimulationResult):
    if result.is_financially_free:
        st.success("✅ 恭喜！您已实现财务自由！")
    else:
        st.error(f"❌ 财务自由未达成")
        st.metric("资金缺口", f"{-result.shortfall_amount:,.0f} 元",
                  delta_color="inverse")
        st.caption(f"缺口出现在 {result.shortfall_year} 年")

    cols = st.columns(4)
    cols[0].metric("初始净资产", f"{result.initial_net_worth:,.0f}")
    cols[1].metric("总收入", f"{result.total_income_all:,.0f}")
    cols[2].metric("总支出", f"{result.total_expense_all:,.0f}")
    cols[3].metric("最终净资产", f"{result.final_net_worth:,.0f}")
```

#### 3.4.3 图表（Plotly）

```python
def plot_net_worth_trend(years: list[SimulationYear]):
    df = pd.DataFrame([
        {"年份": y.year, "年末净资产": y.net_worth_end} for y in years
    ])
    fig = px.line(df, x="年份", y="年末净资产",
                  title="净资产趋势")
    fig.add_hline(y=0, line_dash="dash", line_color="red")
    st.plotly_chart(fig, use_container_width=True)

def plot_income_expense_bar(years: list[SimulationYear]):
    df = pd.DataFrame([
        {"年份": y.year, "收入": y.total_income, "支出": y.total_expense}
        for y in years
    ])
    fig = px.bar(df, x="年份", y=["收入", "支出"],
                 barmode="group", title="年度收支对比")
    st.plotly_chart(fig, use_container_width=True)
```

#### 3.4.4 年度明细表

```python
def render_yearly_table(years: list[SimulationYear]):
    df = pd.DataFrame([
        {
            "年份": y.year,
            "年龄": y.person1_age,
            "配偶年龄": y.person2_age if y.person2_age else "—",
            "收入合计": y.total_income,
            "支出合计": y.total_expense,
            "净现金流": y.net_cashflow,
            "年初净资产": y.net_worth_start,
            "年末净资产": y.net_worth_end,
        }
        for y in years
    ])
    # 格式化数字
    styled = df.style.format({
        "收入合计": "{:,.0f}",
        "支出合计": "{:,.0f}",
        "净现金流": "{:,.0f}",
        "年初净资产": "{:,.0f}",
        "年末净资产": "{:,.0f}",
    })
    st.dataframe(styled, use_container_width=True, height=400)
```

---

### 3.5 modules/io_module.py — 持久化与 IO

#### 3.5.1 核心接口

```python
import json
import os
import io
from datetime import datetime
import pandas as pd

import os as _os
CONFIG_PATH = _os.path.join(_os.path.expanduser("~"), ".finfreedom_config.json")

# ─── 输入参数持久化 ───
def save_config(input_data: InputData, path: str = CONFIG_PATH):
    """将输入参数保存到本地 JSON 文件（含 version 字段用于未来迁移）"""
    payload = {
        "version": "1.0",
        "save_time": datetime.now().isoformat(),
        "input": input_data.to_dict(),
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

def load_config(path: str = CONFIG_PATH) -> InputData:
    """从本地 JSON 文件加载输入参数，文件不存在时返回默认 InputData"""
    if not os.path.exists(path):
        return default_input_data()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return InputData.from_dict(data.get("input", data))
    except (json.JSONDecodeError, KeyError, TypeError):
        return default_input_data()

def default_input_data() -> InputData:
    """返回所有字段为非零默认值的 InputData"""
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

# ─── 结果保存与加载 ───
def save_result_download(input_data: InputData, result: SimulationResult) -> str:
    """生成完整结果 JSON 字符串（供 st.download_button 使用）"""
    payload = {
        "version": "1.0",
        "save_time": datetime.now().isoformat(),
        "input": input_data_to_dict(input_data),
        "result": result_to_dict(result),
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)

def export_csv(years: list[SimulationYear]) -> bytes:
    """导出年度明细为 CSV 字节流"""
    df = pd.DataFrame([asdict(y) for y in years])
    return df.to_csv(index=False).encode("utf-8-sig")

def export_excel(years: list[SimulationYear]) -> bytes:
    """导出年度明细为 Excel 字节流"""
    df = pd.DataFrame([asdict(y) for y in years])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="模拟明细")
    return output.getvalue()

# ─── 序列化辅助 ───
def input_data_to_dict(input_data: InputData) -> dict:
    """将 InputData 递归转换为可 JSON 序列化的 dict"""
    ...

def dict_to_input_data(data: dict) -> InputData:
    """从 dict 递归重建 InputData"""
    ...

def result_to_dict(result: SimulationResult) -> dict:
    ...
```

#### 3.5.2 保存/加载按钮（在 app.py 中调用）

```python
# 保存参数（侧边栏或主界面）
if st.button("💾 保存参数"):
    save_config(st.session_state.input_data)
    st.toast("参数已保存", icon="✅")

# 保存结果（下载按钮）
st.download_button(
    "💾 保存结果",
    data=save_result_download(input_data, result),
    file_name=f"财务自由评估_{datetime.now().strftime('%Y%m%d')}.json",
    mime="application/json",
)

# 导出 CSV
st.download_button(
    "📥 导出 CSV",
    data=export_csv(result.years),
    file_name=f"模拟明细_{datetime.now().strftime('%Y%m%d')}.csv",
    mime="text/csv",
)

# 导出 Excel
st.download_button(
    "📥 导出 Excel",
    data=export_excel(result.years),
    file_name=f"模拟明细_{datetime.now().strftime('%Y%m%d')}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

# 加载结果
uploaded = st.file_uploader("📂 加载结果", type=["json"])
if uploaded:
    data = json.load(uploaded)
    # 重建 input_data 和 result 并写入 session_state
    st.session_state.input_data = dict_to_input_data(data["input"])
    st.session_state.result = dict_to_result(data["result"])
    st.rerun()
```

---

### 3.6 utils/helpers.py — 工具函数

```python
def inflation_factor(rate: float, years_elapsed: int) -> float:
    """计算 (1 + rate)^years_elapsed"""
    return (1 + rate) ** years_elapsed

def is_in_education_stage(child_age: int, stage_start: int, stage_duration: int) -> bool:
    """判断小孩年龄是否处于某个教育阶段"""
    return stage_start <= child_age < stage_start + stage_duration

def years_until_retirement(current_age: int, retirement_age: int) -> int:
    """距离退休还有多少年（最低 0）"""
    return max(0, retirement_age - current_age)

def format_currency(value: float) -> str:
    """格式化金额：1234567 → '1,234,567'"""
    return f"{value:,.0f}"
```

---

## 4. app.py — 主入口

### 4.1 整体结构

```python
import streamlit as st

from modules.input_module import render_sidebar, validate_input
from modules.calculator import run_simulation
from modules.display_module import render_dashboard
from modules.io_module import (
    load_config, save_config,
    save_result_download, export_csv, export_excel,
)
from models.datamodels import InputData

# ─── 页面配置 ───
st.set_page_config(
    page_title="财务自由模拟评估",
    page_icon="💰",
    layout="wide",
)

# ─── 初始化 Session State ───
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.input_data = load_config() or default_input_data()
    st.session_state.result = None

# ─── 主界面标题 ───
st.title("💰 财务自由模拟评估系统")
st.markdown("---")

# ─── 侧边栏输入 ───
with st.sidebar:
    st.header("📋 输入参数")
    input_data = render_sidebar()

# ─── 校验与计算 ───
errors = validate_input(input_data)
if errors:
    for err in errors:
        st.error(err)
else:
    # 如果输入有变化，重新计算
    if (st.session_state.result is None or
        input_data != st.session_state.input_data):
        st.session_state.input_data = input_data
        with st.spinner("正在模拟计算..."):
            st.session_state.result = run_simulation(input_data)
        # 自动保存参数
        save_config(input_data)

    # ─── 显示结果 ───
    if st.session_state.result:
        render_dashboard(st.session_state.result, input_data)

        # ─── 底部操作区 ───
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            result_json = save_result_download(input_data, st.session_state.result)
            st.download_button("💾 保存结果", result_json,
                               f"评估结果_{datetime.now():%Y%m%d}.json")
        with col2:
            csv_data = export_csv(st.session_state.result.years)
            st.download_button("📥 导出 CSV", csv_data,
                               f"模拟明细_{datetime.now():%Y%m%d}.csv")
        with col3:
            xlsx_data = export_excel(st.session_state.result.years)
            st.download_button("📥 导出 Excel", xlsx_data,
                               f"模拟明细_{datetime.now():%Y%m%d}.xlsx")
        with col4:
            uploaded = st.file_uploader("📂 加载结果", type=["json"])
            if uploaded:
                data = json.load(uploaded)
                st.session_state.input_data = dict_to_input_data(data["input"])
                st.session_state.result = dict_to_result(data["result"])
                st.rerun()
```

### 4.2 启动命令

```bash
streamlit run app.py
```

---

## 5. 注意事项与边界处理

| 场景 | 处理方式 |
|------|----------|
| 年龄 > 预期寿命 | 校验拦截，提示错误 |
| 所有收入为 0 | 允许，评估结果必然为「未达成」 |
| 小孩年龄已超过大学阶段 | 教育费用为 0，仅触发赞助费 |
| 月消费为 0 | 允许（极端情况） |
| 模拟年限为 0 | 当年龄已 ≥ 预期寿命时，直接判定为自由 |
| config.json 损坏 | 在 `load_config` 中 try/except，回退默认值并提示 |
| 初始净资产为负 | 允许，评估结果大概率未达成 |
| 通胀率或收益率为负 | 允许，但校验不超出合理范围（-5% ~ 20%） |
| 小孩教育阶段索引变更 | 学前作为第 0 个阶段，小学/中学/大学分别变为 1/2/3 |
| 参数持久化路径 | 存储到 `%USERPROFILE%\.finfreedom_config.json` |

---

## 6. UI 组件树

```
┌─ Streamlit App ─────────────────────────────────────────────┐
│  sidebar                                                      │
│  ├─ 📋 输入参数                                              │
│  │  ├─ ⬇ 评估对象 (expander)                                │
│  │  ├─ ⬇ 资产与负债 (expander)                              │
│  │  ├─ ⬇ 持续收入 (expander)                                │
│  │  ├─ ⬇ 生活支出 (expander)                                │
│  │  ├─ ⬇ 小孩抚养 (expander)                                │
│  │  │  └─ 小孩 1..N (动态 container)                        │
│  │  ├─ ⬇ 意外预留 (expander)                                │
│  │  └─ ⬇ 经济参数 (expander)                                │
│  │  [💾 保存参数] [🔄 重新计算]                              │
│                                                               │
│  main                                                         │
│  ├─ 💰 财务自由模拟评估系统 (title)                          │
│  ├─ 结果概览卡                                                │
│  │  ├─ ✅/❌ 判定结果                                         │
│  │  └─ 4 个 metric: 初始净资产 / 总收入 / 总支出 / 最终       │
│  ├─ 图表区 (2列)                                              │
│  │  ├─ 净资产趋势折线图 (Plotly)                              │
│  │  └─ 年度收支对比柱状图 (Plotly)                            │
│  │  └─ [⬇ 收支构成分析] (可选饼图, expander)                │
│  ├─ 年度明细表 (st.dataframe)                                 │
│  └─ 底部操作区                                                │
│     [💾 保存结果] [📥 导出 CSV] [📥 导出 Excel] [📂 加载]    │
└──────────────────────────────────────────────────────────────┘
```

---

## 7. 实现顺序

为降低风险，建议按以下阶段依次实现：

| 阶段 | 任务 | 产出物 | 检验标准 |
|------|------|--------|----------|
| **P0** | 数据模型 + 工具函数 | `models/datamodels.py`, `utils/helpers.py` | dataclass 可正确序列化/反序列化，工具函数单元测试通过 |
| **P1** | 计算引擎 | `modules/calculator.py` | 对已知输入可计算出正确的逐年结果，边界 case 覆盖 |
| **P2** | 输入模块 | `modules/input_module.py` | 侧边栏渲染完整，默认值正确，校验生效 |
| **P3** | IO 模块 (config) | `modules/io_module.py` | 保存/加载 config.json 正确，启动自动恢复参数 |
| **P4** | 显示模块 + IO 导出 | `modules/display_module.py`, IO 剩余功能 | 图表、表格、概览卡渲染正确，CSV/Excel 下载可用 |
| **P5** | app.py 主入口组装 | `app.py` | 全链路可运行，保存/加载结果功能正常 |

---

## 8. 文件结构

```
FinFreedom/
├── app.py                    # Streamlit 主入口
├── launcher.py               # PyInstaller 打包启动脚本
├── FinFreedom.spec           # PyInstaller 规范文件
├── 重打包.bat                # 一键重新打包脚本
├── 启动.bat                  # 开发模式启动脚本
├── requirements.txt          # Python 依赖清单
├── Design.md                 # 本设计文档
├── SPEC.md                   # 需求规格说明
├── package-exe.md            # 打包发布详细说明
├── FinFreedom_chat.md        # 开发对话记录
├── models/
│   └── datamodels.py         # 所有数据模型定义
├── modules/
│   ├── input_module.py       # 侧边栏输入表单
│   ├── calculator.py         # 逐年模拟计算引擎
│   ├── display_module.py     # 结果展示（图表/表格）
│   └── io_module.py          # JSON 持久化、CSV/Excel 导出
├── utils/
│   └── helpers.py            # 工具函数
├── build/                    # PyInstaller 构建中间产物
└── dist/
    └── 财务自由评估/         # PyInstaller onedir 打包产物
```

### 6.1 各文件职责

| 文件 | 职责 |
|------|------|
| `app.py` | Streamlit 应用入口，组装各模块，管理 Session State |
| `launcher.py` | PyInstaller 打包入口，启动 Streamlit 子进程 |
| `FinFreedom.spec` | PyInstaller 打包配置，包含数据文件和隐藏导入 |
| `重打包.bat` | 一键执行 `python -m PyInstaller --clean --noconfirm FinFreedom.spec` |
| `启动.bat` | 开发模式一键启动 `streamlit run app.py` |
| `models/datamodels.py` | 所有 dataclass 模型定义，含 to_dict/from_dict 序列化 |
| `modules/input_module.py` | 侧边栏输入表单渲染、数据校验、按钮操作 |
| `modules/calculator.py` | 逐年模拟计算引擎，通胀调整，财务自由判定 |
| `modules/display_module.py` | 主界面结果展示：概览卡、Plotly 图表、明细表 |
| `modules/io_module.py` | 参数 JSON 持久化（用户目录）、CSV/Excel 导出 |
| `utils/helpers.py` | 通用工具函数（通胀因子、格式化等） |

---

## 7. 依赖清单 （requirements.txt）

```
python>=3.10
streamlit>=1.28
pandas>=2.0
plotly>=5.15
openpyxl>=3.1
```

---

## 9. 打包发布

使用 PyInstaller `onedir` 模式，入口为 `launcher.py`，配置在 `FinFreedom.spec`。

**关键配置要点：**
- `collect_data_files('streamlit')` — 打包前端静态文件（缺失则页面 Not Found）
- `collect_submodules('streamlit')` — 递归收集所有 Streamlit 子模块（缺失则 ModuleNotFoundError）
- `copy_metadata(...)` — 各依赖包的 dist-info（缺失则 PackageNotFoundError）
- 显式添加 conda 环境缺失 DLL（libcrypto, libssl, sqlite3 等）
- `COLLECT` 块实现 onedir 模式（onefile 模式 Streamlit 页面 Not Found）
- 端口固定 3568，环境变量 `STREAMLIT_GLOBAL_DEVELOPMENT_MODE=false`

**一键重打包：** `重打包.bat` 或 `python -m PyInstaller --clean --noconfirm FinFreedom.spec`

产物为 `dist/财务自由评估/` 文件夹，分发整个文件夹即可。

详见 `package-exe.md`。

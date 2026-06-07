from dataclasses import dataclass, field, asdict
from typing import Optional
import json


@dataclass
class EducationStage:
    name: str
    start_age: int
    duration: int
    annual_cost: float

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "EducationStage":
        return cls(**data)


@dataclass
class Child:
    current_age: int
    education_stages: list[EducationStage] = field(default_factory=list)
    graduation_sponsorship: float = 0.0

    def to_dict(self) -> dict:
        d = asdict(self)
        d["education_stages"] = [s.to_dict() for s in self.education_stages]
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "Child":
        stages_data = data.pop("education_stages", [])
        child = cls(**data)
        child.education_stages = [EducationStage.from_dict(s) for s in stages_data]
        return child


@dataclass
class Person:
    name: str
    current_age: int
    retirement_age: int
    life_expectancy: int

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Person":
        return cls(**data)


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

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "FamilyFinance":
        return cls(**data)


@dataclass
class Income:
    salary_annual: float = 0.0
    rental_annual: float = 0.0
    dividend_annual: float = 0.0
    other_annual: float = 0.0

    @property
    def total(self) -> float:
        return self.salary_annual + self.rental_annual + self.dividend_annual + self.other_annual

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Income":
        return cls(**data)


@dataclass
class EmergencyReserve:
    amount: float = 0.0
    mode: str = "一次性扣除"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "EmergencyReserve":
        return cls(**data)


@dataclass
class EconParams:
    inflation_rate: float = 0.02
    asset_return_rate: float = 0.02

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "EconParams":
        return cls(**data)


@dataclass
class InputData:
    evaluation_mode: str
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

    def to_dict(self) -> dict:
        return {
            "evaluation_mode": self.evaluation_mode,
            "your_age": self.your_age,
            "spouse_age": self.spouse_age,
            "retirement_age": self.retirement_age,
            "life_expectancy": self.life_expectancy,
            "finance": self.finance.to_dict(),
            "income": self.income.to_dict(),
            "monthly_expense": self.monthly_expense,
            "children": [c.to_dict() for c in self.children],
            "emergency_reserve": self.emergency_reserve.to_dict(),
            "params": self.params.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "InputData":
        return cls(
            evaluation_mode=data["evaluation_mode"],
            your_age=data["your_age"],
            spouse_age=data.get("spouse_age"),
            retirement_age=data["retirement_age"],
            life_expectancy=data["life_expectancy"],
            finance=FamilyFinance.from_dict(data["finance"]),
            income=Income.from_dict(data["income"]),
            monthly_expense=data["monthly_expense"],
            children=[Child.from_dict(c) for c in data.get("children", [])],
            emergency_reserve=EmergencyReserve.from_dict(data["emergency_reserve"]),
            params=EconParams.from_dict(data["params"]),
        )


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

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "SimulationYear":
        return cls(**data)


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

    def to_dict(self) -> dict:
        return {
            "years": [y.to_dict() for y in self.years],
            "is_financially_free": self.is_financially_free,
            "shortfall_amount": self.shortfall_amount,
            "shortfall_year": self.shortfall_year,
            "total_income_all": self.total_income_all,
            "total_expense_all": self.total_expense_all,
            "initial_net_worth": self.initial_net_worth,
            "final_net_worth": self.final_net_worth,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SimulationResult":
        return cls(
            years=[SimulationYear.from_dict(y) for y in data["years"]],
            is_financially_free=data["is_financially_free"],
            shortfall_amount=data["shortfall_amount"],
            shortfall_year=data.get("shortfall_year"),
            total_income_all=data["total_income_all"],
            total_expense_all=data["total_expense_all"],
            initial_net_worth=data["initial_net_worth"],
            final_net_worth=data["final_net_worth"],
        )

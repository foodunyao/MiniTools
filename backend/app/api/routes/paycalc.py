from typing import Any
from fastapi import APIRouter
from services.pay_calculator import calculate_pay

router = APIRouter(prefix="/paycalc")


@router.get("/list")
async def list_shifts():
    return ["kek", "lol"]


@router.post("/calc", response_model=Any)
async def compute_pay(query: Any):
    """Compute pay summary for provided shifts."""
    summary = calculate_pay(query.shifts)
    return summary

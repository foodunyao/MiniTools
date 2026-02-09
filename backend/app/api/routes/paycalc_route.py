from typing import List
from fastapi import APIRouter
from app.services.pay_calculator import calculate_pay
from app.models.schemas.paycalc_schema import ShiftSchema, PayCalcResponse

router = APIRouter(prefix="/paycalc")


@router.get("/list")
async def list_shifts():
    return ["kek", "lol"]


@router.post("/calc", response_model=PayCalcResponse)
async def compute_pay(query: List[ShiftSchema]):
    """Compute pay summary for provided shifts."""
    summary = calculate_pay(query)
    return summary

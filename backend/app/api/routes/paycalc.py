from fastapi import APIRouter
from models.schemas.paycalc_schema import PayQuery, PaySummary
from services.pay_calculator import calculate_pay

router = APIRouter(prefix="/paycalc")


@router.get('/list')
async def list_shifts():
    return ['kek', 'lol']


@router.post('/calc', response_model=PaySummary)
async def compute_pay(query: PayQuery):
    """Compute pay summary for provided shifts."""
    summary = calculate_pay(query.shifts)
    return summary
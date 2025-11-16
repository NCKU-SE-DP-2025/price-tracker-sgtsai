from fastapi import APIRouter, Query
from app.services.price_service import PriceService

router = APIRouter()

@router.get("/necessities")
def get_necessities_prices(
    category: str = Query(None),
    commodity: str = Query(None)
):
    return PriceService.get_necessities_prices(category, commodity)

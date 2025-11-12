import requests

class PriceService:
    @staticmethod
    def get_necessities_prices(category: str = None, commodity: str = None) -> dict:
        response = requests.get(
            "https://opendata.ey.gov.tw/api/ConsumerProtection/NecessitiesPrice",
            params={"CategoryName": category, "Name": commodity}
        )
        return response.json()

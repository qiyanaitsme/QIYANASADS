import requests
from config import TRANSFER_TOKEN, SECRET_ANSWER


class PaymentAPI:
    def __init__(self):
        self.headers = {
            "accept": "application/json",
            "authorization": f"Bearer {TRANSFER_TOKEN}"
        }

    async def send_payment(self, user_id, amount):
        url = "https://api.lzt.market/balance/transfer"

        params = {
            "user_id": user_id,
            "amount": amount,
            "currency": "rub",
            "secret_answer": SECRET_ANSWER,
            "comment": f"{user_id}_реклама_срок_месяц_с_момента_получения_средств_для_рекламы",
            "transfer_hold": "true",
            "hold_length_value": "1",
            "hold_length_option": "day"
        }

        try:
            response = requests.post(url, headers=self.headers, params=params)
            return response.json()
        except Exception as e:
            print(f"Payment API error: {e}")
            return None
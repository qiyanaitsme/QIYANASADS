import requests


class ZelenkaAPI:
    def __init__(self, token):
        self.token = token
        self.headers = {
            "accept": "application/json",
            "authorization": f"Bearer {token}"
        }

    async def get_user_id(self, username):
        url = 'https://api.zelenka.guru/users/find'
        params = {'username': username}

        try:
            response = requests.get(url, params=params, headers=self.headers)
            data = response.json()
            return str(data['users'][0]['user_id']) if data.get('users') else None
        except Exception as e:
            print(f"Debug: API error - {str(e)}")
            return None

    async def get_profile_data(self, user_id):
        url = f"https://api.zelenka.guru/users/{user_id}/profile-posts"
        try:
            response = requests.get(url, headers=self.headers)
            return response.json()
        except Exception as e:
            print(f"Debug: API error - {str(e)}")
            return None
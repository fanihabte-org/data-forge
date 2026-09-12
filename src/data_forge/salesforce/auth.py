import requests
from dataclasses import dataclass


@dataclass(frozen=True)
class Auth:
    client_id: str
    client_secret: str
    grant_type: str
    base_url: str

    def get_token(self):
        post_kwargs = {
            "url": f"{self.base_url}/services/oauth2/token",
            "data": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": self.grant_type,
            }
        }

        sec_response = requests.post(**post_kwargs)
        sec_response.raise_for_status()

        token_data = sec_response.json()
        return token_data["access_token"]

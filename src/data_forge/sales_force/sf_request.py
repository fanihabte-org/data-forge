import requests

from dataclasses import dataclass
from data_forge.sales_force.auth import Auth


@dataclass
class SalesForceRequest:
    auth: Auth

    @staticmethod
    def request_json(kwargs):
        response = requests.get(**kwargs)
        response.raise_for_status()

        return response.json()

    @staticmethod
    def post_request(kwargs):
        print(kwargs)
        response = requests.post(**kwargs)
        response.raise_for_status()

        return response.json()

    @staticmethod
    def request(kwargs):
        requests.get(kwargs)

    def soql_request_kwargs(self, soql_query: str) -> dict:
        token = self.auth.get_token()
        base_url = self.auth.base_url

        header = {"Authorization": f"Bearer {token}"}
        endpoint = "/services/data/v60.0/queryAll"
        params = {"q": soql_query}

        return {
            "url": f"{base_url}{endpoint}",
            "headers": header,
            "params": params
        }

    def bulk_request_kwargs(self, soql_query: str):
        token = self.auth.get_token()
        base_url = self.auth.base_url

        header = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        json_obj = {
            "operation": "query",
            "query": soql_query
        }
        endpoint = "/services/data/v60.0/jobs/query"

        return {
            "url": f"{base_url}{endpoint}",
            "headers": header,
            "json": json_obj
        }

    def bulk_export_job_state_kwargs(self, job_id: str):
        token = self.auth.get_token()
        base_url = self.auth.base_url

        header = {"Authorization": f"Bearer {token}"}
        endpoint = f"/services/data/v60.0/jobs/query/{job_id}"

        return {
            "url": f"{base_url}{endpoint}",
            "headers": header,
        }

    def build_bulk_export_results_kwargs(self, job_id: str, file_number: int):
        token = self.auth.get_token()
        base_url = self.auth.base_url

        header = {"Authorization": f"Bearer {token}"}
        endpoint = f"/services/data/v60.0/jobs/query/{job_id}"
        url = f"{base_url}{endpoint}/results/?locator={file_number}"
        if file_number == 0:
            url = f"{base_url}{endpoint}/results"

        return {
            "url": url,
            "headers": header,
            "stream": True
        }

    def build_pagination_kwargs(self, next_url: str) -> dict:
        token = self.auth.get_token()
        base_url = self.auth.base_url
        headers = {"Authorization": f"Bearer {token}"}

        return {
            "url": base_url + next_url,
            "headers": headers
        }

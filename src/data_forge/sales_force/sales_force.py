from datetime import datetime
from pathlib import Path
from time import sleep

import requests

from dataclasses import dataclass
from data_forge.sales_force.auth import Auth
from src.data_forge.context.context import Context
from data_forge.util.query_builder import select_all_query


@dataclass(frozen=True)
class SalesForce:
    context: Context
    auth: Auth
    source: str = "crm"

    def _soql_request_kwargs(self, table_name: str) -> dict:
        token = self.auth.get_token()
        base_url = self.context.base_url

        sql_query = select_all_query(
            table_name=table_name,
            columns=self.context.get_columns(table_name, self.source),
            source=self.source
        )

        header = {"Authorization": f"Bearer {token}"}
        endpoint = "/services/data/v60.0/queryAll"
        params = {"q": sql_query}

        return {
            "url": f"{base_url}{endpoint}",
            "headers": header,
            "params": params
        }

    def _bulk_request_kwargs(self, table_name: str):
        token = self.auth.get_token()
        base_url = self.context.base_url

        sql_query = select_all_query(
            table_name=table_name,
            columns=self.context.get_columns(table_name, self.source),
            source=self.source
        )

        header = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        json_obj = {
            "operation": "query",
            "query": sql_query
        }
        endpoint = "/services/data/v60.0/jobs/query"

        return {
            "url": f"{base_url}{endpoint}",
            "headers": header,
            "json": json_obj
        }

    def _bulk_export_job_state_kwargs(self, job_id: str):
        token = self.auth.get_token()
        base_url = self.context.base_url

        header = {"Authorization": f"Bearer {token}"}
        endpoint = f"/services/data/v60.0/jobs/query/{job_id}"

        return {
            "url": f"{base_url}{endpoint}",
            "headers": header,
        }

    def _build_bulk_export_results_kwargs(self, job_id: str, file_number: int):
        token = self.auth.get_token()
        base_url = self.context.base_url

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

    def _build_pagination_kwargs(self, next_url: str) -> dict:
        token = self.auth.get_token()
        base_url = self.context.base_url
        headers = {"Authorization": f"Bearer {token}"}

        return {
            "url": base_url + next_url,
            "headers": headers
        }

    def _check_export_status(self, job_id) -> bool:
        while True:
            kwargs = self._bulk_export_job_state_kwargs(job_id=job_id)

            response = _request_json(kwargs=kwargs)
            job_status = response["state"]

            if job_status == "JobComplete":
                return True

            sleep(30)

    def fetch_data_from_table(self, table_name) -> None:
        soql_kwargs = self._soql_request_kwargs(table_name=table_name)
        json_response = _request_json(kwargs=soql_kwargs)

        return self._process_response(json_response)

    def fetch_all_data(self) -> None:
        tables = self.context.tables

        for table in tables:
            self.fetch_data_from_table(table_name=table)

    def request_bulk_export(self, table_name: str, folder_path: Path) -> None:
        blk_req_kwargs = self._bulk_request_kwargs(table_name=table_name)
        json_response = _post_request(kwargs=blk_req_kwargs)
        job_id = json_response["id"]

        is_export_done = self._check_export_status(job_id=job_id)
        if is_export_done:
            file_number = 0
            download_dir = _setup_dir(folder_path=folder_path, job_id=job_id, table_name=table_name)

            while True:
                download_kwargs = self._build_bulk_export_results_kwargs(job_id=job_id, file_number=file_number)

                is_done = _download_bulk_export(
                    download_dir=download_dir,
                    kwargs=download_kwargs,
                    file_number=file_number,
                    table_name=table_name,
                    chunk_size=self.context.chunk_size
                )

                if is_done:
                    break

                file_number += 1

            print("Files has been downloaded!")

    def _paginate_pages(self, json_response: dict) -> None:
        data_records, api_call_count = json_response["records"], 1
        records_count = len(data_records)

        while True:
            # request next page
            next_page = self._fetch_next_page_from(response=json_response)
            next_page_records = next_page["records"]
            no_next_page = next_page["done"]

            # add page to list
            data_records.extend(next_page_records)

            # if a divisible by 10 api calls are made process the data in the list
            if api_call_count % 10 == 0:
                self._write_to_db(data_records)
                data_records.clear()

            # increment count values
            api_call_count += 1
            records_count += len(next_page_records)

            # check if we have 120 calls and sleep for a min with 10 seconds as buffer
            if api_call_count % 120 == 0:
                print(
                    f"Sleeping for 70 seconds given that 120 calls per min limit as been reached. "
                    f"Current cumulative api call count is {api_call_count}")
                sleep(70)

            # check if we have reached at the end of the page
            if no_next_page:
                print(f"\nSuccessfully completed fetching all {records_count} records!")
                break

            # check if user made more than 12 api calls
            if api_call_count >= 20:
                print("\nWARNING: You have made more than 12 api calls, please consider using bulk export.")
                break

    def _fetch_next_page_from(self, response: dict) -> dict:
        next_url = response["nextRecordsUrl"]
        next_req_kwargs = self._build_pagination_kwargs(next_url=next_url)
        return _request_json(kwargs=next_req_kwargs)

    def _process_response(self, json_response: dict):
        # process first record
        self._write_to_db(json_response["records"])

        # is there are records then paginate
        if not json_response["done"]:
            self._paginate_pages(json_response)

    def _write_to_db(self, all_records: list):
        print(f"Loaded {len(all_records)} records")


def _request_json(kwargs):
    response = requests.get(**kwargs)
    response.raise_for_status()

    return response.json()


def _setup_dir(folder_path: Path, job_id: int, table_name: str) -> Path:
    current_time = datetime.now()
    today_dir = folder_path / current_time.strftime("%Y/%m/%d")
    job_folder_path = today_dir / table_name / str(job_id)

    job_folder_path.mkdir(parents=True, exist_ok=True)

    return job_folder_path


def _build_file_path(table_name: str, folder_path: Path, file_number: int) -> Path:
    clean_table_name = table_name.lower().replace(" ", "_")
    file_name = f"{clean_table_name}_{file_number}.csv"

    return folder_path / file_name


def _download_bulk_export(kwargs, download_dir: Path, table_name: str, file_number: int, chunk_size: int) -> bool:
    file_path = _build_file_path(table_name=table_name, folder_path=download_dir, file_number=file_number)
    with requests.get(**kwargs) as response:
        if response.status_code == 400:
            return True

        if response.status_code == 429:
            sleep(70)

        with pl.read_csv(response.raw, chunksize=chunk_size) as reader:
            for chunk_df in reader:
                if file_path.exists():
                    chunk_df.to_csv(file_path, mode="a")
                else:
                    chunk_df.to_csv(file_path)

        print(f"Completed downloading file number {file_number}")

    return False


def _post_request(kwargs):
    response = requests.post(**kwargs)
    response.raise_for_status()

    return response.json()

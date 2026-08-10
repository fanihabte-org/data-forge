from dataclasses import dataclass
from datetime import datetime
from time import sleep

from data_forge.FileStorage.FileStorage import FileStorage
from data_forge.db_engine.db_super_class import SourceInterface
from data_forge.logging.watermark import Watermark
from data_forge.sales_force.sf_request import SalesForceRequest
from data_forge.sales_force.sf_soql_builder import select_all_after_watermark, select_all_query
from src.data_forge.context.context import Context

@dataclass
class SalesForce(SourceInterface):
    context: Context
    source: str
    file_storage: FileStorage
    sf_request: SalesForceRequest

    def bulk_export_all(self, run_datetime: datetime, table_name: str):
        columns = self.context.get_columns(table_name=table_name, source=self.source)
        soql_query = select_all_query(table_name=table_name, columns=columns)

        self._request_bulk_download(soql_query=soql_query, table_name=table_name)

    def extract_after_watermark(self, run_datetime: datetime, watermark: Watermark):
        columns = self.context.get_columns(table_name=watermark.table_name, source=self.source)
        soql_query = select_all_after_watermark(watermark=watermark, columns=columns)
        soql_kwargs = self.sf_request.soql_request_kwargs(soql_query=soql_query)
        json_response = self.sf_request.request_json(kwargs=soql_kwargs)

        return self._paginate_pages(json_response)

    def bulk_export_after_watermark(self, run_datetime: datetime, watermark: Watermark):
        columns = self.context.get_columns(table_name=watermark.table_name, source=self.source)
        soql_query = select_all_after_watermark(watermark=watermark, columns=columns)

        self._request_bulk_download(table_name=watermark.table_name, soql_query=soql_query)

    ## ------------------------------------------------------------------------------------- ##

    def _request_bulk_download(self, soql_query: str, table_name: str):
        blk_req_kwargs = self.sf_request.bulk_request_kwargs(soql_query=soql_query)
        json_response = self.sf_request.post_request(kwargs=blk_req_kwargs)

        self._process_download(job_id=json_response["id"], table_name=table_name)

    def _process_download(self, job_id, table_name):
        is_export_done = self._check_export_status(job_id=job_id)

        if is_export_done:
            file_number = 0
            while True:
                download_kwargs = self.sf_request.build_bulk_export_results_kwargs(job_id=job_id,
                                                                                   file_number=file_number)

                is_done = self._download_bulk_export(
                    kwargs=download_kwargs,
                    file_number=file_number,
                    table_name=table_name,
                    job_id=job_id
                )

                if is_done:
                    break

                file_number += 1

            print("Files has been downloaded!")

    def _check_export_status(self, job_id) -> bool:
        while True:
            kwargs = self.sf_request.bulk_export_job_state_kwargs(job_id=job_id)

            response = self.sf_request.request_json(kwargs=kwargs)
            job_status = response["state"]

            if job_status == "JobComplete":
                return True

            sleep(30)

    def _paginate_pages(self, json_response: dict):
        data_records_list, records, api_call_count = [], json_response["records"], 1
        records_count, is_done = 0, json_response["done"]

        while not is_done:
            # add page to list
            data_records_list.append(records)

            # check if we have 120 calls and sleep for a min with 10 seconds as buffer
            if api_call_count % 120 == 0:
                print(
                    f"Sleeping for 70 seconds given that 120 calls per min limit as been reached. "
                    f"Current cumulative api call count is {api_call_count}")
                sleep(70)

            # check if user made more than 20 api calls
            if api_call_count >= 20:
                print(
                    "\nWARNING: You have made 20 api calls and still have remaining pages, please consider using bulk export.")

            # fetch next page from the recent response
            json_response = self._fetch_next_page_from(response=json_response)
            records = json_response["records"]
            is_not_done = json_response["done"]

            # increment count values
            api_call_count += 1
            records_count += len(records)

        print(f"\nSuccessfully completed fetching all {records_count} records!")
        return data_records_list

    def _fetch_next_page_from(self, response: dict) -> dict:
        next_url = response["nextRecordsUrl"]
        next_req_kwargs = self.sf_request.build_pagination_kwargs(next_url=next_url)
        return self.sf_request.request_json(kwargs=next_req_kwargs)

    def _download_bulk_export(self, kwargs: dict, table_name: str, file_number: int, job_id) -> bool:

        with self.sf_request.request(kwargs=kwargs) as response:
            if response.status_code == 400:
                return True

            if response.status_code == 429:
                sleep(70)

            self.file_storage.save_to_csv_file(response, table_name, file_number, job_id)

        return False

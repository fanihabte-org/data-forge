from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

@dataclass
class FileStorage:
    export_path: str
    chunk_size: int

    def setup_export_dir(self, job_id: int, table_name: str):
        today_dir = Path(self.export_path) / datetime.now().strftime("%Y/%m/%d")
        job_folder_path = today_dir / table_name / str(job_id)

        job_folder_path.mkdir(parents=True, exist_ok=True)

        return job_folder_path

    def setup_csv_file_path(self, table_name: str, file_number: int, job_id: int) -> Path:
        clean_table_name = table_name.lower().replace(" ", "_")
        file_name = f"{clean_table_name}_{file_number}.csv"

        return self.setup_export_dir(job_id=job_id, table_name=table_name) / file_name

    def save_to_csv_file(self, response, table_name, file_number, job_id):
        file_path = self.setup_csv_file_path(table_name=table_name, file_number=file_number, job_id=job_id)

        with open(file_path, "wb") as download_file:
            for chunk in response.iter_content(chunk_size=self.chunk_size):
                if file_path.exists() and chunk:
                    download_file.write(chunk)

        print(f"Completed downloading file number {file_number}")

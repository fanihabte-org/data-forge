class WatermarkNotAvailable(Exception):

    def __init__(self, table: str, msg: str = "When calling for incremental data export you should have a watermark",
                 error_code=1001):
        self.msg = msg
        self.table = table
        self.error_code = error_code
        super().__init__(self.msg)

    def __str__(self) -> str:
        return f"Table {self.table} doesn't have a watermark recorded yet. Please use bulk export functionality to do first time loading."

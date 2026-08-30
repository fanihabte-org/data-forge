from pydantic import BaseModel


class VolumeAnalysis(BaseModel):
    table_name: str
    schema_name: str
    egress_volume: int

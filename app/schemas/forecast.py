# app/schemas/forecast.py

from datetime import datetime
from pydantic import BaseModel


class ForecastRead(BaseModel):
    """
    Forecastレコード1件をJSONで返すときの形。
    """

    id: int
    run_time: datetime
    forecast_time: datetime
    lat: float
    lon: float
    temp_2m: float | None = None
    wind10m_u: float | None = None
    wind10m_v: float | None = None
    ghi: float | None = None

    class Config:
        orm_mode = True

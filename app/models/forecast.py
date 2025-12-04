# app/models/forecast.py

from sqlalchemy import Column, Integer, Float, DateTime
from core.db import Base


class Forecast(Base):
    """
    GRIB2由来の予報データ1点分（1格子・1時刻）のレコード。
    実務レベルで最低限ほしい軸：
      - run_time      : どの予報サイクル（例: 2025-12-03 00UTC）
      - forecast_time : その格子点の予報が指す時刻
      - lat, lon      : 緯度・経度
      - 各種変数      : 2m気温、風、日射など
    """

    __tablename__ = "forecasts"

    id = Column(Integer, primary_key=True, index=True)

    run_time = Column(DateTime, index=True, nullable=False)
    forecast_time = Column(DateTime, index=True, nullable=False)

    lat = Column(Float, index=True, nullable=False)
    lon = Column(Float, index=True, nullable=False)

    # 実際の物理量（必要に応じて増やせる）
    temp_2m = Column(Float, nullable=True)      # 2m気温 [℃]
    wind10m_u = Column(Float, nullable=True)    # 10m風U成分 [m/s]
    wind10m_v = Column(Float, nullable=True)    # 10m風V成分 [m/s]
    ghi = Column(Float, nullable=True)          # 全球水平日射量 [W/m2]（仮）

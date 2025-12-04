# app/models/weather.py

"""
気象データのダミーテーブル用モデル。

将来的には:
- 緯度 / 経度
- 予報時刻
- 気温 / 風 / 日射 など

を持たせていけばOK。
ここではシンプルに temp(気温) と location だけ持つ。
"""

from sqlalchemy import Column, Integer, String, Float
from core.db import Base


class WeatherSample(Base):
    """
    weather_samples テーブルの ORM モデル。
    """

    __tablename__ = "weather_samples"

    id = Column(Integer, primary_key=True, index=True)
    location = Column(String(100), nullable=False, index=True)  # 地点名
    temp_c = Column(Float, nullable=False)                      # 気温[℃]

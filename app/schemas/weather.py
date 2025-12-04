# app/schemas/weather.py

"""
weather_samples テーブル用の Pydantic スキーマ定義。

FastAPI は:
- レスポンスの型ヒント（response_model）
- この BaseModel

を元に、JSON の形をチェック＆整形して返してくれる。
"""

from pydantic import BaseModel


class WeatherSampleRead(BaseModel):
    """
    レスポンス用の型。

    DB の weather_samples テーブルの1行に対応:
      - id: 主キー
      - location: 地点名
      - temp_c: 気温[℃]
    """

    id: int
    location: str
    temp_c: float

    class Config:
        # orm_mode=True にすると SQLAlchemy モデルからでも自動で変換してくれる
        orm_mode = True

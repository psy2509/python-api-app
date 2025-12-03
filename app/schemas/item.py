# app/schemas/item.py

"""
FastAPI がリクエスト/レスポンスをバリデーションするときに使う
Pydantic のモデル（スキーマ）を定義する。

ORM の Item モデルとは別に、
- 入力用 (ItemCreate)
- 出力用 (ItemRead)
などを用意して使い分ける。
"""

from typing import Optional  # Optional[str] = str または None
from pydantic import BaseModel


class ItemBase(BaseModel):
    """
    共有フィールドをまとめた基底クラス。
    継承して ItemCreate / ItemRead を作る。
    """

    name: str                   # 必須の文字列フィールド
    description: Optional[str]  # None 許可の文字列
    price: float                # 必須の float


class ItemCreate(ItemBase):
    """
    POST /items で使う「作成用」のスキーマ。
    ItemBase そのままで OK なので、中身は追加しない。
    """
    pass


class ItemRead(ItemBase):
    """
    レスポンス用スキーマ。

    DB には id カラムがあるが、作成時の入力には不要なので、
    出力用だけに id を持たせる。
    """

    id: int

    class Config:
        # orm_mode=True にすると、SQLAlchemy のモデルからでも
        # 自動的に Pydantic モデルに変換してくれる
        orm_mode = True

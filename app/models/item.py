# app/models/item.py

"""
SQLAlchemy の ORM モデル（= テーブル定義）を置くモジュール。

ここではシンプルに "items" テーブルを定義する。

- id: 主キー (int)
- name: アイテム名 (str)
- description: 説明 (str, NULL 可)
- price: 価格 (float)
"""

from sqlalchemy import Column, Integer, String, Float, Text
from core.db import Base  # さっき作った Base を継承する


class Item(Base):
    """
    Python のクラス定義:
        class クラス名(親クラス):
            クラス本体...

    Base を継承することで、SQLAlchemy に「これはテーブルだよ」と伝える。
    """

    # __tablename__ は、このクラスが対応するテーブル名を指定する特別な変数
    __tablename__ = "items"

    # Column(...) が「テーブルの列（カラム）」を表す
    # 第1引数: 型 (Integer, String, Float...)
    # primary_key=True で主キー（PK）になる
    id = Column(Integer, primary_key=True, index=True)

    # String(255) は最大長 255 文字の VARCHAR 的なイメージ
    name = Column(String(255), nullable=False, index=True)

    # Text は長い文字列用。nullable=True で NULL 許可
    description = Column(Text, nullable=True)

    # Float は浮動小数
    price = Column(Float, nullable=False)

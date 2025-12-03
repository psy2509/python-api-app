# app/core/db.py

"""
DB 接続まわりをまとめるモジュール。

- SQLAlchemy の "engine"（DBとの接続本体）
- SessionLocal（DBセッションを作るためのクラス）
- Base（モデルの基底クラス）

を定義する。

FastAPI からは:
  from core.db import Base, engine, SessionLocal
のように import して使う。
"""

import os  # 環境変数（os.getenv）を読むための標準ライブラリ
from sqlalchemy import create_engine  # DB 接続用のエンジンを作る関数
from sqlalchemy.orm import sessionmaker, declarative_base  # セッションとベースクラス用


# 環境変数から設定を読み込む（なければデフォルト値）
# os.getenv("キー", "デフォルト")
DB_USER = os.getenv("DB_USER", "weather")
DB_PASSWORD = os.getenv("DB_PASSWORD", "weatherpass")
DB_NAME = os.getenv("DB_NAME", "weatherdb")
DB_HOST = os.getenv("DB_HOST", "db")    # docker-compose のサービス名
DB_PORT = os.getenv("DB_PORT", "5432")


# f文字列: f"...{変数}..." で文字列に値を埋め込む
SQLALCHEMY_DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# create_engine(...) で DB と話すための本体を作る
# echo=True にすると実行される SQL がコンソールに出てきてデバッグに便利
engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True)

# sessionmaker は「Session クラスを作る工場」のようなもの
# ここで設定した内容を元に、あとで SessionLocal() でセッションインスタンスを作る
SessionLocal = sessionmaker(
    autocommit=False,  # 自動コミットしない（明示的に commit を呼ぶ）
    autoflush=False,   # 自動フラッシュもしない（基本これでOK）
    bind=engine,       # この Session は上で作った engine を使う
)

# declarative_base() は「全モデルの基底クラス」を作る関数
# この Base を継承したクラスがテーブルとして扱われる
Base = declarative_base()

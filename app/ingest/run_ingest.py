# app/ingest/run_ingest.py

from datetime import datetime

from sqlalchemy.orm import Session

from core.db import Base, engine, SessionLocal
from models.forecast import Forecast


def init_db() -> None:
    """
    Base を継承したすべてのモデルのテーブルを作成する。

    すでにテーブルが存在する場合は何もしないので、
    毎回呼んで OK。
    """
    Base.metadata.create_all(bind=engine)


def insert_dummy_forecasts(db: Session) -> None:
    """
    Forecast テーブルにダミーデータを数件だけ入れる。

    すでにレコードがある場合は何もしない。
    """
    count = db.query(Forecast).count()
    if count > 0:
        print(f"[ingest] forecasts already has {count} rows, skip insert.")
        return

    now = datetime.utcnow()

    rows = [
        Forecast(
            run_time=now,
            forecast_time=now,
            lat=35.0,
            lon=139.0,
            temp_2m=15.0,
            wind10m_u=1.0,
            wind10m_v=0.5,
            ghi=300.0,
        ),
        Forecast(
            run_time=now,
            forecast_time=now,
            lat=43.0,
            lon=141.0,
            temp_2m=5.0,
            wind10m_u=3.0,
            wind10m_v=-1.0,
            ghi=150.0,
        ),
    ]

    db.add_all(rows)
    db.commit()
    print("[ingest] inserted dummy forecast rows.")


def main() -> None:
    print("[ingest] Start ingest script.")
    init_db()

    db = SessionLocal()
    try:
        insert_dummy_forecasts(db)
    finally:
        db.close()

    print("[ingest] Done.")


if __name__ == "__main__":
    main()

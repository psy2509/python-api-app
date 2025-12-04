# app/main.py

from typing import List

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.db import Base, engine, SessionLocal
from models.item import Item
from schemas.item import ItemCreate, ItemRead
from models.weather import WeatherSample       
from schemas.weather import WeatherSampleRead 

from models.forecast import Forecast
from schemas.forecast import ForecastRead



Base.metadata.create_all(bind=engine)

app = FastAPI()


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def read_root():
    return {"message": "Hello from Docker FastAPI + PostgreSQL"}


@app.post("/items", response_model=ItemRead, status_code=status.HTTP_201_CREATED)
def create_item(item_in: ItemCreate, db: Session = Depends(get_db)):
    db_item = Item(**item_in.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@app.get("/items", response_model=List[ItemRead])
def list_items(db: Session = Depends(get_db)):
    return db.query(Item).all()


@app.get("/items/{item_id}", response_model=ItemRead)
def get_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@app.put("/items/{item_id}", response_model=ItemRead)
def update_item(item_id: int, item_in: ItemCreate, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    for field, value in item_in.dict().items():
        setattr(item, field, value)

    db.commit()
    db.refresh(item)
    return item


@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    db.delete(item)
    db.commit()
    # 204なので何も返さない

@app.get("/weather-samples", response_model=List[WeatherSampleRead])
def list_weather_samples(db: Session = Depends(get_db)):
    """
    weather_samples テーブルに入っている
    気象サンプルデータを全部返すエンドポイント。

    - Depends(get_db) で DB セッションを1つ受け取る
    - db.query(WeatherSample).all() で全件取得
    - そのリストを返すと、FastAPI が WeatherSampleRead のリストに変換して
      JSON としてクライアントに返してくれる。
    """
    samples = db.query(WeatherSample).all()
    return samples

@app.get("/forecasts", response_model=List[ForecastRead])
def list_forecasts(db: Session = Depends(get_db)):
    """
    Forecast テーブルに入っている予報データを全件返す。
    実務では本当に全件返すと重すぎるので、
    ページングや領域・時間フィルタを必ず入れる想定。
    ここでは「全データJSON」を経験するための実装。
    """
    forecasts = db.query(Forecast).all()
    return forecasts

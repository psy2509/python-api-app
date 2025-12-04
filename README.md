# python-api-app

# 気象予報API基盤 全体設計（Python / FastAPI / PostgreSQL / Docker）

## 1. ゴール

- 気象庁などから GRIB2（数値予報バイナリ）を定期的に取得する
- 取得した GRIB2 を保存しておき、予報の「根拠データ」として数ヶ月分保持する
- GRIB2 をパースして、地点ごとの予報値を PostgreSQL に格納する
- FastAPI で JSON API（例: `/forecasts`）を提供する
- 将来的にフィルタや高度なクエリ（地点・時間・モデル別など）に拡張できる設計にする

---

## 2. システム構成（Docker）

### 2.1 コンポーネント

`docker-compose.yml` で構成するサービス:

- `db`  
  - イメージ: `postgres:16`
  - 役割: 予報データ・根拠メタ情報を保存
  - データ永続化: volume `db-data`

- `api`  
  - ビルド: `Dockerfile.api`
  - 役割: FastAPI による API サーバー
  - 内容: Python, FastAPI, SQLAlchemy, Pydantic
  - 起動コマンド: `uvicorn main:app --host 0.0.0.0 --port 8000 --reload`

- `ingest`  
  - ビルド: `Dockerfile.ingest`
  - 役割: GRIB2 取得・保存・パース・DB への書き込みを行うバッチ
  - 内容: Python, `requests`, `xarray`, `cfgrib`, SQLAlchemy
  - `/data` にホスト `./data` をマウント
  - 起動コマンド: `python -m ingest.run_ingest`

### 2.2 共有ボリューム

- `db-data` : PostgreSQL 用
- `./data:/data` : GRIB2 などバイナリデータ保存用（ingest コンテナとホストで共有）

---

## 3. ディレクトリ構成

プロジェクトルート:

```text
python-api-app/
  docker-compose.yml
  Dockerfile.api
  Dockerfile.ingest
  requirements.txt
  app/
    main.py             # FastAPI エントリポイント
    core/
      db.py             # SQLAlchemy Engine / Session 設定
      config.py         # 設定値（DB URL, DATA_ROOT など）
    models/
      forecast.py       # Forecast / ForecastRun モデル
      item.py           # 学習用サンプル（任意）
    schemas/
      forecast.py       # Pydantic スキーマ
      item.py
    routers/
      forecasts.py      # /forecasts API
      items.py          # サンプル API
    ingest/
      run_ingest.py     # ingest メイン処理
      fetch_jma.py      # 気象庁から GRIB2 を取得（今後実装）
      parse_grib.py     # GRIB2 → Forecast 変換（今後実装）
  data/
    grib/               # GRIB2 生データ（/data/grib としてコンテナから参照）
    latest/             # 最新ファイルへのポインタ

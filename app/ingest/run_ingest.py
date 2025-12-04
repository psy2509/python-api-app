# app/ingest/run_ingest.py

from datetime import datetime
from pathlib import Path
import zipfile

import requests
import xarray as xr
from sqlalchemy.orm import Session

from core.db import Base, engine, SessionLocal
from models.forecast import Forecast


# 気象庁 GPV サンプル（GSM全球）の ZIP
JMA_GPV_GSM_GLOBAL_ZIP = (
    "https://www.data.jma.go.jp/developer/gpv_sample/gsm_gl.zip"
)

# /app 配下に data ディレクトリを掘ってそこに保存する
BASE_DIR = Path(__file__).resolve().parent.parent   # .../app
RAW_DIR = BASE_DIR / "data" / "raw" / "gsm_gl"
RAW_DIR.mkdir(parents=True, exist_ok=True)


def init_db() -> None:
    """
    Base を継承したすべてのモデルのテーブルを作成する。

    すでにテーブルが存在する場合は何もしないので、
    毎回呼んで OK。
    """
    Base.metadata.create_all(bind=engine)


# ===== ここから JMA サンプル用の処理を追加 =====

def download_sample_zip(url: str = JMA_GPV_GSM_GLOBAL_ZIP) -> Path:
    """
    気象庁の GPV サンプル ZIP を HTTP で取得して
    data/raw/gsm_gl/gsm_gl_sample.zip に保存する。
    """
    zip_path = RAW_DIR / "gsm_gl_sample.zip"

    print(f"[ingest] Downloading JMA sample ZIP: {url}")
    resp = requests.get(url, timeout=120)
    resp.raise_for_status()

    zip_path.write_bytes(resp.content)
    print(f"[ingest] Saved ZIP -> {zip_path}")
    return zip_path


def extract_first_grib(zip_path: Path) -> Path:
    """
    ZIP の中から .bin/.grib2/.grb2/.grb のどれかを探し、
    最初の1ファイルだけ data/raw/gsm_gl に展開する。
    """
    print(f"[ingest] Extracting GRIB from {zip_path}")
    with zipfile.ZipFile(zip_path, "r") as zf:
        members = zf.infolist()

        grib_members = [
            m
            for m in members
            if m.filename.lower().endswith(
                (".bin", ".grib2", ".grb2", ".grb")
            )
        ]
        if not grib_members:
            raise RuntimeError("ZIP 内に GRIB2/GRIB ファイルが見つかりません")

        target = grib_members[0]
        print(f"[ingest] Use member -> {target.filename}")

        out_path = RAW_DIR / Path(target.filename).name
        with zf.open(target, "r") as src, out_path.open("wb") as dst:
            dst.write(src.read())

    print(f"[ingest] Extracted GRIB -> {out_path}")
    return out_path


def open_dataset(grib_path: Path, filter_by_keys: dict | None = None) -> xr.Dataset:
    """
    GRIB2 を xarray+cfgrib で開く。
    filter_by_keys を指定すると、その条件に合うメッセージだけを読む。

    例:
      filter_by_keys={"stepType": "instant"}
      filter_by_keys={"stepType": "accum"}
    """
    print(f"[ingest] Open GRIB with xarray+cfgrib -> {grib_path}")
    backend_kwargs: dict = {"indexpath": ""}

    if filter_by_keys is not None:
        backend_kwargs["filter_by_keys"] = filter_by_keys
        print(f"[ingest]   with filter_by_keys={filter_by_keys}")

    ds = xr.open_dataset(
        grib_path,
        engine="cfgrib",
        backend_kwargs=backend_kwargs,
    )
    return ds



def insert_forecasts_from_jma_sample(db: Session) -> None:
    """
    気象庁 GPV サンプル（GSM 全球）を 1 ファイルだけ読み込み、
    forecasts テーブルに「とりあえず何点か」INSERT する。

    ※ ここではまだ temp_2m / wind10m_u などの中身は埋めていない。
      （まずは pipeline 動作確認用）
    """
    # 既に forecasts が埋まっているならスキップ（今までと同じロジック）
    deleted = db.query(Forecast).delete()
    db.commit()
    print(f"[ingest] deleted {deleted} existing forecasts rows.")
    # 1. ZIP ダウンロード → GRIB 展開
    zip_path = download_sample_zip()
    grib_path = extract_first_grib(zip_path)

    # 2. GRIB を開く
    # ds = open_dataset(grib_path)
    ds = open_dataset(
    grib_path,
    filter_by_keys={"stepType": "instant", "numberOfPoints": 65160},
)



    print("[ingest] Dataset summary:")
    print(ds)

    # 3. DataFrame に変換して、先頭の数点だけ Forecast に変換する
    #   実際には time, step, latitude, longitude を使って
    #   run_time / forecast_time / lat / lon を作るイメージ
    df = ds.to_dataframe().reset_index()

    # 行数が膨大になるので、まずは 10 点だけに絞る
    sample_df = df.head(10)

    rows: list[Forecast] = []

    for _, row in sample_df.iterrows():
        # time / step があれば forecast_time = time + step みたいにする
        # なければ、とりあえず今の UTC を入れておく
        time_val = row.get("time")
        step_val = row.get("step")

        if isinstance(time_val, datetime):
            run_time = time_val
        else:
            run_time = datetime.utcnow()

        if isinstance(time_val, datetime) and step_val is not None:
            try:
                forecast_time = time_val + step_val
            except Exception:
                forecast_time = run_time
        else:
            forecast_time = run_time

        lat = float(row.get("latitude"))
        lon = float(row.get("longitude"))

        f = Forecast(
            run_time=run_time,
            forecast_time=forecast_time,
            lat=lat,
            lon=lon,
            # ★ ここは後で GRIB の変数名に合わせて埋めていく
            temp_2m=None,
            wind10m_u=None,
            wind10m_v=None,
            ghi=None,
        )
        rows.append(f)

    db.add_all(rows)
    db.commit()
    print(f"[ingest] inserted {len(rows)} forecast rows from JMA sample.")


# ===== ここまで 新しい ingest ロジック =====


def main() -> None:
    print("[ingest] Start ingest script.")
    init_db()

    db = SessionLocal()
    try:
        # ここを insert_dummy_forecasts から差し替える
        insert_forecasts_from_jma_sample(db)
    finally:
        db.close()

    print("[ingest] Done.")


if __name__ == "__main__":
    main()

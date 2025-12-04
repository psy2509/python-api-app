# app/ingest/preview_grib.py

from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any, Dict, List

import requests
import xarray as xr
import pandas as pd
from math import atan2, degrees
import numpy as np


# 気象庁 GPV サンプル ZIP
JMA_ZIP_URL = "https://www.data.jma.go.jp/developer/gpv_sample/gsm_gl.zip"

# コンテナ内での保存先
DATA_DIR = Path("/app/data/raw/gsm_gl")
ZIP_PATH = DATA_DIR / "gsm_gl_sample.zip"

# ZIP 内で使う GRIB2 ファイル名（サンプル仕様に依存）
GRIB_MEMBER = "gsm_gl/Z__C_RJTD_20171205000000_GSM_GPV_Rgl_FD0006_grib2.bin"
GRIB_PATH = DATA_DIR / "Z__C_RJTD_20171205000000_GSM_GPV_Rgl_FD0006_grib2.bin"


def download_sample_zip() -> None:
    """気象庁のサンプル ZIP をダウンロードして保存する。既にあればスキップ。"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if ZIP_PATH.exists():
        print(f"[preview] ZIP already exists: {ZIP_PATH}")
        return

    print(f"[preview] Downloading JMA sample ZIP: {JMA_ZIP_URL}")
    resp = requests.get(JMA_ZIP_URL, timeout=60)
    resp.raise_for_status()

    ZIP_PATH.write_bytes(resp.content)
    print(f"[preview] Saved ZIP -> {ZIP_PATH}")


def extract_grib_from_zip() -> None:
    """ZIP から GRIB2 ファイルを取り出して保存する。既にあればスキップ。"""
    if GRIB_PATH.exists():
        print(f"[preview] GRIB already exists: {GRIB_PATH}")
        return

    print(f"[preview] Extracting GRIB from {ZIP_PATH}")
    with zipfile.ZipFile(ZIP_PATH, "r") as zf:
        with zf.open(GRIB_MEMBER) as src, open(GRIB_PATH, "wb") as dst:
            dst.write(src.read())
    print(f"[preview] Extracted GRIB -> {GRIB_PATH}")


def open_dataset() -> xr.Dataset:
    """
    GRIB2 を xarray+cfgrib で開く。

    サンプルは等圧面 (isobaricInhPa) の gh/u/v/t/w が入っているので、
    cfgrib から提示された filter_by_keys に従ってフィルタをかける。
    """
    print(f"[preview] Open GRIB with xarray+cfgrib -> {GRIB_PATH}")
    backend_kwargs = {
        # さっきのエラーが教えてくれた組み合わせ
        "filter_by_keys": {
            "stepType": "instant",
            "numberOfPoints": 65160,
        },
        "errors": "ignore",
    }

    ds = xr.open_dataset(
        GRIB_PATH,
        engine="cfgrib",
        backend_kwargs=backend_kwargs,
    )

    print("[preview] Dataset summary:")
    print(ds)
    print("[preview] Data variables:", list(ds.data_vars))
    print("[preview] Coords:", list(ds.coords))

    return ds


def build_power_related_samples(ds: xr.Dataset, limit: int = 30) -> List[Dict[str, Any]]:
    """
    発電量に関係しそうな情報を中心に 30件ほど JSON レコードを作る。

    - 代表レベルとして isobaricInhPa の最初のレベル（上空の1層）を使う
      ※ 本番では 2m/10m の別プロダクトを使う想定
    - 使う変数:
        * t: 温度 [K] → ℃に変換
        * u, v: 風の東西・南北成分 → 風速・風向に変換
    """
    # 代表として 1 つ目の気圧レベルを使う
    ds_level = ds.isel(isobaricInhPa=0)

    # 必要な変数だけ DataFrame にする
    vars_to_use = []
    if "t" in ds_level.data_vars:
        vars_to_use.append("t")
    if "u" in ds_level.data_vars:
        vars_to_use.append("u")
    if "v" in ds_level.data_vars:
        vars_to_use.append("v")

    df = ds_level[vars_to_use].to_dataframe().reset_index()

    # valid_time があれば使い、なければ time を使う
    time_col = "valid_time" if "valid_time" in df.columns else "time"

    records: List[Dict[str, Any]] = []

    for _, row in df.head(limit).iterrows():
        lat = float(row["latitude"])
        lon = float(row["longitude"])
        pressure = float(row["isobaricInhPa"])

        # 時刻
        t_valid = row[time_col]
        if pd.isna(t_valid):
            valid_time_str = None
        else:
            # pandas.Timestamp → ISO 文字列
            valid_time_str = pd.to_datetime(t_valid).isoformat()

        # 温度 [K] → [℃]
        temp_c = None
        if "t" in df.columns and not pd.isna(row["t"]):
            temp_c = float(row["t"]) - 273.15

        # 風（u, v）→ 風速と風向
        wind_u = None
        wind_v = None
        wind_speed = None
        wind_dir_deg = None

        if "u" in df.columns and not pd.isna(row["u"]):
            wind_u = float(row["u"])
        if "v" in df.columns and not pd.isna(row["v"]):
            wind_v = float(row["v"])

        if wind_u is not None and wind_v is not None:
            wind_speed = float((wind_u ** 2 + wind_v ** 2) ** 0.5)
            # 気象の風向ではなく、簡易的な「どの方位から吹いているか」の角度例
            # u: 東向き +, v: 北向き +
            # ここでは数学的なベクトル角度から「風が来る方角」を計算する例
            wind_dir_deg = float((270.0 - degrees(atan2(wind_v, wind_u))) % 360.0)

        rec: Dict[str, Any] = {
            "valid_time": valid_time_str,
            "pressure_hPa": pressure,
            "lat": lat,
            "lon": lon,
            "temp_C": temp_c,
            "wind_u": wind_u,
            "wind_v": wind_v,
            "wind_speed": wind_speed,
            "wind_direction_deg": wind_dir_deg,
        }
        records.append(rec)

    return records


def main() -> None:
    print("[preview] Start GRIB preview")

    download_sample_zip()
    extract_grib_from_zip()
    ds = open_dataset()

    samples = build_power_related_samples(ds, limit=30)

    # JSON として標準出力へ
    print("[preview] ---- JSON samples (limit=30) ----")
    print(json.dumps(samples, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

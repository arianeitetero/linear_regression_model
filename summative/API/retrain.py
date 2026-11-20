import io

import joblib
import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile
from sklearn.base import clone
from sklearn.linear_model import SGDRegressor
from sklearn.metrics import mean_squared_error

MODEL_PATH = "best_model.pkl"
TRAIN_PATH = "train_data.csv"   # small sample of the original training rows

NUM = ["year", "odometer"]
CAT = ["manufacturer", "condition", "cylinders", "fuel", "transmission", "drive", "type", "title_status"]
FEATURES = NUM + CAT
TARGET = "price_k"              # price in thousands of dollars, same as the notebook

router = APIRouter()

# the model lives in this dict so /retrain can swap it and /predict sees the new one
state = {"model": joblib.load(MODEL_PATH)}


def get_allowed_values():
    """Return the category values the encoder saw during training."""
    encoder = state["model"].named_steps["pre"].named_transformers_["cat"]
    allowed = {}
    for column, values in zip(CAT, encoder.categories_):
        allowed[column] = set(values)
    return allowed


def clean_upload(df):
    # accept a plain "price" column in dollars too
    if TARGET not in df.columns and "price" in df.columns:
        df[TARGET] = pd.to_numeric(df["price"], errors="coerce") / 1000

    missing = [c for c in FEATURES + [TARGET] if c not in df.columns]
    if missing:
        raise HTTPException(status_code=422, detail=f"CSV is missing columns: {missing}")

    df = df[FEATURES + [TARGET]].copy()
    for col in NUM + [TARGET]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in CAT:
        df[col] = df[col].astype(str).str.lower().str.strip()

    df = df.dropna()
    df = df[df["year"].between(1990, 2026)]
    df = df[df["odometer"].between(100, 400000)]
    df = df[df[TARGET].between(0.5, 100)]
    if len(df) == 0:
        raise HTTPException(status_code=422, detail="No valid rows left after cleaning the CSV.")
    return df


@router.post("/retrain")
async def retrain(file: UploadFile = File(...)):
    """Upload a CSV with the 10 input columns and price_k (or price). The model is retrained right away."""
    try:
        new_data = pd.read_csv(io.BytesIO(await file.read()))
    except Exception:
        raise HTTPException(status_code=400, detail="Could not read the file as a CSV.")
    new_data = clean_upload(new_data)

    model = state["model"]
    regressor = model.named_steps["model"]

    if isinstance(regressor, SGDRegressor):
        # keep training the saved model on the new rows only
        X_new = model.named_steps["pre"].transform(new_data[FEATURES])
        for _ in range(10):
            regressor.partial_fit(X_new, new_data[TARGET])
        method = "partial_fit on the new rows"
    else:
        # other models cannot learn step by step, so refit on old + new rows
        old_data = pd.read_csv(TRAIN_PATH)
        all_data = pd.concat([old_data, new_data], ignore_index=True)
        model = clone(model)
        model.fit(all_data[FEATURES], all_data[TARGET])
        method = "refit on the original sample plus the new rows"

    mse = mean_squared_error(new_data[TARGET], model.predict(new_data[FEATURES]))
    joblib.dump(model, MODEL_PATH, compress=3)
    state["model"] = model

    return {"status": "model retrained", "method": method,
            "new_rows": len(new_data), "mse_on_new_rows": round(mse, 3)}

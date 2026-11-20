import os

import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from retrain import CAT, FEATURES, get_allowed_values, router, state

app = FastAPI(title="Used-car price predictor")

# CORS: only the websites listed in origins may call this API from a browser.
# Allowed: my Render URL (Swagger UI) and the local Flutter web address.
# Restricted: every other origin (no "*"), methods to GET and POST because that is
# all the API uses, and headers to Content-Type. Credentials are off because
# there is no login or cookies. The Flutter mobile app is not a browser, so CORS
# does not affect it.
origins = os.getenv(
    "ALLOWED_ORIGINS",
    "https://linear-regression-model-l4wc.onrender.com,http://localhost:8080,http://127.0.0.1:8080",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
    allow_credentials=False,
)

app.include_router(router)


class CarInput(BaseModel):
    year: int = Field(ge=1990, le=2026)
    odometer: float = Field(ge=100, le=400000)
    manufacturer: str
    condition: str
    cylinders: str
    fuel: str
    transmission: str
    drive: str
    type: str
    title_status: str

    @field_validator(*CAT)
    @classmethod
    def check_category(cls, value, info):
        value = value.strip().lower()
        if info.field_name == "cylinders" and value.isdigit():
            value = value + " cylinders"   # accept "6" as well as "6 cylinders"
        allowed = get_allowed_values()[info.field_name]
        if value not in allowed:
            raise ValueError(f"'{value}' is not a known value. Choose one of: {', '.join(sorted(allowed))}")
        return value


@app.post("/predict")
def predict(car: CarInput):
    row = pd.DataFrame([car.model_dump()])[FEATURES]
    price_k = state["model"].predict(row)[0]
    price = max(float(price_k) * 1000, 0)   # the model predicts in thousands of dollars
    return {"predicted_price_usd": round(price, 2)}

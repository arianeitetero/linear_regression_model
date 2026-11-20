# Used-Car Price Prediction

**Mission and problem.** My mission is to make buying a vehicle more transparent and affordable for ordinary buyers.
Used-car listings are often overpriced and buyers have no quick way to check.
This project predicts a fair asking price (in US dollars) from a car's year, mileage, make and condition.
Buyers and small dealers can use it to check a listing before negotiating.

## Dataset
Craigslist used-vehicle listings (`vehicles.csv`): about 295,000 rows and 40 columns, from which I use 10 input features (2 numeric: year, odometer; 8 categorical: manufacturer, condition, cylinders, fuel, transmission, drive, type, title status) and the target `price`.
Source: Craigslist vehicles dataset on Kaggle - https://www.kaggle.com/datasets/austinreese/craigslist-carstrucks-data
(the file is too large for GitHub, so it is not committed; the notebook expects it at `summative/linear_regression/vehicles.csv`).

## Public API (Swagger UI)
https://linear-regression-model-api.onrender.com/docs  <!-- replace with your real Render URL after deploying -->

The free Render plan sleeps after 15 minutes, so the first request can take up to a minute.

## Video demo
<!-- paste your YouTube link here -->

## Run the mobile app
1. Install [Flutter](https://docs.flutter.dev/get-started/install) and Android Studio (or Xcode) and start an emulator, or connect a phone with USB debugging.
2. Open `summative/FlutterApp/lib/main.dart` and check that `apiUrl` is your Render URL followed by `/predict`.
3. In a terminal:
   ```
   cd summative/FlutterApp
   flutter pub get
   flutter devices        # confirm the emulator or phone is listed
   flutter run
   ```
4. Fill in all 10 fields (e.g. year 2015, odometer 80000, toyota, good, 6 cylinders, gas, automatic, 4wd, suv, clean) and tap **Predict**. Empty, non-numeric or out-of-range values show an error message in the result box.

## Repository layout / other notes
- `summative/linear_regression/multivariate.ipynb`: data exploration and the four models (best: Random Forest).
- `summative/API/`: FastAPI service (`prediction.py`, `retrain.py`, `best_model.pkl`; `train_data.csv` is a 10,000-row sample of the training data used when retraining a non-SGD model).
- Run the API locally: `cd summative/API && uv sync && uv run uvicorn prediction:app --reload`.
- Render: root directory `summative/API`, build command `pip install -r requirements.txt`, start command `uvicorn prediction:app --host 0.0.0.0 --port $PORT`. Set the `ALLOWED_ORIGINS` env var to your Render URL plus local origins (comma separated).

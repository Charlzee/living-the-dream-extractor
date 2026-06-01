from fastapi import FastAPI
from pydantic import BaseModel
from get_data import get_mii_data, run_extractor

app = FastAPI()

@app.get("/api/get_mii_data")
def get_data():
    return {"message": get_mii_data()}
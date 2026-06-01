from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from get_data import get_mii_data, run_extractor

app = FastAPI()

class ExtractionRequest(BaseModel):
    target_id: str | None = None

@app.get("/api/test")
async def test():
    return {"message": "Hello"}

@app.get("/api/get_mii_data")
async def get_data(payload: ExtractionRequest):
    try:
        extracted_payload = get_mii_data()
        
        return {
            "status": "success",
            "data": extracted_payload
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Local extraction failed: {str(e)}"
        )
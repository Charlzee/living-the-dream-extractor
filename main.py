from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from get_data import get_mii_data

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/test")
def test():
    return {"message": "Hello!"}

@app.post("/api/get_mii_data")
def get_data(file: UploadFile = File(...)):
    try:
        file_bytes = file.file.read()

        extracted_payload = get_mii_data(file=file_bytes)
        
        return {
            "status": "success",
            "filename": file.filename,
            "data": extracted_payload
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Local extraction failed: {str(e)}"
        )
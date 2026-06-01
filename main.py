import os
import requests
from fastapi import FastAPI, HTTPException

app = FastAPI()

TUNNEL_URL = os.environ.get("TUNNEL_URL", "https://ltd-extractor-api.imposter-gm.com")

@app.get("/api/get_mii_data")
def forward_to_pc():
    try:
        response = requests.post(f"{TUNNEL_URL}/api/get_mii_data", json={}) 
        
        return response.json()
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=503, 
            detail="Your home PC is currently offline or unreachable."
        )
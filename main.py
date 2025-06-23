from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi.responses import FileResponse
import boto3
import os
import json

# Load credentials from .env
load_dotenv()

app = FastAPI()

# Wasabi S3 Configuration
WASABI_ACCESS_KEY = os.getenv("WASABI_ACCESS_KEY")
WASABI_SECRET_KEY = os.getenv("WASABI_SECRET_KEY")
WASABI_ENDPOINT = "https://s3.ca-central-1.wasabisys.com"
BUCKET_NAME = "chet-stats"

s3_client = boto3.client(
    's3',
    endpoint_url=WASABI_ENDPOINT,
    aws_access_key_id=WASABI_ACCESS_KEY,
    aws_secret_access_key=WASABI_SECRET_KEY
)

class StatsUpload(BaseModel):
    user_id: str
    stats: dict

@app.get("/")
def root():
    return {"message": "NovaPrime backend is live."}

@app.post("/upload_stats")
async def upload_stats(data: StatsUpload):
    try:
        key = f"stats/{data.user_id}.json"
        json_data = json.dumps(data.stats)
        s3_client.put_object(Bucket=BUCKET_NAME, Key=key, Body=json_data)
        return {"status": "success", "message": "Stats uploaded."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/openapi.yaml")
async def serve_openapi():
    openapi_path = os.path.join(os.path.dirname(__file__), "openapi.yaml")
    if os.path.exists(openapi_path):
        return FileResponse(openapi_path, media_type="text/yaml")
    else:
        raise HTTPException(status_code=404, detail="openapi.yaml not found.")

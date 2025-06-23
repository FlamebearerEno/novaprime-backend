from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import boto3
import botocore
import os
import json

# Load environment variables
load_dotenv()

app = FastAPI()

# Wasabi S3 Configuration
WASABI_ACCESS_KEY = os.getenv("WASABI_ACCESS_KEY")
WASABI_SECRET_KEY = os.getenv("WASABI_SECRET_KEY")
WASABI_ENDPOINT = "https://s3.ca-central-1.wasabisys.com"
BUCKET_NAME = "chet-stats"

# Force Signature Version 4 (avoids signature mismatch)
s3_client = boto3.client(
    's3',
    endpoint_url=WASABI_ENDPOINT,
    aws_access_key_id=WASABI_ACCESS_KEY,
    aws_secret_access_key=WASABI_SECRET_KEY,
    config=botocore.client.Config(signature_version='s3v4')
)

# Data Models
class StatsUpload(BaseModel):
    user_id: str
    stats: dict

class UserIDRequest(BaseModel):
    user_id: str

# Routes
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

@app.post("/get_user_stats")
async def get_user_stats(data: UserIDRequest):
    try:
        key = f"stats/{data.user_id}.json"
        response = s3_client.get_object(Bucket=BUCKET_NAME, Key=key)
        stats_data = json.loads(response['Body'].read())
        return {"user_id": data.user_id, "stats": stats_data}
    except s3_client.exceptions.NoSuchKey:
        raise HTTPException(status_code=404, detail="User stats not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/list_all_user_ids")
async def list_all_user_ids():
    try:
        result = s3_client.list_objects_v2(Bucket=BUCKET_NAME, Prefix="stats/")
        if 'Contents' not in result:
            return {"user_ids": []}
        user_ids = [obj['Key'].split("/")[1].replace(".json", "") for obj in result['Contents']]
        return {"user_ids": user_ids}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get_all_user_stats")
async def get_all_user_stats():
    try:
        result = s3_client.list_objects_v2(Bucket=BUCKET_NAME, Prefix="stats/")
        if 'Contents' not in result:
            return {"users": []}

        users = []
        for obj in result['Contents']:
            user_id = obj['Key'].split("/")[1].replace(".json", "")
            response = s3_client.get_object(Bucket=BUCKET_NAME, Key=obj['Key'])
            stats_data = json.loads(response['Body'].read())
            users.append({"user_id": user_id, "stats": stats_data})
        return {"users": users}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/openapi.yaml")
async def serve_openapi():
    openapi_path = os.path.join(os.path.dirname(__file__), "openapi.yaml")
    if os.path.exists(openapi_path):
        return FileResponse(openapi_path, media_type="text/yaml")
    else:
        raise HTTPException(status_code=404, detail="openapi.yaml not found.")

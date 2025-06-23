from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load\_dotenv
import boto3
import os
import json

load\_dotenv()

app = FastAPI()

# Wasabi S3 Configuration

WASABI\_ACCESS\_KEY = os.getenv("WASABI\_ACCESS\_KEY")
WASABI\_SECRET\_KEY = os.getenv("WASABI\_SECRET\_KEY")
WASABI\_ENDPOINT = "[https://s3.ca-central-1.wasabisys.com](https://s3.ca-central-1.wasabisys.com)"
BUCKET\_NAME = "chet-stats"

s3\_client = boto3.client(
's3',
endpoint\_url=WASABI\_ENDPOINT,
aws\_access\_key\_id=WASABI\_ACCESS\_KEY,
aws\_secret\_access\_key=WASABI\_SECRET\_KEY
)

class StatsUpload(BaseModel):
user\_id: str
stats: dict

class UserIDRequest(BaseModel):
user\_id: str

@app.get("/")
def root():
return {"message": "NovaPrime backend is live."}

@app.post("/upload\_stats")
async def upload\_stats(data: StatsUpload):
try:
key = f"stats/{data.user\_id}.json"
json\_data = json.dumps(data.stats)
s3\_client.put\_object(Bucket=BUCKET\_NAME, Key=key, Body=json\_data)
return {"status": "success", "message": "Stats uploaded."}
except Exception as e:
raise HTTPException(status\_code=500, detail=str(e))

@app.post("/get\_user\_stats")
async def get\_user\_stats(data: UserIDRequest):
try:
key = f"stats/{data.user\_id}.json"
response = s3\_client.get\_object(Bucket=BUCKET\_NAME, Key=key)
stats\_data = json.loads(response\['Body'].read())
return {"user\_id": data.user\_id, "stats": stats\_data}
except s3\_client.exceptions.NoSuchKey:
raise HTTPException(status\_code=404, detail="User stats not found.")
except Exception as e:
raise HTTPException(status\_code=500, detail=str(e))

@app.get("/list\_all\_user\_ids")
async def list\_all\_user\_ids():
try:
result = s3\_client.list\_objects\_v2(Bucket=BUCKET\_NAME, Prefix="stats/")
if 'Contents' not in result:
return {"user\_ids": \[]}
user\_ids = \[obj\['Key'].split("/")\[1].replace(".json", "") for obj in result\['Contents']]
return {"user\_ids": user\_ids}
except Exception as e:
raise HTTPException(status\_code=500, detail=str(e))

@app.get("/get\_all\_user\_stats")
async def get\_all\_user\_stats():
try:
result = s3\_client.list\_objects\_v2(Bucket=BUCKET\_NAME, Prefix="stats/")
if 'Contents' not in result:
return {"users": \[]}

```
    users = []
    for obj in result['Contents']:
        user_id = obj['Key'].split("/")[1].replace(".json", "")
        response = s3_client.get_object(Bucket=BUCKET_NAME, Key=obj['Key'])
        stats_data = json.loads(response['Body'].read())
        users.append({"user_id": user_id, "stats": stats_data})
    return {"users": users}
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
```

@app.get("/openapi.yaml")
async def serve\_openapi():
openapi\_path = os.path.join(os.path.dirname(**file**), "openapi.yaml")
if os.path.exists(openapi\_path):
return FileResponse(openapi\_path, media\_type="text/yaml")
else:
raise HTTPException(status\_code=404, detail="openapi.yaml not found.")

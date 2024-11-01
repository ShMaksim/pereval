import json

from fastapi import FastAPI, HTTPException, Request
from .database import PerevalDatabase

app = FastAPI()

@app.post("/submitData")
async def submit_data(request: Request):
    try:
        data = await request.json()
        db = PerevalDatabase()
        result = db.submit_data(data)

        if result['status'] == 200:
            return result
        else:
            raise HTTPException(status_code=result['status'], detail=result['message'])

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Некорректный JSON")
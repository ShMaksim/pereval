import json
import base64
import uuid

from fastapi import FastAPI, HTTPException, Request, Depends, Query
from fastapi.responses import JSONResponse
from .database import PerevalDatabase, Pereval, Coords, User, Image
from typing import List

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


@app.get("/submitData/{pereval_id}")
async def get_pereval_data(pereval_id: int):
    with PerevalDatabase() as db:
        pereval = db.get_pereval(pereval_id)
        if pereval:
            return pereval
        else:
            raise HTTPException(status_code=404, detail="Перевал не найден")

@app.patch("/submitData/{pereval_id}")
async def update_pereval_data(request: Request, pereval_id: int):
    with PerevalDatabase() as db:
        try:
            data = await request.json()
            result = db.update_pereval(pereval_id, data)
            return JSONResponse(content=result)

        except json.JSONDecodeError as e:
            return JSONResponse(content={'state': 0, 'message': f"Ошибка декодирования JSON: {e}"})


@app.get("/submitData/")
async def get_perevals_by_user_email(user__email: str = Query(...)):
    with PerevalDatabase() as db:
        perevals = db.get_perevals_by_user_email(user__email)

        if perevals:
            return perevals
        else:
            raise HTTPException(status_code=404, detail="Перевалы не найдены для указанного пользователя")
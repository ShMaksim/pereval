import json
import base64
import uuid

from fastapi import FastAPI, HTTPException, Request, Depends, Query
from fastapi.responses import JSONResponse
from fastapi_utils.inferring_router import InferringRouter
from fastapi_utils.cbv import cbv

from .database import PerevalDatabase, Pereval, Coords, User, Image
from typing import List

app = FastAPI()
router = InferringRouter()


@cbv(router)
class PerevalAPI:
    db: PerevalDatabase = Depends(PerevalDatabase)

    @router.post("/submitData")
    async def submit_data(self, request: Request):
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


    @router.get("/submitData/{pereval_id}")
    async def get_pereval_data(self, pereval_id: int):
        with PerevalDatabase() as db:
            pereval = db.get_pereval(pereval_id)
            if pereval:
                return pereval
            else:
                raise HTTPException(status_code=404, detail="Перевал не найден")

    @router.patch("/submitData/{pereval_id}")
    async def update_pereval_data(self, request: Request, pereval_id: int):
        with PerevalDatabase() as db:
            try:
                data = await request.json()
                result = db.update_pereval(pereval_id, data)
                return JSONResponse(content=result)

            except json.JSONDecodeError as e:
                return JSONResponse(content={'state': 0, 'message': f"Ошибка декодирования JSON: {e}"})


    @router.get("/submitData/")
    async def get_perevals_by_user_email(self, user__email: str = Query(...)):
        with PerevalDatabase() as db:
            perevals = db.get_perevals_by_user_email(user__email)

            if perevals:
                return perevals
            else:
                raise HTTPException(status_code=404, detail="Перевалы не найдены для указанного пользователя")

app.include_router(router)
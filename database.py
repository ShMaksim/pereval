import os
import json
from typing import Dict, List, Union

import psycopg2
from psycopg2.extras import Json

class PerevalDatabase:
    def __init__(self):
        self.conn = psycopg2.connect(
            host=os.environ.get("FSTR_DB_HOST"),
            port=os.environ.get("FSTR_DB_PORT"),
            database="pereval",
            user=os.environ.get("FSTR_DB_LOGIN"),
            password=os.environ.get("FSTR_DB_PASS")
        )
        self.cursor = self.conn.cursor()

    def submit_data(self, data: Dict) -> Dict[str, Union[int, str, None]]:
        try:
            #  (Реализация добавления данных в таблицы users, coords,  pereval_added, pereval_images_added.
            #   Будет в следующем ответе, после уточнения формата данных  images)

            return {"status":200, "message": None, "id": pereval_id}
        except psycopg2.Error as e:
            self.conn.rollback()
            return {"statuts": 500, "message": f"Ошибка базы данных: {e}", "id": None}
        finally:
            self.cursor.close()
            self.conn.close()


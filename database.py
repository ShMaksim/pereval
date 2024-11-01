import os
import json
from typing import Dict, List, Union
import base64
import uuid
from datetime import datetime

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
            email = data['user']['email']
            self.cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            user_row = self.cursor.fetchone()

            if user_row:
                user_id = user_row[0]
            else:
                fam = data['user']['fam']
                name = data['user']['name']
                otc = data['user']['otc']
                phone = data['user']['phone']
                self.cursor.execute(
                    "INSERT INTO users (email, fam, name, otc, phone) VALUES (%s, %s, %s, %s, %s) RETURNING id",
                    (email, fam, name, otc, phone))
                user_id = self.cursor.fetchone()[0]

            coords = data['coords']
            self.cursor.execute("INSERT INTO coords (latitude, longitude, height) VALUES (%s, %s, %s) RETURNING id",
                                (coords['latitude'], coords['longitude'], coords['height']))
            coord_id = self.cursor.fetchone()[0]

            self.cursor.execute("""
                            INSERT INTO pereval_added (date_added, beauty_title, title, other_titles, connect, add_time, user_id, coord_id, winter, summer, autumn, spring) 
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
                        """, (
            datetime.now(), data['beauty_title'], data['title'], data['other_titles'], data['connect'],
            data.get('add_time'), user_id, coord_id,
            data['level']['winter'], data['level']['summer'], data['level']['autumn'], data['level']['spring']))
            pereval_id = self.cursor.fetchone()[0]

            for image_data in data['images']:
                image_base64 = image_data['data']
                image_title = image_data['title']
                image_uuid = uuid.uuid4()
                file_extension = '.jpg'

                image_path = f"python/pereval/images/{image_uuid}.jpg"

                with open(image_path, "wb") as f:
                    f.write(base64.b16decode(image_base64))

                self.cursor.execute(
                    "INSERT INTO pereval_images (date_added, img, title) VALUES (%s, %s, %s) RETURNING id",
                    (datetime.now(), image_path, image_title))
                image_id = self.cursor.fetchone()[0]

                self.cursor.execute("INSERT INTO pereval_images_added (pereval_id, image_id) VALUES (%s, %s)",
                                    (pereval_id, image_id))

            self.conn.commit()
            return {"status": 200, "message": None, "id": pereval_id}

        except psycopg2.Error as e:
            self.conn.rollback()
            return {"statuts": 500, "message": f"Ошибка базы данных: {e}", "id": None}
        finally:
            self.cursor.close()
            self.conn.close()
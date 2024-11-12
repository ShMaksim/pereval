import os
import json
from typing import Dict, List, Union, Optional
import base64
import uuid
from datetime import datetime

import psycopg2
from psycopg2.extras import Json
from pydantic import BaseModel, EmailStr, Field, validator

class Coords(BaseModel):
    latitude: float
    longitude: float
    height: int

    @validator('latitude')
    def validate_latitude(cls, value):
        if not (-90 <= value <= 90):
            raise ValueError("Широта должна быть в диапазоне от -90 до 90")
        return value

    @validator('longitude')
    def validate_longitude(cls, value):
        if not (-180 <= value <= 180):
            raise ValueError("Долгота должна быть в диапазоне от -180 до 180")
        return value

    @validator('height')
    def validate_height(cls, value):
        if value < 0:
            raise ValueError("Высота должна быть неотрицательной")
        return value

class User(BaseModel):
    email: EmailStr
    fam: str
    name: str
    otc: str
    phone: str

    @validator('email')
    def validate_email(cls, value):
        if not value:
            raise ValueError("Email не может быть пустым.")
        return value

class Image(BaseModel):
    id: int
    title: str
    img: str
    date_added: datetime

class Pereval(BaseModel):
    id: int
    date_added: datetime
    beauty_title: str
    title: str
    other_titles: str
    connect: str
    add_time: Optional[datetime]
    user: User
    coords: Coords
    winter: Optional[str]
    summer: Optional[str]
    autumn: Optional[str]
    spring: Optional[str]
    status: Optional[str]
    images: Optional[List[Image]]


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

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cursor.close()
        self.conn.close()

    def submit_data(self, data: Dict) -> Dict[str, Union[int, str, None]]:
        with self:
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
                                                INSERT INTO pereval_added (date_added, beauty_title, title, other_titles, connect, add_time, user_id, coord_id, winter, summer, autumn, spring, status) 
                                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
                                            """, (
                    datetime.now(), data['beauty_title'], data['title'], data['other_titles'], data['connect'],
                    data.get('add_time'), user_id, coord_id,
                    data['level'].get('winter'), data['level'].get('summer'), data['level'].get('autumn'),
                    data['level'].get('spring'), 'new')
                )
                pereval_id = self.cursor.fetchone()[0]

                for image_data in data['images']:
                    image_base64 = image_data['data']
                    image_title = image_data['title']
                    image_uuid = uuid.uuid4()
                    file_extension = '.jpg'

                    image_path = f"images/{uuid.uuid4()}.jpg"

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
                return {"status": 500, "message": f"Ошибка базы данных ({type(e).__name__}): {e}", "id": None}
            except ValueError as e:
                self.conn.rollback()
                return {"status": 400, "message": f"Ошибка валидации данных: {e}", "id": None}

    def get_pereval(self, pereval_id: int) -> Optional[Pereval]:
        with self:
            try:
                self.cursor.execute(
                    """
                    SELECT * FROM pereval_added pa
                    JOIN coords c ON pa.coord_id = c.id
                    JOIN users u ON pa.user_id = u.id
                    LEFT JOIN pereval_images_added pia ON pa.id = pia.pereval_id
                    LEFT JOIN pereval_images pi ON pia.image_id = pi.id
                    WHERE pa.id = %s;
                    """,
                    (pereval_id,)
                )
                row = self.cursor.fetchone()

                if not row:
                    return None


                user = self.get_user_by_id(row[6])
                coords = self.get_coords_by_id(row[7])
                images = self.get_images_by_pereval_id(pereval_id)

                pereval_data = {
                    'id': row[0],
                    'date_added': row[1],
                    'beauty_title': row[2],
                    'title': row[3],
                    'other_titles': row[4],
                    'connect': row[5],
                    'add_time': row[6],
                    'user': user,
                    'coords': coords,
                    'winter': row[8],
                    'summer': row[9],
                    'autumn': row[10],
                    'spring': row[11],
                    'status': row[12],
                    'images': images
                }

                return Pereval(**pereval_data)

            except psycopg2.Error as e:
                print(f"Ошибка базы данных: {e}")
                return None

    def update_pereval(self, pereval_id: int, data: Dict) -> Dict:
        with self:
            try:
                self.cursor.execute("SELECT status FROM pereval_added WHERE id = %s", (pereval_id,))

                status = self.cursor.fetchone()
                if not status:
                    return {'state': 0, 'message': 'Перевал с таким id не найден'}
                if status[0] != 'new':
                    return {'state': 0, 'message': 'Перевал уже прошел модерацию, редактирование невозможно'}
                else:
                    self.cursor.execute(
                        """UPDATE pereval_added SET beauty_title=%s, title=%s, other_titles=%s, connect=%s, add_time=%s, winter=%s, summer=%s, autumn=%s, spring=%s
                           WHERE id=%s;""",
                        (data['beauty_title'], data['title'], data['other_titles'], data['connect'], data.get('add_time'),
                         data['level']['winter'], data['level']['summer'], data['level']['autumn'], data['level']['spring'],
                         pereval_id)
                    )
                    self.conn.commit()

                    return {'state': 1, 'message': 'Перевал успешно обновлен'}

            except psycopg2.Error as e:

                self.conn.rollback()
                return {'state': 0, 'message': f"Ошибка базы данных: {e}"}

    def get_perevals_by_user_email(self, user__email: str) -> List[Pereval]:
        with self:
            try:
                self.cursor.execute("""SELECT pa.* FROM pereval_added pa
                                            JOIN users u ON pa.user_id = u.id
                                            WHERE u.email = %s;""", (user__email,))
                rows = self.cursor.fetchall()

                if not rows:
                    return []

                pereval_list = []

                for row in rows:

                    pereval_list.append(
                        Pereval(id=row[0], date_added=row[1], beauty_title=row[2], title=row[3], other_titles=row[4], connect=row[5], add_time=row[6],
                                user = self.get_user_by_id(row[15]),
                                coords = self.get_coords_by_id(row[7]),
                                winter=row[8], summer=row[9], autumn=row[10], spring=row[11], status=row[12], images=self.get_images_by_pereval_id(row[0]))
                    )
                return pereval_list

            except psycopg2.Error as e:
                print(f"Ошибка базы данных: {e}")
                return []

    def get_images_by_pereval_id(self, pereval_id):
        with self:
            try:
                self.cursor.execute(
                    "SELECT * from pereval_images pi JOIN pereval_images_added pia on pi.id=pia.image_id WHERE pia.pereval_id=%s",
                    (pereval_id,))

                rows = self.cursor.fetchall()

                if not rows:
                    return []
                images = []
                for row in rows:
                    image = Image(id=row[0], date_added=row[1], img=row[2], title=row[3])
                    images.append(image)

                return images
            except (Exception, psycopg2.Error) as error:
                print("Ошибка при работе с PostgreSQL", error)
                return []

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        with self:
            try:

                self.cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
                row = self.cursor.fetchone()
                if not row:
                    return None

                user_data = {
                    'email': row[1],
                    'fam': row[2],
                    'name': row[3],
                    'otc': row[4],
                    'phone': row[5]
                }

                return User(**user_data)
            except psycopg2.Error as e:
                print(f"Ошибка базы данных: {e}")
                return None

    def get_coords_by_id(self, coord_id: int) -> Optional[Coords]:
        with self:
            try:

                self.cursor.execute("SELECT * FROM coords WHERE id = %s", (coord_id,))

                row = self.cursor.fetchone()
                if not row:
                    return None
                coords_data = {
                    'latitude': row[1],
                    'longitude': row[2],
                    'height': row[3]
                }

                return Coords(**coords_data)


            except psycopg2.Error as e:
                print(f"Ошибка базы данных: {e}")
                return None
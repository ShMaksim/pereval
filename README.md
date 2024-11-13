**Pereval API**

Этот REST API предназначен для управления информацией о горных перевалах. Он используется мобильным приложением, позволяющим туристам отправлять данные о перевалах, включая координаты, фотографии и информацию о пользователе. Сотрудники ФСТР затем модерируют отправленные данные.

**Задача**

Целью проекта является разработка REST API для взаимодействия с базой данных перевалов. API должен предоставлять функциональность для добавления, редактирования и просмотра информации о перевалах, а также для управления статусом модерации.

**Функциональность API**

**POST /submitData**

Добавляет новую запись о перевале.

Параметры запроса: Нет
Тело запроса(JSON):

```json
{
  "beauty_title": "пер. ",
  "title": "Пхия",
  "other_titles": "Триев",
  "connect": "",
  "add_time": "2023-10-26T12:00:00Z",
  "user": {
    "email": "user@example.com",
    "fam": "Пупкин",
    "name": "Василий",
    "otc": "Иванович",
    "phone": "+7 123 456 78 90"
  },
  "coords": {
    "latitude": 45.3842,
    "longitude": 7.1525,
    "height": 1200
  },
  "level": {
    "winter": null,
    "summer": "1А",
    "autumn": "1А",
    "spring": null
  },
  "images": [
    {"data": "<base64 encoded image>", "title": "Седловина"},
    {"data": "<base64 encoded image>", "title": "Подъём"}
  ]
}
```

Ответ(JSON):

Успешно (200 ОК):
{"status": 200, "message": null, "id": 42}

Ошибка валидации (400 Bad Request):
{"status": 400, "message": "Ошибка валидации: ...", "id": null}

Ошибка сервера (500 Internal Server Error):
{"status": 500, "message": "Ошибка базы данных: ...", "id": null}


**GET /submitData/{pereval_id}**

Возвращает данные о перевале по его ID

Параметры: pereval_id(int): ID перевала

Ответ (JSON):
Успешно (200 ОК): Данные о перевале
Не найдено (404 Not Found): Перевал не найден

**PATCH /submitData/{pereval_id}**

Редактирует данные о перевале

Параметры: pereval_id (int): ID перевала
Тело запроса (JSON): Аналогично POST /submitData, но без полей user

Ответ (JSON):
Успешно (204 No Content) или (200 OK):
{"state": 1, "message": "Перевал успешно обновлен"}

Ошибка (400 Bad Request) или (404 Not Found):
{"state": 0, "message": "Ошибка: ..."}

**GET /submitData/**

Возвращает список перевалов, добавленных пользователем

Параметры: user__email: Email пользователя

Ответ(JSON): Список объекта перевалов

Успешно (200 ОК): Список перевалов
Не найдено (404 Not Found): Перевалы не найдены

**Запуск приложения:**

Установите зависимости pip install -r requirements.txt
Настройте переменные окружения (см. ниже)
Запустите приложение uvicorn main:app --reload

**Переменные окружения:**

FSTR_DB_HOST
FSTR_DB_PORT
FSTR_DB_LOGIN
FSTR_DB_PASS

**Структура базы данных**

users: id (SERIAL PRIMARY KEY), email (TEXT UNIQUE), fam (TEXT), name (TEXT), otc (TEXT), phone (TEXT)

coords: id (SERIAL PRIMARY KEY), latitude (REAL), longitude (REAL), height (INTEGER)

pereval_added: id (SERIAL PRIMARY KEY), date_added (TIMESTAMP), beauty_title (TEXT), title (TEXT), other_titles (TEXT), connect (TEXT), add_time (TIMESTAMP), user_id (INTEGER REFERENCES users(id)), coord_id (INTEGER REFERENCES coords(id)), winter (TEXT), summer (TEXT), autumn (TEXT), spring (TEXT), status (TEXT)

pereval_images: id (SERIAL PRIMARY KEY), date_added (TIMESTAMP), img (TEXT), title (TEXT)

pereval_images_added: pereval_id (INTEGER REFERENCES pereval_added(id)), image_id (INTEGER REFERENCES pereval_images(id))


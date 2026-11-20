# tkapp
Авторизация + капча + окно администратора с использованием:
* `psycopg`
* `tkinter`

### Настройка БД
`init.sql`: скрипт для создания таблицы (PostgreSQL)
`DB`: строка подключения

### Запуск
```sh
python -m pip install psycopg[binary]
python main.py
```

Запуск через [uv](https://github.com/astral-sh/uv):
```sh
uv run main.py
```

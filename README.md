# Todo List — Лаб 5 & 6

**Стек:** Flask · Flask-SocketIO · PostgreSQL · Vue 3 · Nginx · Docker · GitHub Actions

## Структура проекта

```
project/
├── backend/
│   ├── app.py            # Flask + WebSocket (Socket.IO)
│   ├── models.py         # SQLAlchemy модели
│   ├── email_service.py  # SMTP / IMAP / POP3
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── index.html        # Vue 3 + Socket.IO клиент
│   ├── nginx.conf        # Nginx с WebSocket proxy
│   └── Dockerfile
├── docker-compose.yml
└── .github/
    └── workflows/
        └── ci-cd.yml     # GitHub Actions CI/CD
```

## Запуск

```bash
docker compose up --build
```

Приложение будет доступно по адресу: **http://localhost**

## Лаб 5 — WebSocket

### Как работает

1. Клиент подключается к `/socket.io` при загрузке страницы
2. Сервер отправляет событие `init` с текущим списком задач
3. При любом изменении (создание/обновление/удаление) через REST API сервер:
   - Выполняет операцию в БД
   - Вызывает `socketio.emit(...)` для broadcast всем клиентам
4. Все открытые вкладки/браузеры получают обновление мгновенно

### Проверка real-time синхронизации

1. Откройте http://localhost в двух разных браузерах/вкладках
2. Добавьте задачу в первом браузере — она появится во втором
3. Измените статус задачи — строка подсветится жёлтым у всех клиентов
4. Удалите задачу — она исчезнет у всех

## Лаб 6 — CI/CD (GitHub Actions)

### Настройка

1. Создайте аккаунт на Docker Hub
2. Добавьте секреты в репозиторий (Settings → Secrets → Actions):
   - `DOCKERHUB_USERNAME` — ваш логин на Docker Hub
   - `DOCKERHUB_TOKEN` — Access Token (не пароль!) с Docker Hub

### Что делает pipeline

| Шаг | Описание |
|-----|----------|
| Checkout | Клонирует репозиторий |
| Build images | Собирает образы backend и frontend |
| Start containers | Запускает `docker compose up -d` |
| HTTP tests | curl-тесты: health, GET, POST, PUT, DELETE |
| Stop & clean | `docker compose down -v`, `docker image prune` |
| Push to Hub | Пушит образы с тегами `latest` и SHA коммита |

### Email (необязательно)

Раскомментируйте в `docker-compose.yml`:

```yaml
EMAIL_USER: your@gmail.com
EMAIL_PASS: your-app-password   # App Password, не обычный пароль
```

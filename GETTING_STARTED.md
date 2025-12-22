# Start ITSM Tool

## Backend

```bash
cd itsm_backend
source venv/bin/activate
python manage.py runserver
```

→ http://localhost:8000

## Frontend

```bash
cd itsm-frontend
npm run dev
```

→ http://localhost:5173

## Database (if needed)

```bash
cd itsm_backend
docker-compose up -d mssql
```

# COMMANDS

## Backend

### Install dependencies
```bash
cd backend
python3 -m pip install -e '.[dev]'
```

### Run API (dev)
```bash
cd backend
uvicorn app.main:app --reload --env-file .env
```

### Run tests
```bash
cd backend
pytest
```

## Frontend

### Install dependencies
```bash
cd frontend
npm install
```

### Run app (dev)
```bash
cd frontend
npm run dev
```

### Frontend env required for auth/onboarding
```bash
NEXT_PUBLIC_SUPABASE_URL=...
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

Optional local-dev bypass token (if backend `ALLOW_DEV_AUTH=true`):

```bash
NEXT_PUBLIC_DEV_AUTH_TOKEN=local-dev-token
```

### Run tests
```bash
cd frontend
npm test
```

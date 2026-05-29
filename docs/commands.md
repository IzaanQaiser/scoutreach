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
uvicorn app.main:app --reload
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

### Run tests
```bash
cd frontend
npm test
```

# Life OS

Life OS is an AI-assisted second brain focused on decision quality, execution consistency, and adaptive planning.

## Architecture (current)

This implementation now uses **SQLAlchemy ORM** with a normalized domain model aligned to your `database.py` direction:

- `user_preferences`, `time_blocks`
- `goals`, `projects`, `tasks`, `resources`
- `task_dependencies`, `recurrence_rules`
- `inbox_items`, `inbox_classifications`
- `schedule_blocks`, `behavior_signals`

Core modules:

- `life_os/db.py`: ORM schema + `LifeOSRepository`
- `life_os/inbox.py`: Brain dump ingestion/classification
- `life_os/scheduler.py`: Priority + scheduling engine

## Run

```bash
python -m unittest discover -s tests -p 'test_*.py'
```

## Deploy non-locally (recommended path)

1. Add a small FastAPI layer on top of repository methods.
2. Containerize with Docker.
3. Deploy to Render/Fly/Cloud Run.
4. Move from SQLite to managed Postgres for production multi-device use.

# Database — Member 2 / QUADx

The database is **SQLite** for local hackathon testing. It is *not* a separate server.

- Database file on first run: `database/carbonease.db` (automatically created, ignored by Git).
- Table definitions and validation: `backend/carbon_api/models.py` (source of truth).
- Human-readable schema snapshot: `database/schema.sql` (reference only).
- Create database: `database/init_db.py` (also happens automatically at Flask startup).
- Optional fictional sample records: `database/seed_demo.py`.

## Create the tables

At the project root, after Python dependencies have been installed:

```powershell
.\backend\.venv\Scripts\python.exe database\init_db.py
```

The backend automatically seeds three **illustrative** emission factors into the `emission_factors` table. They must be replaced with verified values for real reporting.

## Add optional fake demo records

```powershell
.\backend\.venv\Scripts\python.exe database\seed_demo.py
```

This creates an example account with a public test password. Only run it on a local, disposable demo database.

## MySQL alternative

The backend supports MySQL through `PyMySQL`. Create a MySQL database, then set `DATABASE_URL=mysql+pymysql://...` inside your **local** `backend/.env` file. Never push a password or a real database dump to GitHub.

`database/schema.sql` uses SQLite syntax and is not the correct schema initialization method for MySQL. Use SQLAlchemy's `create_app()` instead.

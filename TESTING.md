# Local database safety

Run tests with `python manage.py test`. The default command selects
`config.test_settings`, which uses an in-memory SQLite database and local cache.
The `.env` database is not used by that test configuration.

For an explicit command, use:

```powershell
.\venv\Scripts\python.exe manage.py test --settings=config.test_settings
```

The shared test runner rejects all non-SQLite database aliases before Django
creates, reuses or deletes a test database, including when normal application
settings were selected explicitly. Server and migration commands keep their
existing configuration.

Run the safety regression checks with:

```powershell
.\venv\Scripts\python.exe manage.py test config.test_database_safety
```

These checks mock remote database configuration; they never connect to a remote
server. Do not override TEST_RUNNER to bypass this protection.

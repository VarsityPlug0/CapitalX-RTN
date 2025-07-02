## Environment Variables

This project uses environment variables for sensitive settings. Before running the app, create a `.env` file in the project root. You can start by copying the provided `.env.example`:

```
cp .env.example .env
```

Then, edit `.env` and set your own values for:
- `SECRET_KEY` (required)
- `DATABASE_URL` (optional, for PostgreSQL)

**Never commit your `.env` file to version control.** 
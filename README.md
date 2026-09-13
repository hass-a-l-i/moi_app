# Little Diary 🌷

A private end-of-day questionnaire with a welcome screen, one question at a time,
rotating daily themes and prompts, gratitude, needs, trends, history, and backup.

## Personalise it first

At the top of `streamlit_app.py`, change `HER_NAME`, `APP_TITLE`, `FROM_NAME`, and
any mood, feeling, need, or daily theme choices. Avoid putting private information
in a public GitHub repository.

## Run locally

Python 3.11+ is recommended.

```bash
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
streamlit run streamlit_app.py
```

Without cloud secrets, entries are stored in `diary.db` beside the app. That is
good for development, but hosted Streamlit storage is not durable.

## Create the hosted database

1. Create a free project at https://supabase.com/dashboard.
2. Open **SQL Editor**, paste in `supabase_setup.sql`, and run it.
3. In the project's API settings, copy the project URL and a server-side secret
   key. Depending on the dashboard wording, this may be called a **secret** key
   or the legacy **service_role** key. Never commit it to GitHub or expose it in
   browser code.

## Publish and get a link

1. Create a new GitHub repository, preferably private.
2. From this project folder, run:

```bash
git init
git add .
git commit -m "Create little diary"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

3. Visit https://share.streamlit.io, connect GitHub, and click **Create app**.
4. Select your repository, branch `main`, and entrypoint `streamlit_app.py`.
5. Open **Advanced settings** and paste these secrets, using your real values:

```toml
APP_PIN = "a-long-pin-only-the-two-of-you-know"
SUPABASE_URL = "https://YOUR-PROJECT.supabase.co"
SUPABASE_SECRET_KEY = "YOUR-SERVER-SIDE-SECRET-KEY"
```

6. Click **Deploy**. Streamlit will give you a `*.streamlit.app` link to send her.

## Privacy notes

- The GitHub code can be public, but use a private repository if you prefer.
- The PIN and database key belong only in Streamlit Secrets, never in a tracked
  `secrets.toml` file. `.gitignore` already excludes the local secrets file.
- Choose a long PIN/passphrase. This simple gate is lovely for a personal app,
  but it is not a substitute for full user authentication.
- Supabase Row Level Security is enabled and public database roles are revoked;
  the server-side Streamlit app is the only intended database client.
- She can download JSON backups from the Journey tab.

## Optional local cloud test

Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`, fill in the
three values, and restart Streamlit. Never commit that file.

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets as secret_tokens
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

import altair as alt
import pandas as pd
import requests
import streamlit as st


# ---------------------------------------------------------------------------
# PERSONAL CONFIGURATION
# ---------------------------------------------------------------------------

HER_NAME = "Moi's Moment"
APP_TITLE = "Your Daily Moment"
FROM_NAME = "Hassoon"


MOODS = {
    "Amazing!": (5, "🥰"),
    "Feeling good": (4, "😊"),
    "I'm okay": (3, "😌"),
    "A bit low": (2, "😔"),
    "Very low": (1, "🥺"),
}


FEELINGS = [
    "Loved",
    "Happy",
    "Calm",
    "Grateful",
    "Hopeful",
    "Proud",
    "Excited",
    "Content",
    "Joyful",
    "Peaceful",
    "Supported",
    "Appreciated",
    "Confident",
    "Motivated",
    "Playful",
    "Tired",
    "Stressed",
    "Anxious",
    "Sad",
    "Frustrated",
    "Overwhelmed",
    "Lonely",
    "Misunderstood",
    "Overstimulated",
]


NEEDS = [
    "A fat hug",
    "Reassurance",
    "Someone to listen",
    "Some quiet space",
    "Play some games",
    "Some rest",
    "A distraction",
    "Help/Advice",
    "Quality time",
    "Watch something",
    "To lock in",
    "Girls night",
    "Hassoon Meetup",
    "Something different",
    "Adventure",
    "I’m not sure yet",
]


ONE_STEP_CHECKLIST = [
    "Healthy eating - calorie counting",
    "Peppermint tea before bed",
    "NO social media",
    "Start fast 5pm",
    "Reading/Studying",
    "8 hours of sleep",
    "2 litres of water",
    "Outside activity",
    "No sugar",
    "Gym training",
]


DAILY_WORLDS = [
    (
        "Rose garden",
        "flowers/rose.png",
        "#fff5f7",
        "#f8d8e1",
        "#b83a62",
        "What made you feel loved today?",
    ),
    (
        "Sunflower meadow",
        "flowers/sunflower.png",
        "#fffbed",
        "#f9e7a7",
        "#a96f12",
        "What made you feel warm or hopeful today?",
    ),
    (
        "Lavender dream",
        "flowers/lavender.png",
        "#faf6ff",
        "#e7ddfa",
        "#7653ad",
        "What did you handle better than you realise today?",
    ),
    (
        "Cherry blossom",
        "flowers/cherry_blossom.png",
        "#fff7fa",
        "#f8dce8",
        "#bd6084",
        "What beautiful moment passed quickly today?",
    ),
    (
        "Peony paradise",
        "flowers/peony.png",
        "#fff5f8",
        "#f5d7e2",
        "#a94c72",
        "What brought a little colour into your day?",
    ),
    (
        "Bluebell woods",
        "flowers/bluebell.png",
        "#f5f7ff",
        "#dce3fa",
        "#526ba8",
        "Where did you find a moment of quiet today?",
    ),
    (
        "Orchid sanctuary",
        "flowers/orchid.png",
        "#fcf5ff",
        "#ebd8f5",
        "#814f9d",
        "What made you feel special or appreciated today?",
    ),
    (
        "Lily pond",
        "flowers/lily.png",
        "#f6fbfa",
        "#d8efea",
        "#3f8275",
        "What helped you feel peaceful today?",
    ),
    (
        "Magnolia morning",
        "flowers/magnolia.png",
        "#fff9f7",
        "#f0ded8",
        "#996b61",
        "How did you show yourself kindness today?",
    ),
    (
        "Iris garden",
        "flowers/iris.png",
        "#f7f5ff",
        "#ded8f4",
        "#62549b",
        "What achievement, big or small, made you proud today?",
    ),
    (
        "Hydrangea rain",
        "flowers/hydrangea.png",
        "#f3f8ff",
        "#d6e4f7",
        "#5277a3",
        "What brought you comfort today?",
    ),
]


# ---------------------------------------------------------------------------
# DAILY THEME
# ---------------------------------------------------------------------------

TODAY = date.today()

(
    WORLD_NAME,
    WORLD_ICON,
    BG_A,
    BG_B,
    ACCENT,
    DAILY_PROMPT,
) = DAILY_WORLDS[TODAY.toordinal() % len(DAILY_WORLDS)]

LOCAL_DB = Path(__file__).with_name("diary.db")


def icon_html(icon: str) -> str:
    """
    Return either an emoji or embedded local image HTML.

    Local paths are resolved relative to streamlit_app.py.
    """

    image_extensions = (".png", ".jpg", ".jpeg", ".webp", ".avif")

    if not icon.lower().endswith(image_extensions):
        return icon

    image_path = Path(__file__).parent / icon

    if not image_path.exists():
        return "🌹"

    image_bytes = image_path.read_bytes()

    if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        mime_type = "image/png"
    elif image_bytes.startswith(b"\xff\xd8\xff"):
        mime_type = "image/jpeg"
    elif image_bytes.startswith(b"RIFF") and image_bytes[8:12] == b"WEBP":
        mime_type = "image/webp"
    elif image_bytes[4:12] in {b"ftypavif", b"ftypavis"}:
        mime_type = "image/avif"
    else:
        mime_types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
            ".avif": "image/avif",
        }
        mime_type = mime_types.get(image_path.suffix.lower(), "image/png")

    encoded = base64.b64encode(image_bytes).decode("utf-8")

    return (
        f'<img src="data:{mime_type};base64,{encoded}" '
        f'alt="{WORLD_NAME}" '
        f'style="width:110px;height:110px;object-fit:contain;">'
    )


WORLD_ICON_HTML = icon_html(WORLD_ICON)


def hex_to_rgba(hex_color: str, alpha: float) -> str:
    """Convert a #rrggbb color to an rgba() CSS value."""

    clean_hex = hex_color.lstrip("#")
    red = int(clean_hex[0:2], 16)
    green = int(clean_hex[2:4], 16)
    blue = int(clean_hex[4:6], 16)

    return f"rgba({red}, {green}, {blue}, {alpha})"


ACCENT_WASH = hex_to_rgba(ACCENT, 0.1)
ACCENT_SOFT = hex_to_rgba(ACCENT, 0.16)
ACCENT_BORDER = hex_to_rgba(ACCENT, 0.34)
ACCENT_SHADOW = hex_to_rgba(ACCENT, 0.18)


# Use an emoji here because page_icon should not be an HTML image.
st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🌸",
    layout="centered",
)


# ---------------------------------------------------------------------------
# STYLING
# ---------------------------------------------------------------------------

st.markdown(
    f"""
    <style>
        :root,
        html,
        body,
        .stApp,
        [data-testid="stAppViewContainer"] {{
            --primary-color: {ACCENT} !important;
            --primary-color-background: {ACCENT_WASH} !important;
            --primary-color-border: {ACCENT_BORDER} !important;
            --secondary-background-color: {BG_B} !important;
            accent-color: {ACCENT};
        }}

        .stApp {{
            background: linear-gradient(145deg, {BG_A}, {BG_B});
        }}

        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        [data-testid="stStatusWidget"],
        [data-testid="stHeader"],
        #MainMenu,
        footer {{
            visibility: hidden;
            height: 0;
        }}

        .block-container {{
            max-width: 720px;
            padding-top: 2rem;
            padding-bottom: 5rem;
        }}

        h1, h2, h3 {{
            color: #493a43;
            letter-spacing: -0.025em;
        }}

        .hero {{
            background: linear-gradient(145deg, rgba(255, 255, 255, 0.82), {ACCENT_WASH});
            border: 1px solid {ACCENT_BORDER};
            border-radius: 32px;
            padding: 38px 30px;
            text-align: center;
            box-shadow: 0 18px 55px {ACCENT_SHADOW};
            margin: 16px 0 28px;
        }}

        .hero-icon {{
            font-size: 4.2rem;
            animation: float 3s ease-in-out infinite;
        }}

        .eyebrow {{
            text-transform: uppercase;
            letter-spacing: 0.16em;
            font-size: 0.72rem;
            font-weight: 700;
            color: {ACCENT};
        }}

        .hero h1 {{
            margin: 0.25rem 0 0.35rem;
        }}

        .hero p,
        .soft {{
            color: #725f69;
        }}

        .progress-shell {{
            height: 7px;
            background: {ACCENT_SOFT};
            border-radius: 99px;
            margin-bottom: 25px;
            overflow: hidden;
        }}

        .progress-fill {{
            height: 100%;
            background: {ACCENT};
            border-radius: 99px;
        }}

        .stButton > button {{
            border-radius: 999px;
            min-height: 3rem;
            border-color: {ACCENT};
        }}

        .stButton > button[kind="primary"] {{
            background: {ACCENT};
            color: white;
        }}

        .stButton > button[kind="secondary"] {{
            background: rgba(255, 255, 255, 0.68);
            border-color: {ACCENT_BORDER};
            color: #493a43;
        }}

        .stButton > button[kind="secondary"]:hover {{
            background: {ACCENT_WASH};
            border-color: {ACCENT};
            color: {ACCENT};
        }}

        [data-testid="stPopover"] button {{
            background: rgba(255, 255, 255, 0.74);
            border-color: {ACCENT_BORDER};
            color: #493a43;
        }}

        [data-testid="stPopover"] button:hover {{
            background: {ACCENT_WASH};
            border-color: {ACCENT};
            color: {ACCENT};
        }}

        [data-testid="stMetric"] {{
            background: linear-gradient(145deg, rgba(255, 255, 255, 0.8), {ACCENT_WASH});
            border-radius: 20px;
            padding: 14px;
            border: 1px solid {ACCENT_BORDER};
        }}

        div[role="radiogroup"] label {{
            background: rgba(255, 255, 255, 0.66);
            border: 1px solid {ACCENT_BORDER};
            padding: 0.7rem 1rem;
            border-radius: 16px;
            margin: 3px;
        }}

        div[role="radiogroup"] label:hover {{
            background: {ACCENT_WASH};
            border-color: {ACCENT};
        }}

        div[role="radiogroup"] label:has(input:checked) {{
            background: {ACCENT_SOFT};
            border-color: {ACCENT};
            box-shadow: 0 0 0 1px {ACCENT_BORDER};
        }}

        div[role="radiogroup"] label:has(input:checked) p {{
            color: {ACCENT};
            font-weight: 700;
        }}

        input[type="radio"],
        input[type="checkbox"] {{
            accent-color: {ACCENT} !important;
        }}

        [data-testid="stRadio"] label,
        [data-baseweb="radio"] [aria-checked="true"],
        [data-baseweb="radio"] [aria-checked="true"] > div,
        [data-baseweb="radio"] [aria-checked="true"] > div > div,
        [data-testid="stCheckbox"] label,
        [data-baseweb="radio"] input:checked + div,
        [data-baseweb="checkbox"] input:checked + div {{
            border-color: {ACCENT} !important;
        }}

        [data-baseweb="radio"] [aria-checked="true"] > div > div,
        [data-baseweb="radio"] input:checked + div > div,
        [data-baseweb="checkbox"] input:checked + div {{
            background-color: {ACCENT} !important;
        }}

        [data-baseweb="radio"] [aria-checked="true"] svg,
        [data-baseweb="checkbox"] input:checked + div svg {{
            color: white !important;
            fill: white !important;
        }}

        .stTextArea textarea,
        .stTextInput input,
        .stSelectbox [data-baseweb="select"] > div,
        .stMultiSelect [data-baseweb="select"] > div {{
            background: rgba(255, 255, 255, 0.74);
            border-color: {ACCENT_BORDER};
        }}

        .stTextArea textarea:focus,
        .stTextInput input:focus,
        .stSelectbox [data-baseweb="select"] > div:focus-within,
        .stMultiSelect [data-baseweb="select"] > div:focus-within {{
            border-color: {ACCENT};
            box-shadow: 0 0 0 1px {ACCENT};
        }}

        .stMultiSelect [data-baseweb="tag"] {{
            background-color: {ACCENT_SOFT} !important;
            border-color: {ACCENT_BORDER} !important;
            color: {ACCENT} !important;
        }}

        [data-baseweb="popover"] [role="option"]:hover,
        [data-baseweb="popover"] [aria-selected="true"] {{
            background-color: {ACCENT_WASH} !important;
            color: {ACCENT} !important;
        }}

        [data-baseweb="popover"] [aria-selected="true"] svg {{
            color: {ACCENT} !important;
            fill: {ACCENT} !important;
        }}

        [data-baseweb="slider"] [role="slider"] {{
            background-color: {ACCENT} !important;
            border-color: {ACCENT} !important;
            box-shadow: 0 0 0 4px {ACCENT_WASH} !important;
        }}

        [data-testid="stSlider"] div,
        [data-baseweb="slider"] > div > div {{
            border-color: {ACCENT_BORDER} !important;
        }}

        [data-testid="stSlider"] div[style*="rgb(212, 93, 140)"],
        [data-testid="stSlider"] div[style*="#d45d8c"],
        [data-baseweb="slider"] > div > div > div {{
            background-color: {ACCENT} !important;
        }}

        .stSlider [role="slider"] {{
            background-color: {ACCENT} !important;
            border-color: {ACCENT} !important;
            box-shadow: 0 0 0 4px {ACCENT_WASH} !important;
        }}

        .stSlider [data-testid="stTickBar"] {{
            color: {ACCENT};
        }}

        .rating-summary {{
            width: min(100%, 13rem);
            margin: 0.25rem auto 1rem;
            padding: 0.85rem 1rem;
            border-radius: 18px;
            background: linear-gradient(145deg, {ACCENT_SOFT}, rgba(255, 255, 255, 0.72));
            border: 1px solid {ACCENT_BORDER};
            text-align: center;
            box-shadow: 0 12px 28px {ACCENT_SHADOW};
        }}

        .rating-summary span {{
            display: block;
            color: {ACCENT};
            font-size: 2rem;
            font-weight: 800;
            line-height: 1;
        }}

        .rating-summary small {{
            color: #725f69;
            font-weight: 700;
        }}

        [style*="rgb(212, 93, 140)"] {{
            color: {ACCENT} !important;
            border-color: {ACCENT} !important;
            background-color: {ACCENT} !important;
        }}

        [style*="rgb(252, 232, 240)"] {{
            background-color: {ACCENT_WASH} !important;
            border-color: {ACCENT_BORDER} !important;
        }}

        [style*="#d45d8c"] {{
            color: {ACCENT} !important;
            border-color: {ACCENT} !important;
            background-color: {ACCENT} !important;
        }}

        [style*="#fce8f0"] {{
            background-color: {ACCENT_WASH} !important;
            border-color: {ACCENT_BORDER} !important;
        }}

        @keyframes float {{
            0%, 100% {{
                transform: translateY(0);
            }}

            50% {{
                transform: translateY(-8px);
            }}
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# SECRETS AND AUTHENTICATION
# ---------------------------------------------------------------------------

def secret(name: str) -> str:
    try:
        return str(st.secrets.get(name, ""))
    except FileNotFoundError:
        return ""


SUPABASE_URL = secret("SUPABASE_URL").rstrip("/")
SUPABASE_KEY = secret("SUPABASE_SECRET_KEY")

USE_CLOUD = bool(SUPABASE_URL and SUPABASE_KEY)


# ---------------------------------------------------------------------------
# DATABASE
# ---------------------------------------------------------------------------

def db_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(LOCAL_DB)

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS entries (
            entry_date TEXT PRIMARY KEY,
            mood INTEGER NOT NULL,
            mood_name TEXT NOT NULL,
            energy INTEGER NOT NULL,
            rating INTEGER NOT NULL DEFAULT 5,
            feelings TEXT NOT NULL,
            checklist TEXT NOT NULL DEFAULT '[]',
            note TEXT NOT NULL,
            gratitude TEXT NOT NULL,
            need TEXT NOT NULL,
            reflection TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )

    columns = {
        row[1]
        for row in connection.execute("PRAGMA table_info(entries)")
    }

    if "reflection" not in columns:
        connection.execute(
            """
            ALTER TABLE entries
            ADD COLUMN reflection TEXT NOT NULL DEFAULT ''
            """
        )

    if "rating" not in columns:
        connection.execute(
            """
            ALTER TABLE entries
            ADD COLUMN rating INTEGER NOT NULL DEFAULT 5
            """
        )

    if "checklist" not in columns:
        connection.execute(
            """
            ALTER TABLE entries
            ADD COLUMN checklist TEXT NOT NULL DEFAULT '[]'
            """
        )

    return connection


def cloud_request(
    method: str,
    query: str = "",
    payload: dict | None = None,
    table: str = "diary_entries",
) -> requests.Response:

    response = requests.request(
        method,
        f"{SUPABASE_URL}/rest/v1/{table}{query}",
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": (
                "return=representation,"
                "resolution=merge-duplicates"
            ),
        },
        json=payload,
        timeout=15,
    )

    response.raise_for_status()
    return response


PASSWORD_SETTING_KEY = "password_hash"
PASSWORD_ITERATIONS = 260_000


def get_setting(key: str) -> str:
    if USE_CLOUD:
        rows = cloud_request(
            "GET",
            f"?key=eq.{key}&select=value",
            table="app_settings",
        ).json()

        return str(rows[0]["value"]) if rows else ""

    with db_connection() as connection:
        row = connection.execute(
            "SELECT value FROM app_settings WHERE key = ?",
            (key,),
        ).fetchone()

    return str(row[0]) if row else ""


def set_setting(key: str, value: str) -> None:
    now = datetime.now().isoformat(timespec="seconds")

    if USE_CLOUD:
        cloud_request(
            "POST",
            "?on_conflict=key",
            {
                "key": key,
                "value": value,
                "updated_at": now,
            },
            table="app_settings",
        )
        return

    with db_connection() as connection:
        connection.execute(
            """
            INSERT INTO app_settings (key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key)
            DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
            """,
            (key, value, now),
        )


def hash_password(password: str) -> str:
    salt = secret_tokens.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        PASSWORD_ITERATIONS,
    ).hex()

    return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${salt}${digest}"


def password_matches(password: str, stored_hash: str) -> bool:
    try:
        algorithm, iterations, salt, expected = stored_hash.split("$", 3)
        iterations = int(iterations)
    except ValueError:
        return False

    if algorithm != "pbkdf2_sha256":
        return False

    actual = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        iterations,
    ).hex()

    return hmac.compare_digest(actual, expected)


def saved_list(value: object) -> list:
    if isinstance(value, list):
        return value

    if not value:
        return []

    try:
        loaded = json.loads(str(value))
    except json.JSONDecodeError:
        return []

    return loaded if isinstance(loaded, list) else []


def load_entries() -> list[dict]:
    if USE_CLOUD:
        entries = cloud_request(
            "GET",
            "?select=*&order=entry_date.desc",
        ).json()
    else:
        with db_connection() as connection:
            cursor = connection.execute(
                "SELECT * FROM entries ORDER BY entry_date DESC"
            )

            columns = [
                description[0]
                for description in cursor.description
            ]

            entries = [
                dict(zip(columns, row))
                for row in cursor.fetchall()
            ]

    for entry in entries:
        entry["rating"] = int(entry.get("rating") or 5)
        entry["feelings"] = saved_list(entry.get("feelings"))
        entry["checklist"] = saved_list(entry.get("checklist"))

    return entries


def save_entry(entry: dict) -> None:
    try:
        if USE_CLOUD:
            cloud_request(
                "POST",
                "?on_conflict=entry_date",
                entry,
            )
            return

        local_entry = entry | {
            "feelings": json.dumps(entry["feelings"]),
            "checklist": json.dumps(entry["checklist"]),
        }

        fields = ", ".join(local_entry)
        placeholders = ", ".join(
            f":{field}"
            for field in local_entry
        )

        updates = ", ".join(
            f"{field} = excluded.{field}"
            for field in local_entry
            if field not in {"entry_date", "created_at"}
        )

        query = f"""
            INSERT INTO entries ({fields})
            VALUES ({placeholders})
            ON CONFLICT(entry_date)
            DO UPDATE SET {updates}
        """

        with db_connection() as connection:
            connection.execute(query, local_entry)

    except Exception as error:
        st.error("Couldn't save this moment. Please try again.")
        st.exception(error)
        st.stop()


def delete_entry(entry_date: str) -> None:
    try:
        if USE_CLOUD:
            cloud_request(
                "DELETE",
                f"?entry_date=eq.{entry_date}",
            )
            return

        with db_connection() as connection:
            connection.execute(
                "DELETE FROM entries WHERE entry_date = ?",
                (entry_date,),
            )

    except Exception as error:
        st.error("Couldn't delete that page. Please try again.")
        st.exception(error)
        st.stop()


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def calculate_streak(entries: list[dict]) -> int:
    completed_days = {
        date.fromisoformat(entry["entry_date"])
        for entry in entries
    }

    if TODAY in completed_days:
        cursor = TODAY
    else:
        cursor = TODAY - timedelta(days=1)

    total = 0

    while cursor in completed_days:
        total += 1
        cursor -= timedelta(days=1)

    return total


def go(view: str, step: int | None = None) -> None:
    st.session_state.view = view

    if step is not None:
        st.session_state.step = step

    st.rerun()


def navigation_buttons(
    step: int,
    can_continue: bool = True,
) -> None:

    left, right = st.columns(2)

    with left:
        if st.button(
            "← Back",
            use_container_width=True,
        ):
            if step == 0:
                go("welcome")
            else:
                go("survey", step - 1)

    with right:
        if step < 8:
            if st.button(
                "Continue →",
                type="primary",
                use_container_width=True,
                disabled=not can_continue,
            ):
                go("survey", step + 1)


def choose_one(
    key: str,
    options: list,
    labels: dict | None = None,
    columns: int = 2,
) -> None:
    selected = st.session_state.answers.get(key)

    for row_start in range(0, len(options), columns):
        row_options = options[row_start:row_start + columns]
        row_columns = st.columns(len(row_options))

        for column, option in zip(row_columns, row_options):
            label = labels.get(option, option) if labels else option
            button_type = (
                "primary"
                if selected == option
                else "secondary"
            )

            with column:
                if st.button(
                    label,
                    key=f"{key}-{option}",
                    type=button_type,
                    use_container_width=True,
                ):
                    st.session_state.answers[key] = option
                    st.rerun()


def choose_many(
    key: str,
    options: list[str],
    columns: int = 3,
) -> None:
    selected = set(st.session_state.answers.get(key, []))

    for row_start in range(0, len(options), columns):
        row_options = options[row_start:row_start + columns]
        row_columns = st.columns(len(row_options))

        for column, option in zip(row_columns, row_options):
            button_type = (
                "primary"
                if option in selected
                else "secondary"
            )

            with column:
                if st.button(
                    option,
                    key=f"{key}-{option}",
                    type=button_type,
                    use_container_width=True,
                ):
                    if option in selected:
                        selected.remove(option)
                    else:
                        selected.add(option)

                    st.session_state.answers[key] = [
                        item for item in options if item in selected
                    ]
                    st.rerun()


def choose_scale(
    key: str,
    minimum: int,
    maximum: int,
    default: int,
) -> None:
    selected = st.session_state.answers.get(key, default)

    try:
        selected = int(selected)
    except (TypeError, ValueError):
        selected = default

    if selected not in range(minimum, maximum + 1):
        selected = default

    st.session_state.answers[key] = selected

    st.html(
        f"""
        <div class="rating-summary">
            <span>{selected}/10</span>
        </div>
        """
    )

    choose_one(
        key,
        list(range(minimum, maximum + 1)),
        labels={
            option: str(option)
            for option in range(minimum, maximum + 1)
        },
        columns=5,
    )


def themed_dropdown(
    label: str,
    key: str,
    options: list[str],
) -> str:
    if st.session_state.get(key) not in options:
        st.session_state[key] = options[0]

    selected = st.session_state[key]

    with st.popover(
        f"{label}:  {selected}",
        use_container_width=True,
    ):
        for option in options:
            if st.button(
                option,
                key=f"{key}-{option}",
                type=(
                    "primary"
                    if selected == option
                    else "secondary"
                ),
                use_container_width=True,
            ):
                st.session_state[key] = option
                st.rerun()

    return selected


def password_gate() -> None:
    stored_hash = get_setting(PASSWORD_SETTING_KEY)

    if stored_hash and st.session_state.get("authenticated"):
        return

    st.html(
        f"""
        <div class="hero">
            <div class="hero-icon">
                {WORLD_ICON_HTML}
            </div>

            <div class="eyebrow">
                Today is a {WORLD_NAME} day.
            </div>

            <h1>{HER_NAME}</h1>

            <p>
                This is a safe space where you can check in with yourself.
            </p>
        </div>
        """
    )

    if not stored_hash:
        with st.form("set_password_form"):
            password = st.text_input(
                "Create password",
                type="password",
            )
            confirmation = st.text_input(
                "Confirm password",
                type="password",
            )
            submitted = st.form_submit_button(
                "Set password",
                type="primary",
                use_container_width=True,
            )

        if submitted:
            if not password:
                st.error("Please enter a password.")
            elif len(password) < 8:
                st.error("Please use at least 8 characters.")
            elif password != confirmation:
                st.error("The passwords do not match.")
            else:
                set_setting(
                    PASSWORD_SETTING_KEY,
                    hash_password(password),
                )
                st.session_state.authenticated = True
                st.rerun()

        st.stop()

    with st.form("unlock_form"):
        password = st.text_input(
            "Password",
            type="password",
        )
        submitted = st.form_submit_button(
            "Unlock",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        if password_matches(password, stored_hash):
            st.session_state.authenticated = True
            st.rerun()

        st.error("That password did not unlock the diary.")

    st.stop()


# ---------------------------------------------------------------------------
# INITIAL STATE
# ---------------------------------------------------------------------------

st.session_state.setdefault("view", "welcome")
st.session_state.setdefault("step", 0)
st.session_state.setdefault("answers", {})
st.session_state.setdefault("authenticated", False)

try:
    password_gate()
except Exception as error:
    st.error(
        "The diary couldn't reach its password settings. "
        "Check the setup and app secrets."
    )
    st.exception(error)
    st.stop()


# Remove stale answers after options have been renamed.
answers = st.session_state.answers

if answers.get("mood_name") not in MOODS:
    answers.pop("mood_name", None)

saved_need = answers.get("need", "")

if "needs" not in answers:
    if saved_need in NEEDS:
        answers["needs"] = [saved_need]
    else:
        answers["needs"] = [
            need.strip()
            for need in str(saved_need).split(",")
            if need.strip() in NEEDS
        ]

answers["needs"] = [
    need
    for need in answers.get("needs", [])
    if need in NEEDS
]

answers.pop("need", None)

try:
    answers["rating"] = int(answers.get("rating", 5))
except (TypeError, ValueError):
    answers["rating"] = 5

if answers["rating"] not in range(1, 11):
    answers["rating"] = 5

answers["feelings"] = [
    feeling
    for feeling in answers.get("feelings", [])
    if feeling in FEELINGS
]

answers["checklist"] = [
    item
    for item in answers.get("checklist", [])
    if item in ONE_STEP_CHECKLIST
]

try:
    entries = load_entries()
except Exception as error:
    st.error(
        "The diary couldn't reach its database. "
        "Check the setup and app secrets."
    )
    st.exception(error)
    st.stop()


today_entry = next(
    (
        entry
        for entry in entries
        if entry["entry_date"] == TODAY.isoformat()
    ),
    None,
)


# ---------------------------------------------------------------------------
# WELCOME PAGE
# ---------------------------------------------------------------------------

if st.session_state.view == "welcome":
    st.html(
        f"""
        <div class="hero">
            <div class="hero-icon">
                {WORLD_ICON_HTML}
            </div>

            <div class="eyebrow">
                Today is a {WORLD_NAME} day.
            </div>

            <h1>{HER_NAME}</h1>

            <p>
                This is a safe space where you can check in with yourself.
            </p>
        </div>
        """
    )

    if today_entry:
        mood_icon = MOODS.get(
            today_entry.get("mood_name"),
            (3, "😌"),
        )[1]

        if st.button(
            "Update today’s moment",
            type="primary",
            use_container_width=True,
        ):
            saved_answers = {
                key: today_entry.get(key, "")
                for key in [
                    "mood_name",
                    "energy",
                    "rating",
                    "feelings",
                    "checklist",
                    "need",
                    "gratitude",
                    "note",
                    "reflection",
                ]
            }

            if saved_answers.get("mood_name") not in MOODS:
                saved_answers.pop("mood_name", None)

            if saved_answers.get("need") in NEEDS:
                saved_answers["needs"] = [saved_answers["need"]]
            else:
                saved_answers["needs"] = [
                    need.strip()
                    for need in str(
                        saved_answers.get("need", "")
                    ).split(",")
                    if need.strip() in NEEDS
                ]

            saved_answers.pop("need", None)

            saved_answers["feelings"] = [
                feeling
                for feeling in saved_answers.get(
                    "feelings",
                    [],
                )
                if feeling in FEELINGS
            ]

            saved_answers["checklist"] = [
                item
                for item in saved_answers.get(
                    "checklist",
                    [],
                )
                if item in ONE_STEP_CHECKLIST
            ]

            st.session_state.answers = saved_answers
            go("survey", 0)

    else:
        if st.button(
            "Begin today’s moment →",
            type="primary",
            use_container_width=True,
        ):
            st.session_state.answers = {}
            go("survey", 0)

    if st.button(
        "See all your moments",
        use_container_width=True,
    ):
        go("journey")

    st.markdown(
        f"""
        <p
            class="soft"
            style="text-align:center; margin-top:24px;"
        >
            A new flower, colour and final question
            every day.
            <br>
            By {FROM_NAME} 💗
        </p>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# SURVEY
# ---------------------------------------------------------------------------

elif st.session_state.view == "survey":
    answers = st.session_state.answers
    step = st.session_state.step

    question_titles = [
        "How did today feel overall?",
        "How was your energy?",
        "How would you rate today?",
        "Which feelings showed up?",
        "What do you need right now?",
        "What are you grateful for?",
        "What are you looking forward to tomorrow?",
        "One step at a time checklist",
        DAILY_PROMPT,
    ]

    progress = ((step + 1) / len(question_titles)) * 100

    st.markdown(
        f"""
        <div class="progress-shell">
            <div
                class="progress-fill"
                style="width:{progress:.0f}%"
            >
            </div>
        </div>

        <div class="eyebrow">
            Question {step + 1} of {len(question_titles)}
        </div>

        <h2>{question_titles[step]}</h2>
        """,
        unsafe_allow_html=True,
    )

    # Question 1: mood
    if step == 0:
        mood_options = list(MOODS)
        choose_one(
            "mood_name",
            mood_options,
            labels={
                mood: f"{MOODS[mood][1]}  {mood}"
                for mood in mood_options
            },
            columns=1,
        )

        navigation_buttons(
            step,
            bool(answers.get("mood_name")),
        )

    # Question 2: energy
    elif step == 1:
        current_energy = answers.get("energy", 3)

        try:
            current_energy = int(current_energy)
        except (TypeError, ValueError):
            current_energy = 3

        if current_energy not in [1, 2, 3, 4, 5]:
            current_energy = 3

        answers["energy"] = current_energy

        energy_options = [1, 2, 3, 4, 5]
        choose_one(
            "energy",
            energy_options,
            labels={
                1: "Empty",
                2: "Low",
                3: "Steady",
                4: "Good",
                5: "Full",
            },
            columns=5,
        )

        navigation_buttons(step)

    # Question 3: daily rating
    elif step == 2:
        current_rating = answers.get("rating", 5)

        try:
            current_rating = int(current_rating)
        except (TypeError, ValueError):
            current_rating = 5

        if current_rating not in range(1, 11):
            current_rating = 5

        choose_scale("rating", 1, 10, current_rating)

        navigation_buttons(step)

    # Question 4: feelings
    elif step == 3:
        st.markdown("Choose as many as you need.")
        choose_many("feelings", FEELINGS)

        navigation_buttons(
            step,
            bool(answers.get("feelings")),
        )

    # Question 5: needs
    elif step == 4:
        st.markdown("Choose as many as you like.")

        choose_many("needs", NEEDS)

        navigation_buttons(
            step,
            bool(answers.get("needs")),
        )

    # Question 6: gratitude
    elif step == 5:
        answers["gratitude"] = st.text_area(
            "Gratitude",
            value=answers.get("gratitude", ""),
            placeholder=(
                "It can be absolutely anything no matter how small…"
            ),
            height=150,
            label_visibility="collapsed",
        )

        navigation_buttons(
            step,
            bool(answers["gratitude"].strip()),
        )

    # Question 7: looking forward
    elif step == 6:
        answers["note"] = st.text_area(
            "Day",
            value=answers.get("note", ""),
            placeholder=(
                "Something small or something big, "
                "whatever you’re looking forward to…"
            ),
            height=190,
            label_visibility="collapsed",
        )

        navigation_buttons(step)

    # Question 8: one step at a time checklist
    elif step == 7:
        st.markdown("Tick anything that applies today.")

        choose_many(
            "checklist",
            ONE_STEP_CHECKLIST,
            columns=2,
        )

        navigation_buttons(step)

    # Question 9: rotating daily reflection
    else:
        answers["reflection"] = st.text_area(
            "Reflection",
            value=answers.get("reflection", ""),
            placeholder="Whatever comes to mind…",
            height=170,
            label_visibility="collapsed",
        )

        left, right = st.columns(2)

        with left:
            if st.button(
                "← Back",
                use_container_width=True,
            ):
                go("survey", 7)

        with right:
            if st.button(
                "Finish my moment",
                type="primary",
                use_container_width=True,
            ):
                selected_mood = answers.get("mood_name")

                if selected_mood not in MOODS:
                    st.error(
                        "Please go back and choose your mood."
                    )
                    st.stop()

                selected_needs = answers.get("needs", [])

                if not selected_needs:
                    st.error(
                        "Please go back and choose what you need."
                    )
                    st.stop()

                now = datetime.now().isoformat(
                    timespec="seconds"
                )

                save_entry(
                    {
                        "entry_date": TODAY.isoformat(),
                        "mood": MOODS[selected_mood][0],
                        "mood_name": selected_mood,
                        "energy": answers.get("energy", 3),
                        "rating": answers.get("rating", 5),
                        "feelings": answers.get(
                            "feelings",
                            [],
                        ),
                        "checklist": answers.get(
                            "checklist",
                            [],
                        ),
                        "need": ", ".join(selected_needs),
                        "gratitude": answers.get(
                            "gratitude",
                            "",
                        ).strip(),
                        "note": answers.get(
                            "note",
                            "",
                        ).strip(),
                        "reflection": answers.get(
                            "reflection",
                            "",
                        ).strip(),
                        "created_at": (
                            today_entry.get(
                                "created_at",
                                now,
                            )
                            if today_entry
                            else now
                        ),
                        "updated_at": now,
                    }
                )

                go("complete")


# ---------------------------------------------------------------------------
# COMPLETION PAGE
# ---------------------------------------------------------------------------

elif st.session_state.view == "complete":
    mood = st.session_state.answers.get("mood_name")

    if mood not in MOODS:
        mood = next(iter(MOODS))

    mood_icon = MOODS[mood][1]

    st.html(
        """
        <div class="flower-fall" aria-hidden="true">
            <span style="--x: 6%; --delay: 0s; --duration: 7.8s; --size: 1.4rem;">🌸</span>
            <span style="--x: 16%; --delay: 1.1s; --duration: 8.6s; --size: 1.1rem;">🌺</span>
            <span style="--x: 27%; --delay: 0.4s; --duration: 7.2s; --size: 1.3rem;">🌷</span>
            <span style="--x: 39%; --delay: 1.8s; --duration: 8.9s; --size: 1rem;">🌸</span>
            <span style="--x: 51%; --delay: 0.7s; --duration: 7.6s; --size: 1.5rem;">🌼</span>
            <span style="--x: 63%; --delay: 1.4s; --duration: 8.2s; --size: 1.2rem;">🌸</span>
            <span style="--x: 75%; --delay: 0.2s; --duration: 7.4s; --size: 1.4rem;">🌺</span>
            <span style="--x: 87%; --delay: 1.6s; --duration: 8.7s; --size: 1.1rem;">🌷</span>
            <span style="--x: 95%; --delay: 0.9s; --duration: 7.9s; --size: 1.3rem;">🌸</span>
        </div>

        <style>
            .flower-fall {
                position: fixed;
                inset: 0;
                z-index: 999999;
                pointer-events: none;
                overflow: hidden;
            }

            .flower-fall span {
                position: absolute;
                top: -3rem;
                left: var(--x);
                font-size: var(--size);
                animation:
                    flower-fall var(--duration) linear var(--delay) infinite,
                    flower-sway 2.8s ease-in-out var(--delay) infinite;
                opacity: 0.9;
                filter: drop-shadow(0 6px 10px rgba(110, 70, 90, 0.16));
            }

            @keyframes flower-fall {
                from {
                    transform: translate3d(0, -4rem, 0) rotate(0deg);
                }

                to {
                    transform: translate3d(0, 110vh, 0) rotate(360deg);
                }
            }

            @keyframes flower-sway {
                0%, 100% {
                    margin-left: -18px;
                }

                50% {
                    margin-left: 18px;
                }
            }
        </style>
        """
    )

    st.html(
        f"""
        <div class="hero">
            <div class="hero-icon">{mood_icon}</div>

            <div class="eyebrow">
                Moment complete
            </div>

            <h1>Your Moi moment is now complete.</h1>

            <p>
                Whatever you felt today, remember you are loved, appreciated, and never alone.
                Be kind to yourself my love.
            </p>
        </div>
        """
    )

    if st.button(
        "See my journey",
        type="primary",
        use_container_width=True,
    ):
        go("journey")

    if st.button(
        "Back home",
        use_container_width=True,
    ):
        go("welcome")


# ---------------------------------------------------------------------------
# JOURNEY PAGE
# ---------------------------------------------------------------------------

elif st.session_state.view == "journey":
    if st.button("← Home"):
        go("welcome")

    st.markdown(f"## {WORLD_ICON_HTML} Moi moments", unsafe_allow_html=True)

    if not entries:
        st.info(
            "Your days will collect here "
            "after your first moment."
        )
        st.stop()

    st.markdown("### Your Journey")

    range_options = ["Last week", "Last month", "All time"]
    focus_options = [
        "All",
        "Mood",
        "Energy",
        "Checklist",
        "Daily rating",
    ]
    st.session_state.setdefault("chart_range", "Last week")
    st.session_state.setdefault("chart_focus", "All")

    focus_column, range_column = st.columns(2)

    with focus_column:
        selected_focus = themed_dropdown(
            "Line",
            "chart_focus",
            focus_options,
        )

    with range_column:
        selected_range = themed_dropdown(
            "Time window",
            "chart_range",
            range_options,
        )

    range_start = {
        "Last week": TODAY - timedelta(days=6),
        "Last month": TODAY - timedelta(days=29),
        "All time": date.min,
    }[selected_range]

    chart_entries = [
        entry
        for entry in entries
        if date.fromisoformat(entry["entry_date"]) >= range_start
    ]

    column_1, column_2, column_3, column_4, column_5 = st.columns(5)
    n = len(chart_entries)

    column_1.metric("Total", len(entries))
    column_2.metric("Streak", f"{calculate_streak(entries)} 🔥")
    column_3.metric(
        "Mood Av.",
        f"{sum(int(e['mood']) for e in chart_entries) / n:.1f}/5" if n else "—",
    )
    column_4.metric(
        "Energy Av.",
        f"{sum(int(e['energy']) for e in chart_entries) / n:.1f}/5" if n else "—",
    )
    column_5.metric(
        "Rating Av.",
        f"{sum(int(e.get('rating', 5)) for e in chart_entries) / n:.1f}/10" if n else "—",
    )

    if not chart_entries:
        st.info("No moments in this range yet.")
        st.stop()

    chart = pd.DataFrame(chart_entries)
    chart["Date"] = pd.to_datetime(chart["entry_date"])
    chart["Rating"] = chart.get("rating", 5).fillna(5).astype(int)
    chart["Checklist"] = chart["checklist"].apply(len)
    chart = chart.sort_values("Date").set_index("Date")

    chart_data = (
        chart[["mood", "energy", "Checklist", "Rating"]]
        .rename(
            columns={
                "mood": "Mood",
                "energy": "Energy",
                "Rating": "Daily rating",
            }
        )
        .reset_index()
        .melt(
            "Date",
            var_name="Tracker",
            value_name="Score",
        )
    )

    if selected_focus != "All":
        chart_data = chart_data[
            chart_data["Tracker"] == selected_focus
        ]

    chart_data["Score"] = chart_data["Score"].astype(float)
    chart_data["Display"] = chart_data["Score"]

    if selected_focus == "All":
        scaled = chart_data["Tracker"].isin(["Mood", "Energy"])
        chart_data.loc[scaled, "Display"] = (
            chart_data.loc[scaled, "Score"] * 2
        )

    tracker_colors = {
        "Mood": "#3f5f96",
        "Energy": "#b7652a",
        "Checklist": "#3b7f63",
        "Daily rating": "#d45d8c",
    }

    visible = list(chart_data["Tracker"].unique())
    y_max = 5 if selected_focus in {"Mood", "Energy"} else 10

    chart_base = alt.Chart(chart_data).encode(
        x=alt.X(
            "Date:T",
            title=None,
            axis=alt.Axis(format="%d %b", labelAngle=0),
        ),
        y=alt.Y(
            "Display:Q",
            title="Score",
            scale=alt.Scale(domain=[0, y_max]),
            axis=alt.Axis(
                values=(
                    [0, 1, 2, 3, 4, 5]
                    if y_max == 5
                    else [0, 2, 4, 6, 8, 10]
                )
            ),
        ),
        color=alt.Color(
            "Tracker:N",
            scale=alt.Scale(
                domain=visible,
                range=[tracker_colors[name] for name in visible],
            ),
            legend=(
                alt.Legend(orient="top", title=None)
                if selected_focus == "All"
                else None
            ),
        ),
        tooltip=[
            alt.Tooltip("Date:T", title="Date", format="%A, %d %B"),
            alt.Tooltip("Tracker:N", title="Tracker"),
            alt.Tooltip("Score:Q", title="Score", format=".0f"),
        ],
    )

    line = chart_base.mark_line(
        interpolate="monotone",
        strokeWidth=2 if selected_focus != "All" else 1.5,
    )

    points = chart_base.mark_circle(
        size=90 if selected_focus != "All" else 65,
        opacity=0.95,
    )

    st.altair_chart(
        (line + points).properties(height=300),
        use_container_width=True,
    )

    st.markdown("### Your Diary")

    for entry in entries:
        saved_mood_name = entry.get(
            "mood_name",
            "Unknown mood",
        )

        saved_mood_icon = MOODS.get(
            saved_mood_name,
            (0, "💗"),
        )[1]

        entry_date = date.fromisoformat(
            entry["entry_date"]
        )

        label = (
            f"{saved_mood_icon}  "
            f"{entry_date.strftime('%A, %d %B')} "
            f"· {saved_mood_name}"
        )

        with st.expander(label):
            st.write(
                f"**Energy:** {entry.get('energy', '—')}/5"
            )

            st.write(
                f"**Daily rating:** {entry.get('rating', 5)}/10"
            )

            saved_feelings = entry.get("feelings", [])

            if saved_feelings:
                st.write(
                    "**Felt:** "
                    + ", ".join(saved_feelings)
                )

            saved_checklist = entry.get("checklist", [])

            st.write(
                f"**Checklist:** "
                f"{len(saved_checklist)}/{len(ONE_STEP_CHECKLIST)}"
            )

            if saved_checklist:
                st.write(
                    "**Completed:** "
                    + ", ".join(saved_checklist)
                )

            st.write(
                f"**Needed:** {entry.get('need', '—')}"
            )

            if entry.get("gratitude"):
                st.write(
                    f"**Grateful for:** "
                    f"{entry['gratitude']}"
                )

            if entry.get("note"):
                st.write(
                    f"**Looking forward to tomorrow:** "
                    f"{entry['note']}"
                )

            if entry.get("reflection"):
                st.write(
                    f"**Daily reflection:** "
                    f"{entry['reflection']}"
                )

            if st.button(
                "Delete this page",
                key=f"delete-{entry['entry_date']}",
            ):
                delete_entry(entry["entry_date"])
                st.rerun()

    st.download_button(
        "Download private backup",
        data=json.dumps(
            entries,
            indent=2,
            ensure_ascii=False,
        ),
        file_name=f"little-diary-{TODAY}.json",
        mime="application/json",
        use_container_width=True,
    )


# Recover gracefully if the view value becomes invalid.
else:
    st.session_state.view = "welcome"
    st.rerun()

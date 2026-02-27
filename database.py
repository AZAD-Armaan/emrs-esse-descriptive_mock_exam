import os
import sqlite3
from datetime import datetime
from contextlib import contextmanager

# ─── Pick database based on environment ───────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "")
USE_POSTGRES = DATABASE_URL.startswith("postgresql") or DATABASE_URL.startswith("postgres")

# ══════════════════════════════════════════════════════════════════
#  CONNECTION HELPERS
# ══════════════════════════════════════════════════════════════════
@contextmanager
def get_db():
    if USE_POSTGRES:
        import psycopg2
        import psycopg2.extras
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    else:
        conn = sqlite3.connect("emrs_exam.db", check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


def fetchall(cursor):
    """Return list of dicts from cursor — works for both SQLite and Postgres."""
    cols = [d[0] for d in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]

def fetchone(cursor):
    """Return single dict from cursor — works for both SQLite and Postgres."""
    cols = [d[0] for d in cursor.description]
    row  = cursor.fetchone()
    return dict(zip(cols, row)) if row else None

def placeholder():
    """Return correct SQL placeholder: ? for SQLite, %s for Postgres."""
    return "%s" if USE_POSTGRES else "?"

def ph(n=1):
    """Return n placeholders as a comma-separated string."""
    p = placeholder()
    return ", ".join([p] * n)


# ══════════════════════════════════════════════════════════════════
#  INIT & MIGRATIONS
# ══════════════════════════════════════════════════════════════════
def init_db():
    with get_db() as conn:
        cur = conn.cursor()
        if USE_POSTGRES:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    name TEXT,
                    picture TEXT,
                    role TEXT DEFAULT 'student',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )""")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS exam_sessions (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    is_active INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    closed_at TIMESTAMP
                )""")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS questions (
                    id SERIAL PRIMARY KEY,
                    question_text TEXT NOT NULL,
                    marks INTEGER DEFAULT 4,
                    hint TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active INTEGER DEFAULT 0,
                    session_id INTEGER
                )""")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS submissions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    question_id INTEGER NOT NULL,
                    session_id INTEGER NOT NULL,
                    answer_text TEXT,
                    answer_image BYTEA,
                    answer_image_name TEXT,
                    answer_type TEXT DEFAULT 'text',
                    score REAL,
                    max_score INTEGER DEFAULT 4,
                    feedback TEXT,
                    evaluated_at TIMESTAMP,
                    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (question_id) REFERENCES questions(id),
                    UNIQUE(user_id, question_id, session_id)
                )""")
        else:
            cur.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    name TEXT, picture TEXT,
                    role TEXT DEFAULT 'student',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS exam_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL, description TEXT,
                    is_active INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    closed_at TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question_text TEXT NOT NULL,
                    marks INTEGER DEFAULT 4, hint TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active INTEGER DEFAULT 0, session_id INTEGER
                );
                CREATE TABLE IF NOT EXISTS submissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    question_id INTEGER NOT NULL,
                    session_id INTEGER NOT NULL,
                    answer_text TEXT,
                    answer_image BLOB,
                    answer_image_name TEXT,
                    answer_type TEXT DEFAULT 'text',
                    score REAL, max_score INTEGER DEFAULT 4,
                    feedback TEXT, evaluated_at TIMESTAMP,
                    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (question_id) REFERENCES questions(id),
                    UNIQUE(user_id, question_id, session_id)
                );
            """)
            _run_migrations(cur)

def _run_migrations(cur):
    """Safely add missing columns to existing SQLite databases."""
    migrations = [
        ("submissions", "answer_image",      "BLOB"),
        ("submissions", "answer_image_name", "TEXT"),
        ("submissions", "answer_type",       "TEXT DEFAULT 'text'"),
    ]
    for table, column, col_type in migrations:
        cur.execute(f"PRAGMA table_info({table})")
        existing = [row[1] for row in cur.fetchall()]
        if column not in existing:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")


# ══════════════════════════════════════════════════════════════════
#  USER OPERATIONS
# ══════════════════════════════════════════════════════════════════
def upsert_user(email, name, picture):
    p = placeholder()
    with get_db() as conn:
        cur = conn.cursor()
        if USE_POSTGRES:
            cur.execute(f"""
                INSERT INTO users (email, name, picture)
                VALUES ({p},{p},{p})
                ON CONFLICT(email) DO UPDATE SET name=EXCLUDED.name, picture=EXCLUDED.picture
            """, (email, name, picture))
        else:
            cur.execute(f"""
                INSERT INTO users (email, name, picture) VALUES ({p},{p},{p})
                ON CONFLICT(email) DO UPDATE SET name=excluded.name, picture=excluded.picture
            """, (email, name, picture))
    return get_user_by_email(email)

def get_user_by_email(email):
    p = placeholder()
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM users WHERE email={p}", (email,))
        return fetchone(cur)

def set_admin(email):
    p = placeholder()
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(f"UPDATE users SET role='admin' WHERE email={p}", (email,))

def get_all_users():
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users ORDER BY name")
        return fetchall(cur)


# ══════════════════════════════════════════════════════════════════
#  SESSION OPERATIONS
# ══════════════════════════════════════════════════════════════════
def create_session(title, description=""):
    p = placeholder()
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE exam_sessions SET is_active=0")
        cur.execute(
            f"INSERT INTO exam_sessions (title, description, is_active) VALUES ({p},{p},1)",
            (title, description)
        )
        if USE_POSTGRES:
            cur.execute("SELECT lastval()")
        else:
            cur.execute("SELECT last_insert_rowid()")
        return cur.fetchone()[0]

def get_active_session():
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM exam_sessions WHERE is_active=1")
        return fetchone(cur)

def close_session(session_id):
    p = placeholder()
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            f"UPDATE exam_sessions SET is_active=0, closed_at={p} WHERE id={p}",
            (datetime.now(), session_id)
        )

def get_all_sessions():
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM exam_sessions ORDER BY created_at DESC")
        return fetchall(cur)


# ══════════════════════════════════════════════════════════════════
#  QUESTION OPERATIONS
# ══════════════════════════════════════════════════════════════════
def add_question(session_id, question_text, marks=4, hint=""):
    p = placeholder()
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            f"INSERT INTO questions (question_text, marks, hint, is_active, session_id) VALUES ({p},{p},{p},1,{p})",
            (question_text, marks, hint, session_id)
        )

def get_questions_for_session(session_id):
    p = placeholder()
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            f"SELECT * FROM questions WHERE session_id={p} AND is_active=1 ORDER BY id",
            (session_id,)
        )
        return fetchall(cur)

def delete_question(question_id):
    p = placeholder()
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(f"DELETE FROM questions WHERE id={p}", (question_id,))


# ══════════════════════════════════════════════════════════════════
#  SUBMISSION OPERATIONS
# ══════════════════════════════════════════════════════════════════
def save_answer(user_id, question_id, session_id,
                answer_text=None, answer_image=None,
                answer_image_name=None, answer_type="text"):
    p = placeholder()
    with get_db() as conn:
        cur = conn.cursor()
        if USE_POSTGRES:
            cur.execute(f"""
                INSERT INTO submissions
                    (user_id, question_id, session_id, answer_text, answer_image, answer_image_name, answer_type)
                VALUES ({p},{p},{p},{p},{p},{p},{p})
                ON CONFLICT(user_id, question_id, session_id) DO UPDATE SET
                    answer_text=EXCLUDED.answer_text,
                    answer_image=EXCLUDED.answer_image,
                    answer_image_name=EXCLUDED.answer_image_name,
                    answer_type=EXCLUDED.answer_type,
                    submitted_at=CURRENT_TIMESTAMP
            """, (user_id, question_id, session_id, answer_text,
                  answer_image, answer_image_name, answer_type))
        else:
            cur.execute(f"""
                INSERT INTO submissions
                    (user_id, question_id, session_id, answer_text, answer_image, answer_image_name, answer_type)
                VALUES ({p},{p},{p},{p},{p},{p},{p})
                ON CONFLICT(user_id, question_id, session_id) DO UPDATE SET
                    answer_text=excluded.answer_text,
                    answer_image=excluded.answer_image,
                    answer_image_name=excluded.answer_image_name,
                    answer_type=excluded.answer_type,
                    submitted_at=CURRENT_TIMESTAMP
            """, (user_id, question_id, session_id, answer_text,
                  answer_image, answer_image_name, answer_type))

def save_evaluation(submission_id, score, feedback):
    p = placeholder()
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            f"UPDATE submissions SET score={p}, feedback={p}, evaluated_at={p} WHERE id={p}",
            (score, feedback, datetime.now(), submission_id)
        )

def get_user_submissions(user_id, session_id):
    p = placeholder()
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(f"""
            SELECT s.*, q.question_text, q.marks as max_marks
            FROM submissions s
            JOIN questions q ON s.question_id = q.id
            WHERE s.user_id={p} AND s.session_id={p}
            ORDER BY q.id
        """, (user_id, session_id))
        return fetchall(cur)

def get_all_submissions_for_session(session_id):
    p = placeholder()
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(f"""
            SELECT s.*, u.name as student_name, u.email as student_email,
                   q.question_text, q.marks as max_marks
            FROM submissions s
            JOIN users u ON s.user_id = u.id
            JOIN questions q ON s.question_id = q.id
            WHERE s.session_id={p}
            ORDER BY u.name, q.id
        """, (session_id,))
        return fetchall(cur)

def get_unevaluated_submissions(session_id):
    p = placeholder()
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(f"""
            SELECT s.*, u.name as student_name, q.question_text, q.marks as max_marks
            FROM submissions s
            JOIN users u ON s.user_id = u.id
            JOIN questions q ON s.question_id = q.id
            WHERE s.session_id={p}
              AND s.score IS NULL
              AND (s.answer_text IS NOT NULL OR s.answer_image IS NOT NULL)
        """, (session_id,))
        return fetchall(cur)

def get_rankings(session_id):
    p = placeholder()
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(f"""
            SELECT u.name, u.email, u.picture,
                   SUM(s.score) as total_score,
                   SUM(q.marks) as total_max,
                   COUNT(s.id) as answered,
                   COUNT(CASE WHEN s.score IS NOT NULL THEN 1 END) as evaluated
            FROM users u
            JOIN submissions s ON u.id = s.user_id
            JOIN questions q ON s.question_id = q.id
            WHERE s.session_id={p}
              AND (s.answer_text IS NOT NULL OR s.answer_image IS NOT NULL)
            GROUP BY u.id, u.name, u.email, u.picture
            ORDER BY total_score DESC NULLS LAST
        """, (session_id,))
        return fetchall(cur)
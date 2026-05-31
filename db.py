import sqlite3

DATABASE_NAME = "coding_guru.db"


def get_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn



def init_db():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id TEXT NOT NULL,
            problem_id TEXT NOT NULL,

            status TEXT NOT NULL,

            language TEXT,

            latest_code TEXT,

            hint_level INTEGER DEFAULT 0,

            chat_history TEXT,

            review_correctness TEXT,
            review_time_complexity TEXT,
            review_space_complexity TEXT,
            review_feedback TEXT,
            review_score REAL,

            started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(user_id, problem_id)
        )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        session_id INTEGER NOT NULL,

        role TEXT NOT NULL,

        content TEXT NOT NULL,

        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (session_id)
        REFERENCES sessions(id)
    )
""")

    conn.commit()
    conn.close()

import json

def create_session(user_id, problem_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO sessions (
            user_id,
            problem_id,
            status,
            hint_level,
            chat_history
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            user_id,
            problem_id,
            "yet_to_solve",
            0,
            json.dumps([])
        )
    )

    conn.commit()

    cursor.execute(
        """
        SELECT * FROM sessions
        WHERE user_id = ? AND problem_id = ?
        """,
        (user_id, problem_id)
    )

    new_session = cursor.fetchone()

    conn.close()

    return new_session


def get_session(user_id, problem_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT * FROM sessions
        WHERE user_id = ? AND problem_id = ?
        """,
        (user_id, problem_id)
    )

    session = cursor.fetchone()

    conn.close()

    return session

def update_code(session_id, code):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE sessions
        SET latest_code = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (code, session_id)
    )

    conn.commit()

    cursor.execute(
        """
        SELECT * FROM sessions
        WHERE id = ?
        """,
        (session_id,)
    )

    updated_session = cursor.fetchone()

    conn.close()

    return updated_session

def update_chat_history(session_id, chat_history):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE sessions
        SET chat_history = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            json.dumps(chat_history),
            session_id
        )
    )

    conn.commit()

    cursor.execute(
        """
        SELECT * FROM sessions
        WHERE id = ?
        """,
        (session_id,)
    )

    updated_session = cursor.fetchone()

    conn.close()

    return updated_session

def get_session_by_id(session_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT * FROM sessions
        WHERE id = ?
        """,
        (session_id,)
    )

    session = cursor.fetchone()

    conn.close()

    return session

def add_message(session_id, role, content):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO messages (
            session_id,
            role,
            content
        )
        VALUES (?, ?, ?)
        """,
        (
            session_id,
            role,
            content
        )
    )

    conn.commit()

    conn.close()

def get_messages_by_session(session_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT role, content
        FROM messages
        WHERE session_id = ?
        ORDER BY created_at ASC
        """,
        (session_id,)
    )

    messages = cursor.fetchall()

    conn.close()

    return messages
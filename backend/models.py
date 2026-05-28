"""
SQLite 持久化：session、版本歷史
"""
import sqlite3
import uuid
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'dashboard.db')


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _get_conn()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            files_meta TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS dashboards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            version INTEGER NOT NULL,
            html TEXT,
            config TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE(session_id, version)
        );
        CREATE TABLE IF NOT EXISTS templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            config TEXT NOT NULL,
            insight_prompt TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
    ''')
    conn.commit()
    conn.close()


def save_version(session_id, html, config=None):
    """儲存戰情表版本，回傳版本號"""
    init_db()
    conn = _get_conn()
    cur = conn.execute(
        'SELECT COALESCE(MAX(version), 0) + 1 as next_ver FROM dashboards WHERE session_id = ?',
        (session_id,)
    )
    next_ver = cur.fetchone()['next_ver']
    conn.execute(
        'INSERT INTO dashboards (session_id, version, html, config) VALUES (?, ?, ?, ?)',
        (session_id, next_ver, html, json.dumps(config or {}, ensure_ascii=False))
    )
    conn.commit()
    conn.close()
    return next_ver


def get_versions(session_id):
    """列出某個 session 的所有版本"""
    init_db()
    conn = _get_conn()
    rows = conn.execute(
        'SELECT version, created_at FROM dashboards WHERE session_id = ? ORDER BY version DESC',
        (session_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_version_html(session_id, version):
    """取得特定版本的 HTML"""
    init_db()
    conn = _get_conn()
    row = conn.execute(
        'SELECT html FROM dashboards WHERE session_id = ? AND version = ?',
        (session_id, int(version))
    ).fetchone()
    conn.close()
    return row['html'] if row else None


def save_template(name, config, insight_prompt=''):
    """儲存用戶自定義模板"""
    init_db()
    conn = _get_conn()
    conn.execute(
        'INSERT INTO templates (name, config, insight_prompt) VALUES (?, ?, ?)',
        (name, json.dumps(config, ensure_ascii=False), insight_prompt)
    )
    conn.commit()
    conn.close()


def list_templates():
    """列出所有模板"""
    init_db()
    conn = _get_conn()
    rows = conn.execute(
        'SELECT id, name, created_at FROM templates ORDER BY created_at DESC'
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_template(template_id):
    """取得單一模板完整內容"""
    init_db()
    conn = _get_conn()
    row = conn.execute(
        'SELECT * FROM templates WHERE id = ?', (template_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None
import datetime
import json
import sqlite3
from typing import Any, Dict, List, Optional

DB_PATH = "finrobot_messages.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS ai_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            script_name TEXT NOT NULL,
            variables TEXT,
            messages TEXT NOT NULL,
            executed_at TEXT NOT NULL
        )
    """
    )
    conn.commit()
    conn.close()


def save_conversation(
    script_name: str,
    variables: Dict[str, Any],
    messages: List[Dict[str, Any]],
    executed_at: Optional[str] = None,
):
    conn = get_connection()
    c = conn.cursor()
    if executed_at is None:
        executed_at = datetime.datetime.now().isoformat()
    c.execute(
        "INSERT INTO ai_messages (script_name, variables, messages, executed_at) VALUES (?, ?, ?, ?)",
        (
            script_name,
            json.dumps(variables, ensure_ascii=False),
            json.dumps(messages, ensure_ascii=False),
            executed_at,
        ),
    )
    conn.commit()
    conn.close()


def get_conversations(limit: int = 20) -> List[Dict[str, Any]]:
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "SELECT id, script_name, variables, messages, executed_at FROM ai_messages ORDER BY executed_at DESC LIMIT ?",
        (limit,),
    )
    rows = c.fetchall()
    conn.close()
    result = []
    for row in rows:
        result.append(
            {
                "id": row[0],
                "script_name": row[1],
                "variables": json.loads(row[2]) if row[2] else {},
                "messages": json.loads(row[3]),
                "executed_at": row[4],
            }
        )
    return result


if __name__ == "__main__":
    init_db()
    # 示例：保存一条对话
    save_conversation(
        script_name="ollama_function_call.py",
        variables={"company": "AAPL"},
        messages=[{"role": "user", "content": "What is the price?"}],
    )
    # 查询
    print(get_conversations())

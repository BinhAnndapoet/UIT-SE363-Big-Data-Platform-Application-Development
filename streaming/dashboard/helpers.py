"""
Helper functions for TikTok Safety Dashboard
"""

import streamlit as st
import pandas as pd
import requests
import re
import subprocess
from sqlalchemy import create_engine, text
from config import (
    DB_CONFIG,
    MINIO_CONF,
    AIRFLOW_API_URL,
    AIRFLOW_AUTH,
    BLACKLIST_KEYWORDS,
    APP_CONFIG,
)


def get_db_engine():
    """Create SQLAlchemy engine for database connection"""
    url = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
    return create_engine(url)


def get_db_connection():
    """Get raw psycopg2-style connection via SQLAlchemy"""
    engine = get_db_engine()
    return engine.connect()


@st.cache_data(ttl=5)
def get_data(limit=None):
    """Fetch processed results from database"""
    try:
        engine = get_db_engine()
        limit_val = limit or APP_CONFIG["max_records"]
        query = f"""
            SELECT video_id, raw_text, human_label, text_verdict, video_verdict, 
                   text_score, video_score, avg_score, final_decision, processed_at 
            FROM processed_results 
            ORDER BY processed_at DESC LIMIT {limit_val};
        """
        df = pd.read_sql(query, engine)
        if not df.empty:
            df["final_decision"] = df["final_decision"].str.lower().str.strip()
            df["processed_at"] = pd.to_datetime(df["processed_at"])
            df["Category"] = df["final_decision"].apply(
                lambda x: "Harmful" if "harmful" in str(x) else "Safe"
            )
        return df
    except Exception as e:
        st.error(f"Database error: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=10)
def get_all_data_paginated(page=1, per_page=12, filter_category=None):
    """Fetch paginated data for gallery view"""
    try:
        engine = get_db_engine()
        offset = (page - 1) * per_page

        where_clause = ""
        if filter_category == "Harmful":
            where_clause = "WHERE LOWER(final_decision) LIKE '%harmful%'"
        elif filter_category == "Safe":
            where_clause = "WHERE LOWER(final_decision) NOT LIKE '%harmful%'"

        # Get total count
        count_query = f"SELECT COUNT(*) FROM processed_results {where_clause};"
        total = pd.read_sql(count_query, engine).iloc[0, 0]

        # Get paginated data
        query = f"""
            SELECT video_id, raw_text, human_label, text_verdict, video_verdict, 
                   text_score, video_score, avg_score, final_decision, processed_at 
            FROM processed_results 
            {where_clause}
            ORDER BY processed_at DESC 
            LIMIT {per_page} OFFSET {offset};
        """
        df = pd.read_sql(query, engine)
        if not df.empty:
            df["final_decision"] = df["final_decision"].str.lower().str.strip()
            df["processed_at"] = pd.to_datetime(df["processed_at"])
            df["Category"] = df["final_decision"].apply(
                lambda x: "Harmful" if "harmful" in str(x) else "Safe"
            )
        return df, total
    except Exception as e:
        return pd.DataFrame(), 0


def get_recent_logs(limit=50):
    """Get recent logs from system_logs table"""
    try:
        engine = get_db_engine()
        query = f"""
            SELECT timestamp, level, component, message 
            FROM system_logs 
            ORDER BY timestamp DESC LIMIT {limit};
        """
        df = pd.read_sql(query, engine)
        return df
    except:
        return pd.DataFrame()


def get_dag_status(dag_id):
    """Get DAG status from Airflow API"""
    try:
        url = f"{AIRFLOW_API_URL}/{dag_id}/dagRuns?limit=1&order_by=-execution_date"
        res = requests.get(url, auth=AIRFLOW_AUTH, timeout=5)
        if res.status_code == 200 and res.json()["dag_runs"]:
            return res.json()["dag_runs"][0]["state"]
        return "unknown"
    except:
        return "error"


def trigger_dag(dag_id):
    """Trigger Airflow DAG (also unpauses it first)"""
    try:
        # First unpause the DAG
        unpause_url = f"{AIRFLOW_API_URL}/{dag_id}"
        requests.patch(
            unpause_url, json={"is_paused": False}, auth=AIRFLOW_AUTH, timeout=5
        )

        # Then trigger it
        url = f"{AIRFLOW_API_URL}/{dag_id}/dagRuns"
        response = requests.post(url, json={"conf": {}}, auth=AIRFLOW_AUTH, timeout=10)
        return response.status_code == 200
    except:
        return False


def clear_queued_dag_runs(dag_id):
    """Clear all queued DAG runs"""
    try:
        # Get all queued runs
        url = f"{AIRFLOW_API_URL}/{dag_id}/dagRuns?state=queued"
        res = requests.get(url, auth=AIRFLOW_AUTH, timeout=5)
        if res.status_code == 200:
            runs = res.json().get("dag_runs", [])
            deleted = 0
            for run in runs:
                run_id = run.get("dag_run_id")
                if run_id:
                    # Delete the queued run
                    del_url = f"{AIRFLOW_API_URL}/{dag_id}/dagRuns/{run_id}"
                    del_res = requests.delete(del_url, auth=AIRFLOW_AUTH, timeout=5)
                    if del_res.status_code in [200, 204]:
                        deleted += 1
            return deleted
        return 0
    except:
        return -1


def get_dag_info(dag_id):
    """Get DAG info including paused status"""
    try:
        url = f"{AIRFLOW_API_URL}/{dag_id}"
        res = requests.get(url, auth=AIRFLOW_AUTH, timeout=5)
        if res.status_code == 200:
            data = res.json()
            return {
                "is_paused": data.get("is_paused", True),
                "is_active": data.get("is_active", False),
            }
        return {"is_paused": True, "is_active": False}
    except:
        return {"is_paused": True, "is_active": False}


def get_dag_run_history(dag_id, limit=10):
    """Get DAG run history with details"""
    try:
        url = (
            f"{AIRFLOW_API_URL}/{dag_id}/dagRuns?limit={limit}&order_by=-execution_date"
        )
        res = requests.get(url, auth=AIRFLOW_AUTH, timeout=5)
        if res.status_code == 200:
            runs = res.json().get("dag_runs", [])
            return [
                {
                    "dag_run_id": r.get("dag_run_id", ""),
                    "state": r.get("state", "unknown"),
                    "execution_date": r.get("execution_date", ""),
                    "start_date": r.get("start_date", ""),
                    "end_date": r.get("end_date", ""),
                }
                for r in runs
            ]
        return []
    except:
        return []


def get_task_instances(dag_id, dag_run_id):
    """Get task instances for a specific DAG run"""
    try:
        url = f"{AIRFLOW_API_URL}/{dag_id}/dagRuns/{dag_run_id}/taskInstances"
        res = requests.get(url, auth=AIRFLOW_AUTH, timeout=5)
        if res.status_code == 200:
            tasks = res.json().get("task_instances", [])
            return [
                {
                    "task_id": t.get("task_id", ""),
                    "state": t.get("state", "unknown"),
                    "start_date": t.get("start_date", ""),
                    "end_date": t.get("end_date", ""),
                    "duration": t.get("duration", 0),
                    "try_number": t.get("try_number", 1),
                }
                for t in tasks
            ]
        return []
    except:
        return []


def get_task_logs(dag_id, dag_run_id, task_id, try_number=1):
    """Get logs for a specific task instance"""
    try:
        url = f"{AIRFLOW_API_URL}/{dag_id}/dagRuns/{dag_run_id}/taskInstances/{task_id}/logs/{try_number}"
        res = requests.get(url, auth=AIRFLOW_AUTH, timeout=10)
        if res.status_code == 200:
            # Fix UTF-8 encoding for Vietnamese characters
            try:
                return res.content.decode("utf-8")
            except:
                return res.text
        return f"Không thể lấy logs (HTTP {res.status_code})"
    except Exception as e:
        return f"Lỗi kết nối: {str(e)}"


def pause_dag(dag_id, is_paused=True):
    """Pause or unpause a DAG"""
    try:
        url = f"{AIRFLOW_API_URL}/{dag_id}"
        res = requests.patch(
            url, auth=AIRFLOW_AUTH, json={"is_paused": is_paused}, timeout=5
        )
        return res.status_code == 200
    except:
        return False


def mark_dag_run_state(dag_id, dag_run_id, state):
    """Mark a DAG run as success or failed"""
    try:
        url = f"{AIRFLOW_API_URL}/{dag_id}/dagRuns/{dag_run_id}"
        res = requests.patch(url, auth=AIRFLOW_AUTH, json={"state": state}, timeout=5)
        return res.status_code == 200
    except:
        return False


def mark_task_state(dag_id, dag_run_id, task_id, state):
    """Mark a task instance as success, failed, or skipped"""
    try:
        url = f"{AIRFLOW_API_URL}/{dag_id}/dagRuns/{dag_run_id}/taskInstances/{task_id}"
        res = requests.patch(
            url, auth=AIRFLOW_AUTH, json={"new_state": state}, timeout=5
        )
        return res.status_code == 200
    except:
        return False


def infer_streaming_engine_state(processed_df, active_window_seconds=180):
    """Infer AI engine state from processed_results data"""
    if (
        processed_df is None
        or processed_df.empty
        or "processed_at" not in processed_df.columns
    ):
        return {
            "state": "waiting",
            "label": "🕒 WAITING",
            "hint": "Chưa có dữ liệu. Hãy chạy DAG Ingestion để đẩy dữ liệu vào Kafka.",
            "last_processed_at": None,
        }

    try:
        last_ts = pd.to_datetime(processed_df["processed_at"]).max()
    except:
        last_ts = None

    if last_ts is None or pd.isna(last_ts):
        return {
            "state": "waiting",
            "label": "🕒 WAITING",
            "hint": "Không parse được timestamp.",
            "last_processed_at": None,
        }

    age_sec = (
        pd.Timestamp.utcnow().tz_localize(None) - last_ts.to_pydatetime()
    ).total_seconds()

    if age_sec <= active_window_seconds:
        return {
            "state": "active",
            "label": "🔥 ACTIVE",
            "hint": f"Output mới cách đây ~{int(age_sec)}s.",
            "last_processed_at": last_ts,
        }

    return {
        "state": "idle",
        "label": "💤 STANDBY",
        "hint": f"Output gần nhất cách đây ~{int(age_sec)}s.",
        "last_processed_at": last_ts,
    }


def get_video_url(vid_id, label):
    """Generate video URL from MinIO"""
    clean_label = str(label).lower().strip()
    if "harm" in clean_label:
        clean_label = "harmful"
    elif "safe" in clean_label:
        clean_label = "safe"
    else:
        clean_label = "unknown"
    return f"{MINIO_CONF['public_endpoint']}/{MINIO_CONF['bucket']}/raw/{clean_label}/{vid_id}.mp4"


def find_blacklist_hits(text, max_hits=8):
    """Find blacklist keyword matches in text"""
    if not text:
        return []
    tl = str(text).lower()
    hits = []
    for kw in BLACKLIST_KEYWORDS:
        if kw in tl:
            hits.append(kw)
            if len(hits) >= max_hits:
                break
    return hits


def highlight_keywords(text, keywords):
    """Highlight keywords in text with markdown bold"""
    if not text:
        return ""
    out = str(text)
    for kw in sorted(set(keywords), key=len, reverse=True):
        try:
            out = re.sub(
                re.escape(kw),
                lambda m: f"**{m.group(0)}**",
                out,
                flags=re.IGNORECASE,
            )
        except:
            pass
    return out


def render_header(title, subtitle, icon="🛡️"):
    """Render standard header component"""
    st.markdown(
        f"""
        <div class="header-container">
            <div class="header-title">
                <span>{icon}</span> {title}
            </div>
            <div class="header-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_help_panel(title, content):
    """Render help panel component"""
    st.markdown(
        f"""
        <div class="help-panel">
            <h4>💡 {title}</h4>
            <p>{content}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_container_logs(container_name, lines=50):
    """Get Docker container logs"""
    try:
        result = subprocess.run(
            ["docker", "logs", "--tail", str(lines), container_name],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.stdout + result.stderr
    except:
        return ""


def get_database_tables():
    """Get list of tables in database"""
    try:
        engine = get_db_engine()
        query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """
        df = pd.read_sql(query, engine)
        return df["table_name"].tolist() if not df.empty else []
    except:
        return []


def get_table_info(table_name):
    """Get column info for a table"""
    try:
        engine = get_db_engine()
        query = f"""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = '{table_name}'
            ORDER BY ordinal_position;
        """
        return pd.read_sql(query, engine)
    except:
        return pd.DataFrame()


def execute_query(query):
    """Execute a custom SQL query"""
    try:
        engine = get_db_engine()
        if query.strip().upper().startswith("SELECT"):
            return pd.read_sql(query, engine), None
        else:
            with engine.connect() as conn:
                conn.execute(text(query))
                conn.commit()
            return None, "Query executed successfully"
    except Exception as e:
        return None, str(e)


def get_system_stats():
    """Get system statistics"""
    stats = {}
    try:
        engine = get_db_engine()

        # Total processed
        stats["total_processed"] = pd.read_sql(
            "SELECT COUNT(*) FROM processed_results", engine
        ).iloc[0, 0]

        # By category
        category_df = pd.read_sql(
            "SELECT final_decision, COUNT(*) as count FROM processed_results GROUP BY final_decision",
            engine,
        )
        stats["by_category"] = category_df

        # Recent activity
        stats["recent_1h"] = pd.read_sql(
            "SELECT COUNT(*) FROM processed_results WHERE processed_at > NOW() - INTERVAL '1 hour'",
            engine,
        ).iloc[0, 0]

        stats["recent_24h"] = pd.read_sql(
            "SELECT COUNT(*) FROM processed_results WHERE processed_at > NOW() - INTERVAL '24 hours'",
            engine,
        ).iloc[0, 0]

    except:
        pass

    return stats

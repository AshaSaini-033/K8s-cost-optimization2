import json
import os
import psycopg2

def get_connection():
    return psycopg2.connect(host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "self_healing"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"))

def init_db():
    # Incident history save karne ke liye simple audit table.
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("""CREATE TABLE IF NOT EXISTS incidents (
          id SERIAL PRIMARY KEY, timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
          namespace TEXT, resource_name TEXT, problem TEXT,
          agent_recommendation JSONB, ai_recommendation JSONB,
          risk_level TEXT, human_approval BOOLEAN,
          action_taken TEXT, verification_status TEXT)""")
        conn.commit()

def log_incident(data):
    # AI suggestion aur actual action dono audit trail mein save hote hain.
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("""INSERT INTO incidents
          (namespace,resource_name,problem,agent_recommendation,ai_recommendation,
           risk_level,human_approval,action_taken,verification_status)
          VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
          (data.get("namespace"), data.get("resource_name"), data.get("problem"),
           json.dumps(data.get("agent_recommendation", [])),
           json.dumps(data.get("ai_recommendation", {})), data.get("risk_level"),
           data.get("human_approval", False), data.get("action_taken"),
           data.get("verification_status")))
        conn.commit()

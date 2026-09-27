import json
import os
import mysql.connector


def get_connection():
    # MySQL connection ke liye environment variables use kar rahe hain.
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        database=os.getenv("MYSQL_DATABASE", "self_healing"),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", "mysql")
    )


def init_db():
    # Incident history save karne ke liye simple audit table.
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id INT AUTO_INCREMENT PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            namespace VARCHAR(255),
            resource_name VARCHAR(255),
            problem TEXT,
            agent_recommendation JSON,
            ai_recommendation JSON,
            risk_level VARCHAR(50),
            human_approval BOOLEAN,
            action_taken TEXT,
            verification_status VARCHAR(100)
        )
    """)
    conn.commit()
    cur.close()
    conn.close()


def log_incident(data):
    # AI suggestion aur actual action dono audit trail mein save hote hain.
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO incidents
        (namespace, resource_name, problem, agent_recommendation,
         ai_recommendation, risk_level, human_approval,
         action_taken, verification_status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        data.get("namespace"),
        data.get("resource_name"),
        data.get("problem"),
        json.dumps(data.get("agent_recommendation", [])),
        json.dumps(data.get("ai_recommendation", {})),
        data.get("risk_level"),
        data.get("human_approval", False),
        data.get("action_taken"),
        data.get("verification_status")
    ))
    conn.commit()
    cur.close()
    conn.close()

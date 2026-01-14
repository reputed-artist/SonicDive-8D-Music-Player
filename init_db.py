import sqlite3

DB_FILE = "message.db"

conn = sqlite3.connect(DB_FILE)
cur = conn.cursor()

# Create messages table if it doesn't exist
cur.execute("""
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    mobile TEXT NOT NULL,
    created TEXT NOT NULL
)
""")

# Optional: insert some demo data
cur.execute("INSERT INTO messages (name, email, mobile, created) VALUES (?, ?, ?, date('now'))",
            ("John Doe", "johndoe@example.com", "+91-9999999999"))
cur.execute("INSERT INTO messages (name, email, mobile, created) VALUES (?, ?, ?, date('now'))",
            ("Jane Smith", "jane@example.com", "+91-8888888888"))
cur.execute("INSERT INTO messages (name, email, mobile, created) VALUES (?, ?, ?, date('now'))",
            ("Jane Smith", "jane@example.com", "+91-8888888888"))
cur.execute("INSERT INTO messages (name, email, mobile, created) VALUES (?, ?, ?, date('now'))",
            ("Jane Smith", "jane@example.com", "+91-8888888888"))
cur.execute("INSERT INTO messages (name, email, mobile, created) VALUES (?, ?, ?, date('now'))",
            ("Jane Smith", "jane@example.com", "+91-8888888888"))
                        
conn.commit()
conn.close()

print("Database and messages table created successfully!")

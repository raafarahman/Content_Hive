import sqlite3
conn=sqlite3.connect("ContentInfo.db")
cursor=conn.cursor()

cursor.execute(
"""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE,
    password TEXT,
    profile_pic TEXT,
    interests TEXT,
    two_factor_enabled INTEGER DEFAULT 0,
    two_factor_secret TEXT
)
"""
)
cursor.execute(
"""
CREATE TABLE IF NOT EXISTS users_info (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    phone TEXT,
    card_number TEXT,
    expiry TEXT
)
"""
    
)










#cursor.execute(
#   """
#       CREATE TABLE feedback(
#           Fullname VARCHAR(255) NOT NULL,
#          Email   VARCHAR(255) NOT NULL,
#          Reason  TEXT,
#          Budget INT,
#         Message TEXT
#          )
#""")
#cursor.execute(
#"""
#DROP TABLE nodes 

#"""
#)     

cursor.execute("""
CREATE TABLE IF NOT EXISTS notes (
   id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    content TEXT,
    tags TEXT,
   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""
)


#conn.execute("""
#CREATE TABLE IF NOT EXISTS pdf(
#    id INTEGER PRIMARY KEY AUTOINCREMENT,
#    user_id INTEGER NOT NULL,
#   title TEXT,
#    category TEXT,
#   notes TEXT,
#   filename TEXT,
#   FOREIGN KEY(user_id) REFERENCES users(id)
#)
#""")

#conn.execute(
    
#    """   ALTER TABLE users ADD COLUMN profile_pic TEXT; ALTER TABLE users ADD COLUMN name TEXT;
#  """ 
#)
conn.execute(
"""
CREATE TABLE IF NOT EXISTS content (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,

    title TEXT NOT NULL,
    category TEXT,

    type TEXT CHECK(type IN ('pdf','video','link','notes')),

    file TEXT,
    link TEXT,
    notes TEXT,

    schedule_date DATE,
    schedule_time TIME,

    status TEXT DEFAULT 'active',

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
"""
)











conn.commit()
conn.close()
print("Database Connection successfully")
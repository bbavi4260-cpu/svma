import sqlite3

def setup_database():
    conn = sqlite3.connect('accounts.db')
    cursor = conn.cursor()
    
    # 1. Players Table Creation
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            account_id INTEGER PRIMARY KEY,
            open_id TEXT UNIQUE NOT NULL,
            nickname TEXT NOT NULL,
            level INTEGER DEFAULT 60,
            exp INTEGER DEFAULT 99999,
            gold INTEGER DEFAULT 999999,
            diamonds INTEGER DEFAULT 999999,
            avatar_id INTEGER DEFAULT 1,
            gender INTEGER DEFAULT 1,
            character_id INTEGER DEFAULT 101,
            access_token TEXT NOT NULL
        )
    ''')
    
    # 2. Insert Default Master Account (If not exists)
    cursor.execute('''
        INSERT OR IGNORE INTO players 
        (account_id, open_id, nickname, level, exp, gold, diamonds, avatar_id, gender, character_id, access_token)
        VALUES 
        (100000001, 'GUEST_100000001', 'Master', 60, 99999, 999999, 999999, 1, 1, 101, 'GUEST_TOKEN_1785865047')
    ''')
    
    conn.commit()
    conn.close()
    print("[DB SUCCESS] accounts.db initialized with default Master player profile!")

if __name__ == "__main__":
    setup_database()
  

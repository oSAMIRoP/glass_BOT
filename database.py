import sqlite3

def init_db():
    conn = sqlite3.connect('creator_pro.db')
    cursor = conn.cursor()
    # جدول تنظیمات کانال
    cursor.execute('''CREATE TABLE IF NOT EXISTS settings 
                      (user_id INTEGER PRIMARY KEY, channel_id TEXT, main_link TEXT)''')
    # جدول پست‌ها
    cursor.execute('''CREATE TABLE IF NOT EXISTS posts 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, text TEXT, 
                       link TEXT, photo_id TEXT, btn_text TEXT, btn2_text TEXT)''')
    conn.commit()
    conn.close()

def update_settings(user_id, channel_id=None, main_link=None):
    conn = sqlite3.connect('creator_pro.db')
    cursor = conn.cursor()
    if channel_id:
        cursor.execute('INSERT INTO settings (user_id, channel_id) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET channel_id=?', (user_id, channel_id, channel_id))
    if main_link:
        cursor.execute('INSERT INTO settings (user_id, main_link) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET main_link=?', (user_id, main_link, main_link))
    conn.commit()
    conn.close()

def get_settings(user_id):
    conn = sqlite3.connect('creator_pro.db')
    cursor = conn.cursor()
    cursor.execute('SELECT channel_id, main_link FROM settings WHERE user_id = ?', (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res if res else (None, None)

def save_post(user_id, text, link, photo_id, btn_text, btn2_text):
    conn = sqlite3.connect('creator_pro.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO posts (user_id, text, link, photo_id, btn_text, btn2_text) VALUES (?, ?, ?, ?, ?, ?)', 
                   (user_id, text, link, photo_id, btn_text, btn2_text))
    p_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return p_id

def get_post(post_id):
    conn = sqlite3.connect('creator_pro.db')
    cursor = conn.cursor()
    cursor.execute('SELECT text, link, photo_id, btn_text, btn2_text, user_id FROM posts WHERE id = ?', (post_id,))
    res = cursor.fetchone()
    conn.close()
    return res

def get_history(user_id):
    conn = sqlite3.connect('creator_pro.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, text FROM posts WHERE user_id = ? ORDER BY id DESC LIMIT 10', (user_id,))
    res = cursor.fetchall()
    conn.close()
    return res
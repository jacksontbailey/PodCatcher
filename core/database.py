import sqlite3
import os  # Assuming you still use os.path functions  

from core.config import PROJECT_SETTING

class SQLiteDB:

    def __init__(self, db_path="core/audio_downloads.sql") -> None:
        self.db_path = os.path.join(PROJECT_SETTING._base_path, db_path)
        self.conn = None

    def connect(self) -> None:
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)

    def disconnect(self) -> None:
        if self.conn is not None:
            self.conn.commit()
            self.conn.close()
            self.conn = None

    def create_audiobook_table(self) -> None:
        self.connect()
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audiobooks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                series_name TEXT,
                book_number INT,
                url TEXT NOT NULL,
                user TEXT NOT NULL,
                downloaded BOOLEAN NOT NULL DEFAULT 0,  -- Default to not downloaded
                edited BOOLEAN NOT NULL DEFAULT 0  -- Default to not downloaded
            )
        """)
        self.disconnect()

    def add_audiobook(self, title, author, url, user) -> None:
        self.connect()
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO audiobooks (title, author, series_name, book_number, url, user, downloaded, edited) VALUES (?, ?, ?, ?, ?, ?, 0, 0)
        """, (title, author, url, user))
        self.disconnect()

    def add_audiobooks(self, audiobooks) -> None:
        """Inserts multiple audiobook records into the database efficiently.

        Args:
            audiobooks (list): A list of tuples where each tuple represents an audiobook 
                               (title, author, series_name, book_number, url, user, downloaded, edited)
        """
        self.connect()
        cursor = self.conn.cursor()
        cursor.executemany("""
            INSERT INTO audiobooks (title, author, series_name, book_number, url, user, downloaded, edited) VALUES (?, ?, ?, ?, ?, ?, 0, 0)
        """, audiobooks)
        self.disconnect()

    def get_audiobooks(self, column_name, value):  # More flexible parameters
        self.connect()
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, title, author, series_name, book_number, url, user, downloaded, edited 
            FROM audiobooks 
            WHERE {} = ?
        """.format(column_name), (value,)) 
        results = cursor.fetchall()
        self.disconnect()
        return results
    
    def get_last_book_number_in_series(self, series_name):
        self.connect()
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT MAX(book_number)
            FROM audiobooks
            WHERE series_name = (?)
        """, (series_name,))
        result = cursor.fetchone()
        self.disconnect()
        if result and result[0] is not None:
            return result[0]
        else:
            return None

    # - bool_check value can either be 'downloaded' or 'edited'
    def mark_audiobook_bool(self, column_name: str, audiobook_id:int) -> None:
        self.connect()
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE audiobooks SET {} = 1 WHERE id = ?
        """.format(column_name), (audiobook_id,))
        self.disconnect()
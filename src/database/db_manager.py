# search_engine_project/src/database/db_manager.py
import mysql.connector
from mysql.connector import Error
import os
import sys

# Tambahkan path ke folder utils agar config bisa diimpor
# os.path.dirname(__file__) -> src/database
# os.path.join(..., '..') -> src/
# os.path.join(..., '..', 'utils') -> src/utils (ini salah, harusnya ke root utils)
# Perbaikan: harusnya langsung ke utils yang ada di root project
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'utils')))
from config import DB_CONFIG

class DBManager:
    def __init__(self):
        self.connection = None

    def connect(self):
        """Membuat koneksi ke database MySQL."""
        try:
            self.connection = mysql.connector.connect(**DB_CONFIG)
            if self.connection.is_connected():
                print(f"Berhasil terhubung ke database MySQL: {DB_CONFIG['database']}")
                return self.connection
        except Error as e:
            print(f"Error saat mencoba terhubung ke database: {e}")
            return None

    def close_connection(self):
        """Menutup koneksi database."""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("Koneksi database ditutup.")

    def create_tables(self):
        """Membuat tabel pages dan links jika belum ada.
           Catatan: Idealnya ini dijalankan SEKALI di awal melalui setup_database.sql manual."""
        if not self.connection:
            print("Tidak ada koneksi database. Harap panggil .connect() terlebih dahulu.")
            return

        cursor = self.connection.cursor()
        try:
            # Pastikan database yang benar digunakan
            cursor.execute(f"USE {DB_CONFIG['database']}")

            # SQL untuk membuat tabel pages
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pages (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    url VARCHAR(255) UNIQUE NOT NULL,
                    content TEXT,
                    pagerank_score FLOAT DEFAULT 0.0
                )
            """)
            print("Tabel 'pages' dipastikan ada.")

            # SQL untuk membuat tabel links
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS links (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    source_page_id INT NOT NULL,
                    target_page_id INT NOT NULL,
                    FOREIGN KEY (source_page_id) REFERENCES pages(id) ON DELETE CASCADE,
                    FOREIGN KEY (target_page_id) REFERENCES pages(id) ON DELETE CASCADE
                )
            """)
            print("Tabel 'links' dipastikan ada.")
            self.connection.commit()
        except Error as e:
            print(f"Error saat membuat tabel: {e}")
        finally:
            cursor.close()

    def insert_page(self, url, content):
        """
        Menyimpan URL dan konten halaman ke tabel pages.
        Mengembalikan ID halaman jika berhasil, atau ID yang sudah ada jika URL duplikat.
        """
        if not self.connection:
            # print("Tidak ada koneksi database.") # Sering muncul, jadi di-comment
            return None

        cursor = self.connection.cursor()
        try:
            # Cek apakah URL sudah ada
            cursor.execute("SELECT id FROM pages WHERE url = %s", (url,))
            existing_id = cursor.fetchone()
            if existing_id:
                # print(f"URL '{url}' sudah ada dengan ID: {existing_id[0]}") # Sering muncul, jadi di-comment
                return existing_id[0] # Mengembalikan ID yang sudah ada

            # Jika belum ada, masukkan data baru
            sql = "INSERT INTO pages (url, content) VALUES (%s, %s)"
            cursor.execute(sql, (url, content))
            self.connection.commit()
            print(f"Halaman '{url}' berhasil ditambahkan dengan ID: {cursor.lastrowid}")
            return cursor.lastrowid
        except Error as e:
            print(f"Error saat memasukkan halaman '{url}': {e}")
            self.connection.rollback()
            return None
        finally:
            cursor.close()

    def insert_link(self, source_page_id, target_page_id):
        """Menyimpan link antar halaman ke tabel links."""
        if not self.connection:
            # print("Tidak ada koneksi database.") # Sering muncul, jadi di-comment
            return

        cursor = self.connection.cursor()
        try:
            # Cek apakah link sudah ada untuk mencegah duplikasi
            cursor.execute(
                "SELECT id FROM links WHERE source_page_id = %s AND target_page_id = %s",
                (source_page_id, target_page_id)
            )
            if cursor.fetchone():
                # print(f"Link dari ID {source_page_id} ke ID {target_page_id} sudah ada.") # Sering muncul, jadi di-comment
                return

            sql = "INSERT INTO links (source_page_id, target_page_id) VALUES (%s, %s)"
            cursor.execute(sql, (source_page_id, target_page_id))
            self.connection.commit()
            # print(f"Link dari ID {source_page_id} ke ID {target_page_id} berhasil ditambahkan.") # Sering muncul, jadi di-comment
        except Error as e:
            print(f"Error saat memasukkan link dari ID {source_page_id} ke ID {target_page_id}: {e}")
            self.connection.rollback()
        finally:
            cursor.close()

    def get_all_pages(self):
        """Mengambil semua halaman dari tabel pages."""
        if not self.connection:
            # print("Tidak ada koneksi database.") # Sering muncul, jadi di-comment
            return []

        cursor = self.connection.cursor(dictionary=True) # Mengembalikan baris sebagai dictionary
        try:
            cursor.execute("SELECT id, url, content, pagerank_score FROM pages")
            return cursor.fetchall()
        except Error as e:
            print(f"Error saat mengambil semua halaman: {e}")
            return []
        finally:
            cursor.close()

    def get_all_links(self):
        """Mengambil semua link dari tabel links."""
        if not self.connection:
            # print("Tidak ada koneksi database.") # Sering muncul, jadi di-comment
            return []

        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT source_page_id, target_page_id FROM links")
            return cursor.fetchall()
        except Error as e:
            print(f"Error saat mengambil semua link: {e}")
            return []
        finally:
            cursor.close()

    def update_pagerank_score(self, page_id, score):
        """Mengupdate skor PageRank untuk halaman tertentu."""
        if not self.connection:
            # print("Tidak ada koneksi database.") # Sering muncul, jadi di-comment
            return

        cursor = self.connection.cursor()
        try:
            sql = "UPDATE pages SET pagerank_score = %s WHERE id = %s"
            cursor.execute(sql, (score, page_id))
            self.connection.commit()
            # print(f"PageRank untuk ID {page_id} berhasil diupdate menjadi {score:.6f}") # Sering muncul, jadi di-comment
        except Error as e:
            print(f"Error saat mengupdate PageRank untuk ID {page_id}: {e}")
            self.connection.rollback()
        finally:
            cursor.close()

    def search_pages_by_keyword(self, keyword):
        """Mencari halaman berdasarkan kata kunci dalam konten, diurutkan berdasarkan PageRank."""
        if not self.connection:
            # print("Tidak ada koneksi database.") # Sering muncul, jadi di-comment
            return []

        cursor = self.connection.cursor(dictionary=True)
        try:
            # Gunakan LIKE untuk pencarian substring case-insensitive
            sql = "SELECT url, content, pagerank_score FROM pages WHERE content LIKE %s ORDER BY pagerank_score DESC"
            cursor.execute(sql, (f"%{keyword}%",))
            return cursor.fetchall()
        except Error as e:
            print(f"Error saat mencari halaman berdasarkan keyword '{keyword}': {e}")
            return []
        finally:
            cursor.close()

# Blok __main__ ini akan di-comment atau dihapus karena fungsi-fungsi ini akan dipanggil dari main.py atau app.py
# if __name__ == '__main__':
#     db_manager = DBManager()
#     db_manager.connect()
#     db_manager.create_tables()
#     # Tambahkan contoh penggunaan untuk pengujian jika diperlukan
#     db_manager.close_connection()
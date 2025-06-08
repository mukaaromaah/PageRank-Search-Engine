# search_engine_project/src/crawler/simple_crawler.py
import os
import re
import sys

# Tambahkan path ke folder database agar db_manager bisa diimpor
# os.path.dirname(__file__) -> src/crawler
# os.path.join(..., '..') -> src/
# os.path.join(..., '..', 'database') -> src/database
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'database')))
from db_manager import DBManager # Hanya dibutuhkan jika ingin test standalone

def read_pages_from_directory(directory_path):
    """
    Membaca file-file teks dari direktori tertentu,
    mengekstraksi konten dan link keluar.
    """
    pages_data = []
    print(f"Membaca halaman dari direktori: {directory_path}")
    if not os.path.exists(directory_path):
        print(f"Error: Direktori '{directory_path}' tidak ditemukan.")
        return []

    if not os.listdir(directory_path):
        print(f"Warning: Direktori '{directory_path}' kosong. Tidak ada halaman untuk diproses.")
        return []

    for filename in os.listdir(directory_path):
        if filename.endswith(".txt"): # Hanya proses file .txt
            filepath = os.path.join(directory_path, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                # URL adalah nama file itu sendiri
                url = filename
                
                # Ekstrak link keluar
                # Cari baris yang dimulai dengan "Link ke: "
                links_to = []
                # Menggunakan re.IGNORECASE agar tidak case-sensitive untuk "Link ke:"
                link_match = re.search(r"Link ke: (.*)", content, re.IGNORECASE)
                if link_match:
                    # Pisahkan link jika ada beberapa yang dipisahkan koma
                    links_str = link_match.group(1)
                    # split dengan koma dan/atau spasi, lalu filter string kosong
                    for link_name in re.split(r'[, ]+', links_str):
                        if link_name: # pastikan bukan string kosong
                            links_to.append(link_name.strip()) # Hapus spasi ekstra

                pages_data.append({
                    'url': url,
                    'content': content,
                    'links_to': links_to
                })
                print(f"  - Dibaca: '{url}' (dengan {len(links_to)} link)")
            except Exception as e:
                print(f"Error membaca atau memproses file '{filepath}': {e}")
    return pages_data

def populate_database(pages_data, db_manager):
    """
    Mengisi database dengan data halaman dan link.
    Dilakukan dalam dua pass:
    1. Masukkan semua halaman untuk mendapatkan ID.
    2. Masukkan semua link menggunakan ID yang sudah ada.
    """
    url_to_id_map = {}

    print("\n--- Memasukkan Halaman ke Database (Pass 1) ---")
    # Pass 1: Masukkan semua halaman dan bangun peta URL ke ID
    for page in pages_data:
        page_id = db_manager.insert_page(page['url'], page['content'])
        if page_id is not None:
            url_to_id_map[page['url']] = page_id

    print("\n--- Memasukkan Link ke Database (Pass 2) ---")
    # Pass 2: Masukkan semua link
    for page in pages_data:
        source_url = page['url']
        source_id = url_to_id_map.get(source_url) # Ambil ID sumber

        if source_id is None:
            print(f"Warning: ID tidak ditemukan untuk URL sumber: {source_url}. Lewati link-nya.")
            continue

        for target_url in page['links_to']:
            # Pastikan target_url memiliki akhiran .txt jika belum ada
            if not target_url.endswith('.txt'):
                target_url += '.txt' # Asumsi semua link internal mengarah ke file .txt

            target_id = url_to_id_map.get(target_url) # Ambil ID target

            if target_id is None:
                print(f"Warning: ID tidak ditemukan untuk URL target: {target_url} (dari {source_url}). Link diabaikan.")
                continue # Link ke halaman yang tidak ada, abaikan

            db_manager.insert_link(source_id, target_id)

    print("\nProses pengisian database selesai.")

# Blok __main__ ini hanya untuk testing standalone, akan dipanggil dari main.py atau app.py
# if __name__ == '__main__':
#     # Ini adalah path relatif ke folder data/raw_pages dari lokasi script ini
#     current_dir = os.path.dirname(__file__)
#     # Naik dua tingkat ke root proyek, lalu masuk ke data/raw_pages
#     project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
#     data_dir = os.path.join(project_root, 'data', 'raw_pages')

#     # Buat dummy files jika belum ada untuk pengujian
#     if not os.path.exists(data_dir):
#         os.makedirs(data_dir)
#     if not os.listdir(data_dir):
#         print("Direktori data/raw_pages kosong. Membuat file dummy untuk pengujian.")
#         with open(os.path.join(data_dir, 'page1.txt'), 'w', encoding='utf-8') as f:
#             f.write("Konten halaman 1. Ini adalah halaman utama.\nLink ke: page2.txt, page3.txt")
#         with open(os.path.join(data_dir, 'page2.txt'), 'w', encoding='utf-8') as f:
#             f.write("Konten halaman 2. Artikel tentang Python.\nLink ke: page1.txt")
#         with open(os.path.join(data_dir, 'page3.txt'), 'w', encoding='utf-8') as f:
#             f.write("Konten halaman 3. Topik Machine Learning.\nLink ke: page1.txt, page2.txt")
#         print("File dummy telah dibuat di data/raw_pages.")

#     db_manager = DBManager()
#     db_manager.connect()
#     if db_manager.connection:
#         db_manager.create_tables() # Pastikan tabel ada
#         pages_data = read_pages_from_directory(data_dir)
#         populate_database(pages_data, db_manager)
#         db_manager.close_connection()
#     else:
#         print("Tidak dapat melakukan crawling karena koneksi database gagal.")
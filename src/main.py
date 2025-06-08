# search_engine_project/src/main.py
import os
import sys

# Tambahkan path ke folder src agar modul-modul di dalamnya bisa diimpor
# os.path.dirname(__file__) -> src/
# os.path.abspath(os.path.join(os.path.dirname(__file__), 'database')) -> src/database
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'database')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'crawler')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'pagerank')))
# Untuk config.py, path-nya harus ke utils yang ada di root project
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'utils')))


from db_manager import DBManager
from simple_crawler import read_pages_from_directory, populate_database
from pagerank_calculator import calculate_pagerank

def run_indexing_and_pagerank(data_dir):
    """
    Menjalankan proses crawling, pengisian database, dan perhitungan PageRank.
    """
    db_manager = DBManager()
    db_manager.connect()
    if not db_manager.connection:
        print("Gagal terhubung ke database. Proses indexing dibatalkan.")
        return False # Mengindikasikan kegagalan

    try:
        # Catatan: create_tables() di sini untuk memastikan tabel ada saat script dijalankan.
        # Namun, disarankan setup_database.sql dijalankan manual SEKALI di awal.
        db_manager.create_tables()

        print("\n--- Membaca dan Memproses Halaman dari Direktori ---")
        pages_data = read_pages_from_directory(data_dir)
        if not pages_data:
            print("Tidak ada halaman yang ditemukan di direktori data. Pastikan ada file .txt di data/raw_pages/.")
            return False

        print("--- Mengisi Database dengan Halaman dan Link ---")
        populate_database(pages_data, db_manager)

        print("\n--- Menghitung PageRank ---")
        calculate_pagerank(db_manager)

        print("\nProses indexing dan PageRank selesai.")
        return True # Mengindikasikan keberhasilan
    except Exception as e:
        print(f"Terjadi error selama proses indexing/PageRank: {e}")
        return False
    finally:
        db_manager.close_connection()

def search_engine_cli():
    """
    Menyediakan antarmuka Command Line Interface (CLI) untuk pencarian.
    """
    db_manager = DBManager()
    db_manager.connect()
    if not db_manager.connection:
        print("Gagal terhubung ke database. Fungsi pencarian tidak tersedia.")
        return

    print("\n--- Selamat Datang di Search Engine Sederhana ---")
    print("Ketik 'exit' untuk keluar.")

    while True:
        query = input("\nMasukkan kata kunci pencarian: ").strip()
        if query.lower() == 'exit':
            break
        if not query:
            continue

        results = db_manager.search_pages_by_keyword(query)

        if results:
            print(f"\nDitemukan {len(results)} hasil untuk '{query}':")
            for i, result in enumerate(results):
                print(f"  {i+1}. URL: {result['url']}")
                print(f"     PageRank Score: {result['pagerank_score']:.6f}")
                # Tampilkan cuplikan konten (misalnya 100 karakter pertama)
                snippet = result['content'][:100] + ('...' if len(result['content']) > 100 else '')
                print(f"     Konten: {snippet}")
        else:
            print(f"Tidak ada hasil ditemukan untuk '{query}'.")

    db_manager.close_connection()
    print("\nTerima kasih telah menggunakan search engine.")

if __name__ == '__main__':
    # Pastikan jalur ke data/raw_pages sudah benar dari root proyek
    current_dir = os.path.dirname(__file__) # src/
    project_root = os.path.abspath(os.path.join(current_dir, '..')) # search_engine_project/
    data_raw_pages_dir = os.path.join(project_root, 'data', 'raw_pages')

    print("--- Memulai Proses Indexing dan Perhitungan PageRank ---")
    indexing_successful = run_indexing_and_pagerank(data_raw_pages_dir)

    if indexing_successful:
        print("\n--- Memulai Antarmuka Pencarian ---")
        search_engine_cli()
    else:
        print("\nProses indexing gagal, tidak dapat memulai pencarian CLI.")
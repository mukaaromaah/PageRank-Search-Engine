# search_engine_project/src/web/app.py
from flask import Flask, render_template, request
import os
import sys

# Tambahkan path ke folder src agar modul-modul di dalamnya bisa diimpor
# os.path.dirname(__file__) -> src/web
# os.path.join(..., '..') -> src/
# os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'database')) -> search_engine_project/src/database
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'database')))
# Tambahkan path ke folder utils agar config bisa diimpor
# os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'utils')) -> search_engine_project/utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'utils')))


from db_manager import DBManager # Import DBManager yang sudah kita buat

# Konfigurasi Flask agar tahu di mana mencari template dan file statis
app = Flask(__name__,
            template_folder=os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'templates')),
            static_folder=os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'static')))

@app.route('/')
def index():
    """
    Rute untuk halaman utama (form pencarian).
    """
    return render_template('index.html')

@app.route('/search', methods=['GET'])
def search():
    """
    Rute untuk memproses permintaan pencarian.
    Mengambil kata kunci dari query parameter 'q', melakukan pencarian,
    dan menampilkan hasilnya.
    """
    query = request.args.get('q', '').strip()
    results = []
    
    db_manager = DBManager()
    db_manager.connect() # Buka koneksi database

    if db_manager.connection:
        if query:
            # Panggil fungsi pencarian dari DBManager
            results = db_manager.search_pages_by_keyword(query)
        else:
            print("Pencarian kosong.") # Pesan jika query kosong
    else:
        print("Error: Gagal terhubung ke database untuk pencarian.")
    
    db_manager.close_connection() # Tutup koneksi database
    
    return render_template('results.html', query=query, results=results)

@app.route('/page/<filename>')
def show_page_content(filename):
    """
    Rute untuk menampilkan konten lengkap dari sebuah halaman simulasi (.txt).
    Parameter <filename> akan diambil dari URL.
    """
    # Path ke folder data/raw_pages/ dari root proyek
    current_dir = os.path.dirname(__file__) # src/web
    project_root = os.path.abspath(os.path.join(current_dir, '..', '..')) # search_engine_project/
    data_raw_pages_dir = os.path.join(project_root, 'data', 'raw_pages')
    
    filepath = os.path.join(data_raw_pages_dir, filename)
    
    # Periksa apakah file ada dan memiliki ekstensi .txt untuk keamanan
    if os.path.exists(filepath) and os.path.isfile(filepath) and filename.endswith('.txt'):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            # Render template baru untuk menampilkan konten
            return render_template('page_viewer.html', filename=filename, content=content)
        except Exception as e:
            # Jika ada error saat membaca file
            print(f"Error reading file {filename}: {e}")
            return "Error: Tidak dapat membaca konten halaman.", 500
    else:
        # Jika file tidak ditemukan atau bukan file .txt
        print(f"Akses tidak valid: File '{filename}' tidak ditemukan atau tidak diizinkan.")
        return "Halaman tidak ditemukan.", 404

if __name__ == '__main__':
    # Untuk menjalankan aplikasi web Flask
    # Pastikan kamu sudah menjalankan src/main.py SETIDAKNYA SEKALI
    # untuk mengisi database dengan data dan PageRank score.
    print("-----------------------------------------------------")
    print("             Memulai Aplikasi Web Search Engine      ")
    print("-----------------------------------------------------")
    print("Pastikan database sudah terisi (jalankan src/main.py terlebih dahulu!)")
    print(f"Aplikasi Flask akan berjalan di: http://127.0.0.1:5000/")
    print("Tekan CTRL+C untuk menghentikan server.")
    print("-----------------------------------------------------")
    app.run(debug=True) # debug=True akan memberikan pesan error lebih detail
                        # dan otomatis me-reload server saat ada perubahan kode

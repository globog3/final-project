# PANDUAN SLIDE PRESENTASI
## Final Project: Simple LMS Extended Backend

Gunakan draf materi presentasi ini untuk membuat slide (PowerPoint/Canva) atau jadikan panduan langsung saat menjelaskan arsitektur dan fitur kepada dosen penguji.

---

### **Slide 1: Halaman Judul & Identitas**
* **Judul Slide**: Pengembangan Backend Simple LMS Teraugmentasi (Extended Backend)
* **Sub-judul**: Implementasi Django Ninja, Database PostgreSQL, Caching Redis, dan Sistem Otorisasi RBAC
* **Identitas**: 
  * Nama: Adi Priyo
  * NIM: [Lengkapi NIM Anda]
  * Mata Kuliah: Pemrograman Sisi Server (A11.54403)
  * Universitas Dian Nuswantoro

---

### **Slide 2: Arsitektur & Desain Sistem**
* **Poin Utama**: Struktur backend dirancang modular dengan pemisahan berkas yang tegas sesuai standar *clean code*.
* **Komponen Arsitektur**:
  * **Framework**: Django 4.2+ dengan **Django Ninja** untuk kecepatan respons REST API (tipe data tervalidasi menggunakan Pydantic).
  * **Database**: PostgreSQL di dalam Docker untuk data relasional utama.
  * **Caching Layer**: Redis untuk optimasi performa list course.
  * **Authentication**: JWT Bearer token untuk otorisasi *stateless*.
* **Visualisasi Arsitektur**:
  ```
  Client (Swagger/Postman/UI) ---> Django Ninja Router ---> Service/Logic ---> PostgreSQL
                                             |
                                             v
                                        Redis Cache
  ```

---

### **Slide 3: Pembuktian Fondasi Wajib (Nilai: 30 Poin)**
* **Kriteria Penilaian**:
  * [x] **Docker Compose**: Service web, db, dan redis terisolasi secara rapi.
  * [x] **Database PostgreSQL**: Migrasi otomatis berjalan dengan aman.
  * [x] **Authentication JWT**: Mekanisme login & bearer token valid.
  * [x] **Role-Based Access Control (RBAC)**: Validasi peran `admin`, `instructor`, dan `student`.
  * [x] **Swagger & OpenAPI**: Akses dokumentasi API interaktif pada `/api/docs`.
  * [x] **Non-hardcoded Settings**: Konfigurasi sensitif aman menggunakan file `.env`.

---

### **Slide 4: Fitur Tambahan Terpilih (Nilai: 46 Poin dari Target 45-60)**
Jelaskan 4 fitur tambahan ringan yang diintegrasikan secara penuh:
1. **Permission & Ownership Ketat (12 Poin)**:
   * Pengamanan hak akses. Siswa tidak bisa melihat detail modul sebelum mendaftar course. Instruktur hanya bisa memodifikasi course buatannya sendiri.
2. **Search, Filter, & Sorting Lanjutan + Redis Cache (12 Poin)**:
   * Pencarian fleksibel, filter kategori, pengurutan terpopuler & rating tertinggi. Hasil pencarian disimpan di Redis Cache dan di-invalidasi otomatis saat data berubah.
3. **Rating, Review, & Wishlist (12 Poin)**:
   * Memberi penilaian bintang (1-5), komentar ulasan, dan menyimpan course favorit ke dalam *wishlist*.
4. **Course Announcement (10 Poin)**:
   * Papan pengumuman satu arah khusus bagi siswa yang terdaftar di course terkait.

---

### **Slide 5: Demonstrasi UI Dashboard & Postman (Bonus +5 Poin)**
* **Poin Utama**: Selain REST API, proyek ini dilengkapi antarmuka frontend web Single Page Application (SPA) sederhana pada `index.html`.
* **Kelebihan UI**:
  * Tampilan responsif dan estetis (*Outfit Font*, *Clean Layout*).
  * Menampilkan hak akses dinamis. Jika login sebagai **Admin/Instructor**, tombol edit/hapus dan tambah course akan muncul. Jika login sebagai **Student**, tombol tersebut disembunyikan.
  * Dilengkapi **Postman Collection** (`LMS_Postman_Collection.json`) untuk kemudahan pengujian.

---

### **Slide 6: Kualitas Kode & Unit Testing (Nilai: 10 Poin)**
* **Kriteria Penilaian Kualitas Kode (15 Poin)**:
  * Pemisahan logika terstruktur antara `models.py` (definisi database), `schemas.py` (validasi Pydantic), `auth.py` (keamanan JWT), dan `api.py` (routing).
  * Struktur basis kode aman dari SQL Injection berkat Django ORM.
* **Hasil Pengujian Otomatis (Testing - 10 Poin)**:
  * Pengujian menyeluruh menggunakan Django Test Runner (`python manage.py test lms`).
  * Menguji registrasi/login, penghitungan progress belajar, otorisasi review, dan hak akses pengumuman.
  * Hasil: **4/4 Tes Berhasil Lulus (OK)**.

---

### **Slide 7: Kesimpulan & Tanya Jawab**
* **Kesimpulan**:
  * Django Ninja sangat mempercepat pengembangan backend berkat auto-documentation dan validasi skema otomatis.
  * Implementasi caching Redis terbukti meningkatkan skalabilitas sistem saat melayani permintaan berulang.
  * Batasan otorisasi yang ketat menjamin keamanan hak cipta materi pengajar di dalam sistem LMS.
* **Sesi**: Tanya Jawab (Q&A).

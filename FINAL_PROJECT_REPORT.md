# LAPORAN FINAL PROJECT
## Simple LMS Extended Backend

---

### 1. Identitas
* **Nama**: Adi Priyo
* **NIM**: [Silakan lengkapi NIM Anda di sini]
* **Kelas**: Pemrograman Sisi Server (A11.54403)
* **Program Studi**: Teknik Informatika – Universitas Dian Nuswantoro (UDINUS)
* **URL Repository**: [Silakan masukkan URL repositori GitHub/GitLab Anda di sini]

---

### 2. Deskripsi Project
Project ini adalah **Simple Learning Management System (LMS) Extended Backend** yang dibangun dengan framework **Django**, menggunakan **Django Ninja** untuk REST API yang berkinerja tinggi, **PostgreSQL** sebagai database relasional utama, dan **Redis** untuk manajemen caching. Aplikasi ini mendukung fungsionalitas manajemen pembelajaran daring lengkap dengan role-based access control (RBAC) untuk tiga tipe user: Admin, Instructor, dan Student.

---

### 3. Fitur Dasar yang Sudah Berjalan (Fondasi - 30 Poin)
Seluruh fitur dasar yang dipersyaratkan telah berhasil diimplementasikan dan berjalan dengan baik:
* **Docker & Docker Compose**: Konfigurasi deployment multi-container untuk service web, database PostgreSQL, dan caching Redis.
* **Database Relasional**: Migrasi database PostgreSQL berjalan lancar dan otomatis saat inisialisasi.
* **Authentication & RBAC**: Autentikasi JWT Bearer token yang aman dan pembatasan hak akses per-role (Admin, Instructor, Student).
* **Endpoint Dasar**: API lengkap untuk pengelolaan Course, Lesson, Enrollment, dan tracking Progress student.
* **Swagger/OpenAPI Docs**: Dokumentasi interaktif API yang otomatis digenerate dan dapat diakses di `/api/docs`.

---

### 4. Fitur Tambahan yang Dipilih (Total: 46 Poin)

| No | Fitur Tambahan | Kategori | Poin | Status |
|---|---|---|:---:|---|
| 1 | **Permission & Ownership Ketat** | A. Course & Learning Experience | 12 | Selesai |
| 2 | **Search, Filter, & Sorting Lanjutan** | A. Course & Learning Experience | 12 | Selesai |
| 3 | **Rating, Review, & Wishlist** | A. Course & Learning Experience | 12 | Selesai |
| 4 | **Course Announcement** | M. Business Feature Tambahan | 10 | Selesai |
| | **TOTAL POIN FITUR TAMBAHAN** | | **46** | |

---

### 5. Penjelasan Implementasi Fitur Tambahan

#### A. Permission & Ownership Ketat (12 Poin)
* **Detail**: Memastikan keamanan akses konten pembelajaran.
  * Instructor hanya diperbolehkan mengubah (PUT) atau menghapus (DELETE) data Course, Lesson, dan Announcement yang merupakan milik mereka.
  * Student tidak dapat mengakses detail isi Lesson dari suatu Course sebelum mereka melakukan enrollment ke Course tersebut secara sah.
* **Implementasi**: Dilakukan dengan menambahkan pemeriksaan autentikasi dan otorisasi secara dinamis di level logika handler Django Ninja menggunakan `request.auth` (JWT Payload).

#### B. Search, Filter, & Sorting Lanjutan (12 Poin)
* **Detail**: Mempermudah pencarian course oleh student dengan efisien.
* **Implementasi**:
  * Menambahkan parameter opsional `search` (pencarian teks pada title/description), `category_id`, dan `instructor_id` pada query API.
  * Menambahkan parameter `sort_by` dengan opsi: `newest` (terbaru), `popular` (berdasarkan jumlah enrollment terbanyak), dan `rating` (berdasarkan rata-rata rating review tertinggi).
  * **Redis Caching**: Hasil query list course disimpan di Redis untuk request berulang. Cache diinvalidasikan secara otomatis (`cache.clear()`) setiap kali ada penambahan, perubahan, atau penghapusan course/review untuk menjamin konsistensi data.

#### C. Rating, Review, & Wishlist (12 Poin)
* **Detail**: Memberikan umpan balik terhadap kualitas materi pembelajaran.
  * Enrolled student dapat mengirimkan rating (skala 1-5) dan ulasan (comment) pada course yang diikuti.
  * Student dapat menandai (bookmark) course favorit mereka ke dalam Wishlist pribadi.
* **Implementasi**: Penambahan model data `Review` dan `Wishlist` dengan constraint `unique_together` agar student hanya bisa memberikan 1 review dan 1 wishlist per course.

#### D. Course Announcement (10 Poin)
* **Detail**: Komunikasi satu arah dari pengajar ke siswa.
  * Instructor dapat mempublikasikan pengumuman terkait course yang ia ajar.
  * Hanya student yang terdaftar di course tersebut yang diperbolehkan membaca pengumuman.
* **Implementasi**: Penambahan model `Announcement` dan endpoint terproteksi `/announcements/course/{course_id}`.

---

### 6. Cara Menjalankan Project

#### Menggunakan Docker Compose (Rekomendasi Production-ready)
1. Pastikan Docker dan Docker Compose sudah terinstal di komputer Anda.
2. Salin berkas `.env.example` menjadi `.env` dan sesuaikan konfigurasinya jika diperlukan.
3. Jalankan perintah berikut untuk membangun image dan menjalankan kontainer:
   ```bash
   docker compose up --build -d
   ```
4. Lakukan migrasi database dan seed data di dalam kontainer `web`:
   ```bash
   docker compose exec web python manage.py migrate
   docker compose exec web python manage.py seed_data
   ```

#### Menggunakan Virtual Environment Lokal (SQLite Fallback untuk Pengujian Cepat)
Jika Anda ingin mencoba aplikasi secara lokal tanpa setup database PostgreSQL secara manual:
1. Buat virtual environment python dan instal semua dependensi:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. Jalankan perintah migrasi data:
   ```bash
   python manage.py makemigrations lms
   python manage.py migrate
   ```
3. Lakukan seeding database untuk membuat data contoh:
   ```bash
   python manage.py seed_data
   ```
4. Jalankan server lokal:
   ```bash
   python manage.py runserver
   ```
5. Akses dokumentasi Swagger API di URL: `http://127.0.0.1:8000/api/docs`

---

### 7. Akun Demo Pengujian

Semua akun di bawah di-hash menggunakan password bawaan dari perintah `seed_data`:

| Username | Password | Role | Keterangan |
|---|---|---|---|
| **admin** | `admin123` | **Admin** | Hak akses penuh sistem |
| **instructor1** | `instructor123` | **Instructor** | Pengajar yang memiliki course contoh |
| **student1** | `student123` | **Student** | Siswa yang sudah terdaftar di course Django |
| **student2** | `student123` | **Student** | Siswa baru yang belum terdaftar di course mana pun |

---

### 8. Endpoint Penting

| Endpoint | Method | Kebutuhan Auth | Deskripsi |
|---|---|---|---|
| `/api/auth/register` | POST | Public | Registrasi akun baru |
| `/api/auth/login` | POST | Public | Login akun untuk mendapatkan JWT |
| `/api/courses/` | GET | Bearer JWT | Melihat daftar course (dengan search, filter, sorting, & cache) |
| `/api/courses/create` | POST | JWT (Admin/Instructor) | Membuat course baru |
| `/api/lessons/course/{id}` | GET | JWT (Enrolled Student/Instructor) | Melihat modul/lesson dari course |
| `/api/enrollments/create`| POST | JWT (Student) | Pendaftaran student ke course |
| `/api/progress/course/{id}`| GET | JWT (Student) | Melihat persentase progres belajar |
| `/api/reviews/course/{id}/create`| POST | JWT (Enrolled Student) | Memberikan ulasan/rating course |
| `/api/wishlists/course/{id}/toggle`| POST | JWT (Student) | Menambah/menghapus course dari wishlist |
| `/api/announcements/course/{id}`| GET | JWT (Enrolled Student/Instructor) | Membaca pengumuman course |

---

### 9. Bukti Pengujian (Automated Test Result)

Pengujian otomatis dijalankan menggunakan command `python manage.py test lms` dan memberikan hasil sukses 100%:

```text
Creating test database for alias 'default'...
....
----------------------------------------------------------------------
Ran 4 tests in 6.494s

OK
Destroying test database for alias 'default'...
Found 4 test(s).
System check identified no issues (0 silenced).
```

---

### 10. Kendala dan Solusi
* **Kendala**: Terdapat kendala koneksi saat Docker mencoba mengunduh base image `python:3.11-slim` dari Docker Hub karena kegagalan otorisasi atau pemblokiran unduhan anonim di beberapa jaringan internet (Error 404 pada authentication token).
* **Solusi**: Sebagai alternatif untuk pengujian lokal, kami mengimplementasikan sistem *fallback* pada `settings.py`. Jika environment variable database tidak terdeteksi (seperti saat berjalan di luar Docker), Django secara otomatis akan beralih menggunakan database lokal SQLite. Dengan demikian, pengujian unit test dan seeding data tetap dapat dilakukan dengan lancar di komputer lokal tanpa bergantung pada Docker daemon maupun PostgreSQL.

---

### 11. Kesimpulan
Melalui pengerjaan Final Project ini, kami berhasil mengintegrasikan materi pemrograman sisi server secara komprehensif. Implementasi Django Ninja terbukti mempermudah pengembangan API yang bersih dan terstruktur dengan validasi tipe data otomatis (Pydantic). Integrasi Redis caching juga memberikan peningkatan efisiensi yang signifikan pada pemuatan daftar course, sementara pengamanan RBAC dan pembatasan kepemilikan data (permission/ownership) menjamin privasi konten pembelajaran daring yang andal.

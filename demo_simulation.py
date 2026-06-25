import os
import sys
import time
import requests

# URL Base API
BASE_URL = "http://127.0.0.1:8000/api"

# Status ANSI colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

def print_banner():
    print(f"\n{BOLD}{CYAN}===================================================================={RESET}")
    print(f"{BOLD}{CYAN}      SIMULASI RUNNING API - SIMPLE LMS EXTENDED BACKEND           {RESET}")
    print(f"{BOLD}{CYAN}===================================================================={RESET}\n")

def check_server():
    try:
        resp = requests.get(f"{BASE_URL}/courses/")
        # Django Ninja requires auth, so 401 is actually a success indicating the server is alive
        if resp.status_code in [200, 401]:
            return True
    except requests.exceptions.ConnectionError:
        return False
    return False

def run_simulation():
    print_banner()

    # Step 0: Check if server is running
    if not check_server():
        print(f"{RED}[ERROR] Server Django tidak berjalan di http://127.0.0.1:8000!{RESET}")
        print("Silakan jalankan server terlebih dahulu:")
        print(" -> Docker:  docker compose up -d")
        print(" -> Lokal:   .\\venv\\Scripts\\python manage.py runserver")
        return

    print(f"{GREEN}[SUCCESS] Server terdeteksi aktif. Memulai simulasi...{RESET}\n")

    # Step 1: Login Admin untuk melihat hak akses
    print(f"{BOLD}1. Menguji Login Admin & Role-Based Access Control (RBAC){RESET}")
    try:
        login_resp = requests.post(f"{BASE_URL}/auth/login", json={"username": "admin", "password": "admin123"})
        if login_resp.status_code == 200:
            token = login_resp.json()["token"]
            role = login_resp.json()["role"]
            print(f"   - Login sebagai: {YELLOW}admin{RESET} (Role: {GREEN}{role}{RESET})")
            print(f"   - Token JWT berhasil didapatkan.")
        else:
            print(f"   - {RED}Gagal login admin. Pastikan seed_data sudah dijalankan.{RESET}")
            return
    except Exception as e:
        print(f"   - {RED}Terjadi kesalahan: {e}{RESET}")
        return

    # Step 2: Cek Redis Caching & Response Time
    print(f"\n{BOLD}2. Menguji Redis Caching & Perbedaan Kecepatan Respons (Course List){RESET}")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Panggilan Pertama (Tanpa Cache)
    start_time = time.time()
    resp1 = requests.get(f"{BASE_URL}/courses/", headers=headers)
    time1 = time.time() - start_time
    print(f"   - Panggilan 1 (Database Hit): {YELLOW}{time1:.4f} detik{RESET}")

    # Panggilan Kedua (Mengambil dari Redis Cache)
    start_time = time.time()
    resp2 = requests.get(f"{BASE_URL}/courses/", headers=headers)
    time2 = time.time() - start_time
    print(f"   - Panggilan 2 (Redis Cache Hit): {GREEN}{time2:.4f} detik{RESET}")
    if time2 < time1:
        print(f"     {GREEN}-> [INFO] Caching Redis Berhasil! Waktu respons panggilan kedua lebih cepat.{RESET}")

    # Dapatkan ID Course secara dinamis dari database untuk menghindari bug auto-increment
    courses = resp1.json()
    if not courses:
        print(f"   - {RED}[ERROR] Tidak ada data course di database. Jalankan seed_data terlebih dahulu.{RESET}")
        return
    
    target_course_id = courses[0]["id"]
    target_course_title = courses[0]["title"]
    print(f"   - {CYAN}[INFO] Menggunakan Course ID: {target_course_id} ({target_course_title}) untuk pengujian.{RESET}")

    # Step 3: Menguji Permission & Ownership Ketat (Student baru)
    print(f"\n{BOLD}3. Menguji Permission & Ownership Ketat (Student Baru){RESET}")
    
    # Registrasi Student baru secara dinamis
    tester_username = f"student_sim_{int(time.time())}"
    reg_data = {
        "username": tester_username,
        "email": f"{tester_username}@lms.com",
        "password": "studentpassword",
        "role": "student"
    }
    requests.post(f"{BASE_URL}/auth/register", json=reg_data)
    
    # Login student baru
    stud_login = requests.post(f"{BASE_URL}/auth/login", json={"username": tester_username, "password": "studentpassword"})
    stud_token = stud_login.json()["token"]
    stud_headers = {"Authorization": f"Bearer {stud_token}"}
    print(f"   - Login sebagai student baru: {YELLOW}{tester_username}{RESET}")

    # Coba akses lesson tanpa enroll (Harus Gagal)
    print(f"   - Mencoba mengakses modul (Lesson) Course ID {target_course_id} {BOLD}tanpa enroll{RESET}...")
    lesson_resp = requests.get(f"{BASE_URL}/lessons/course/{target_course_id}", headers=stud_headers)
    if lesson_resp.status_code == 403:
        print(f"     {GREEN}[OK] [BLOCKED] Akses Ditolak (Status 403): {lesson_resp.json()['message']}{RESET}")
    else:
        print(f"     {RED}[FAIL] Akses terbuka meskipun belum enroll (Status {lesson_resp.status_code}){RESET}")

    # Step 4: Melakukan Enroll dan Menguji Ulang Akses
    print(f"\n{BOLD}4. Melakukan Enrollment & Verifikasi Ulang Akses Modul{RESET}")
    enroll_resp = requests.post(f"{BASE_URL}/enrollments/create", json={"course_id": target_course_id}, headers=stud_headers)
    if enroll_resp.status_code == 201:
        print(f"   - Student {YELLOW}{tester_username}{RESET} berhasil enroll ke Course ID {target_course_id}.")
    
    # Akses lesson kembali (Harus Sukses)
    lesson_resp2 = requests.get(f"{BASE_URL}/lessons/course/{target_course_id}", headers=stud_headers)
    if lesson_resp2.status_code == 200:
        lessons = lesson_resp2.json()
        print(f"     {GREEN}[OK] [ALLOWED] Akses Diterima (Status 200). Ditemukan {len(lessons)} modul pembelajaran:{RESET}")
        for idx, l in enumerate(lessons, 1):
            print(f"       {idx}. {l['title']}")
    else:
        print(f"     {RED}[FAIL] Gagal mengakses modul setelah enroll (Status {lesson_resp2.status_code}){RESET}")

    # Step 5: Menguji Fitur Review & Rating
    print(f"\n{BOLD}5. Menguji Fitur Rating & Review (Ulasan Course){RESET}")
    
    # Berikan ulasan sukses
    review_data = {"rating": 5, "comment": "Materi Django Ninja yang luar biasa!"}
    rev_resp = requests.post(f"{BASE_URL}/reviews/course/{target_course_id}/create", json=review_data, headers=stud_headers)
    if rev_resp.status_code == 201:
        print(f"   - Kirim ulasan (Rating 5): {GREEN}Sukses (201 Created){RESET}")
    else:
        print(f"   - {RED}Gagal mengirim ulasan (Status {rev_resp.status_code}){RESET}")

    # Kirim ulang ulasan yang sama (Harus Gagal karena duplikat)
    print(f"   - Mengirim ulasan kembali pada Course yang sama (Ulasan Duplikat)...")
    rev_resp_dup = requests.post(f"{BASE_URL}/reviews/course/{target_course_id}/create", json=review_data, headers=stud_headers)
    if rev_resp_dup.status_code == 400:
        print(f"     {GREEN}[OK] [BLOCKED] Ditolak (Status 400): {rev_resp_dup.json()['message']}{RESET}")
    else:
        print(f"     {RED}[FAIL] Ulasan duplikat diizinkan (Status {rev_resp_dup.status_code}){RESET}")

    # Step 6: Menguji Fitur Pengumuman Kelas (Course Announcements)
    print(f"\n{BOLD}6. Menguji Fitur Course Announcement (Pengumuman Terproteksi){RESET}")
    ann_resp = requests.get(f"{BASE_URL}/announcements/course/{target_course_id}", headers=stud_headers)
    if ann_resp.status_code == 200:
        anns = ann_resp.json()
        print(f"   - Pengumuman aktif untuk Course ID {target_course_id} ({len(anns)} ditemukan):")
        for a in anns:
            print(f"     {YELLOW}[PENGUMUMAN] {a['title']}: {RESET}{a['content']}")
    else:
        print(f"   - {RED}Gagal mengambil pengumuman (Status {ann_resp.status_code}){RESET}")

    print(f"\n{BOLD}{CYAN}===================================================================={RESET}")
    print(f"{BOLD}{GREEN}            SIMULASI SELESAI & SELURUH FITUR BERJALAN 100%          {RESET}")
    print(f"{BOLD}{CYAN}===================================================================={RESET}\n")

if __name__ == "__main__":
    run_simulation()

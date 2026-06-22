from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from lms.models import Category, Course, Lesson, Enrollment, Progress, Review, Wishlist, Announcement

User = get_user_model()

class Command(BaseCommand):
    help = "Seed database dengan data contoh (demo data) untuk pengujian Simple LMS"

    def handle(self, *args, **options):
        self.stdout.write("Menghapus data lama...")
        Progress.objects.all().delete()
        Enrollment.objects.all().delete()
        Lesson.objects.all().delete()
        Review.objects.all().delete()
        Wishlist.objects.all().delete()
        Announcement.objects.all().delete()
        Course.objects.all().delete()
        Category.objects.all().delete()
        User.objects.all().delete()

        self.stdout.write("Membuat user demo...")
        admin = User.objects.create(
            username="admin",
            email="admin@lms.com",
            password=make_password("admin123"),
            role="admin",
            is_staff=True,
            is_superuser=True
        )
        instructor = User.objects.create(
            username="instructor1",
            email="instructor1@lms.com",
            password=make_password("instructor123"),
            role="instructor"
        )
        student1 = User.objects.create(
            username="student1",
            email="student1@lms.com",
            password=make_password("student123"),
            role="student"
        )
        student2 = User.objects.create(
            username="student2",
            email="student2@lms.com",
            password=make_password("student123"),
            role="student"
        )

        self.stdout.write("Membuat kategori...")
        web_dev = Category.objects.create(name="Web Development", description="Mempelajari pemrograman web dari frontend hingga backend")
        data_science = Category.objects.create(name="Data Science", description="Analisis data, machine learning, dan visualisasi data")

        self.stdout.write("Membuat course...")
        course1 = Course.objects.create(
            title="Belajar Django Ninja dari Nol",
            description="Course backend modern menggunakan Django Ninja yang cepat dan mudah dipelajari.",
            category=web_dev,
            instructor=instructor
        )
        course2 = Course.objects.create(
            title="Analisis Data dengan Python",
            description="Pelajari pustaka Pandas, Numpy, dan Matplotlib untuk analisis data profesional.",
            category=data_science,
            instructor=instructor
        )

        self.stdout.write("Membuat lesson...")
        # Lessons untuk course 1
        l1 = Lesson.objects.create(
            course=course1,
            title="Pengenalan Django Ninja",
            content="Django Ninja adalah framework web modern untuk membuat API dengan Python dan Pydantic.",
            order=1
        )
        l2 = Lesson.objects.create(
            course=course1,
            title="Membuat Models dan Database",
            content="Belajar cara mendefinisikan Django Models dan melakukan migrasi database.",
            order=2
        )
        l3 = Lesson.objects.create(
            course=course1,
            title="Autentikasi JWT",
            content="Implementasi JWT Bearer token untuk pengamanan API endpoints.",
            order=3
        )

        # Lessons untuk course 2
        Lesson.objects.create(
            course=course2,
            title="Pengenalan Pandas DataFrame",
            content="Pandas DataFrame adalah struktur data 2 dimensi berlabel dengan kolom bertipe data variatif.",
            order=1
        )

        self.stdout.write("Membuat enrollment untuk student1...")
        enroll = Enrollment.objects.create(student=student1, course=course1)

        self.stdout.write("Membuat progress pembelajaran student1...")
        Progress.objects.create(student=student1, lesson=l1, is_completed=True)
        Progress.objects.create(student=student1, lesson=l2, is_completed=False)

        self.stdout.write("Membuat review & wishlist...")
        Review.objects.create(student=student1, course=course1, rating=5, comment="Sangat bagus dan mudah dipahami!")
        Wishlist.objects.create(student=student1, course=course2)

        self.stdout.write("Membuat pengumuman course...")
        Announcement.objects.create(
            course=course1,
            title="Jadwal Live Q&A",
            content="Sesi tanya jawab langsung akan diadakan hari Jumat pukul 19:00 WIB via Zoom."
        )

        self.stdout.write(self.style.SUCCESS("Database seeding berhasil diselesaikan!"))

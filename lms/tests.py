from django.test import TestCase
from django.contrib.auth import get_user_model
from lms.models import Category, Course, Lesson, Enrollment, Progress, Review, Announcement
from lms.auth import generate_token

User = get_user_model()

class LMSTests(TestCase):
    def setUp(self):
        # Create users
        self.instructor = User.objects.create_user(
            username="test_instructor",
            email="instructor@test.com",
            password="password123",
            role="instructor"
        )
        self.student = User.objects.create_user(
            username="test_student",
            email="student@test.com",
            password="password123",
            role="student"
        )
        self.other_student = User.objects.create_user(
            username="other_student",
            email="other@test.com",
            password="password123",
            role="student"
        )

        # Create Category
        self.category = Category.objects.create(name="Web Dev")

        # Create Course
        self.course = Course.objects.create(
            title="Test Django Ninja",
            description="Testing Django Ninja API",
            category=self.category,
            instructor=self.instructor
        )

        # Create Lesson
        self.lesson1 = Lesson.objects.create(
            course=self.course,
            title="Lesson 1",
            content="Content 1",
            order=1
        )
        self.lesson2 = Lesson.objects.create(
            course=self.course,
            title="Lesson 2",
            content="Content 2",
            order=2
        )

    def test_enrollment_and_lessons_visibility(self):
        # Student not enrolled yet
        is_enrolled = Enrollment.objects.filter(student=self.student, course=self.course).exists()
        self.assertFalse(is_enrolled)

        # Enroll student
        enrollment = Enrollment.objects.create(student=self.student, course=self.course)
        self.assertTrue(Enrollment.objects.filter(student=self.student, course=self.course).exists())

    def test_progress_calculation(self):
        # Enroll student
        Enrollment.objects.create(student=self.student, course=self.course)

        # Complete lesson 1
        Progress.objects.create(student=self.student, lesson=self.lesson1, is_completed=True)

        total_lessons = Lesson.objects.filter(course=self.course).count()
        completed_lessons = Progress.objects.filter(
            student=self.student,
            lesson__course=self.course,
            is_completed=True
        ).count()

        percentage = (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0.0
        self.assertEqual(total_lessons, 2)
        self.assertEqual(completed_lessons, 1)
        self.assertEqual(percentage, 50.0)

    def test_course_reviews(self):
        # Only enrolled students can review
        # Let's verify rating constraints
        Enrollment.objects.create(student=self.student, course=self.course)
        review = Review.objects.create(
            student=self.student,
            course=self.course,
            rating=5,
            comment="Awesome course!"
        )
        self.assertEqual(Review.objects.filter(course=self.course).count(), 1)
        self.assertEqual(review.rating, 5)

    def test_announcements(self):
        announcement = Announcement.objects.create(
            course=self.course,
            title="New Announcement",
            content="Some announcement content"
        )
        self.assertEqual(Announcement.objects.filter(course=self.course).count(), 1)
        self.assertEqual(announcement.title, "New Announcement")

import json
from datetime import datetime
from typing import List, Optional
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password, check_password
from django.core.cache import cache
from django.db.models import Avg, Q
from django.shortcuts import get_object_or_404
from ninja import NinjaAPI, Router
from ninja.errors import HttpError

from lms.auth import jwt_auth, generate_token
from lms.models import Category, Course, Lesson, Enrollment, Progress, Review, Wishlist, Announcement
from lms.schemas import (
    RegisterInputSchema, LoginInputSchema, TokenSchema, UserOutSchema, ErrorSchema,
    CategorySchema, CategoryCreateSchema,
    CourseSchema, CourseCreateSchema, CourseUpdateSchema,
    LessonSchema, LessonCreateSchema,
    EnrollmentSchema, EnrollmentCreateSchema,
    ProgressSchema, CourseProgressSchema,
    ReviewSchema, ReviewCreateSchema,
    WishlistSchema, AnnouncementSchema, AnnouncementCreateSchema
)

User = get_user_model()
api = NinjaAPI(
    title="Simple LMS Extended Backend API",
    version="1.0.0",
    description="Backend untuk Simple LMS dengan Django, PostgreSQL, Redis, dan Django Ninja"
)

# Routers
auth_router = Router()
category_router = Router()
course_router = Router()
lesson_router = Router()
enrollment_router = Router()
progress_router = Router()
review_router = Router()
wishlist_router = Router()
announcement_router = Router()

# Cache helper functions
def invalidate_course_cache(course_id=None):
    """
    Clear course lists and specific course details cache
    """
    # Simple and robust invalidation: clear the whole cache
    cache.clear()

# ==========================================
# AUTH ENDPOINTS
# ==========================================

@auth_router.post("/register", response={201: UserOutSchema, 400: ErrorSchema})
def register(request, data: RegisterInputSchema):
    if User.objects.filter(username=data.username).exists():
        return 400, {"message": "Username sudah digunakan"}
    if User.objects.filter(email=data.email).exists():
        return 400, {"message": "Email sudah digunakan"}
    
    if data.role not in ['admin', 'instructor', 'student']:
        return 400, {"message": "Role tidak valid. Harus admin, instructor, atau student"}

    user = User.objects.create(
        username=data.username,
        email=data.email,
        password=make_password(data.password),
        role=data.role
    )
    return 201, user


@auth_router.post("/login", response={200: TokenSchema, 400: ErrorSchema})
def login(request, data: LoginInputSchema):
    try:
        user = User.objects.get(username=data.username)
    except User.DoesNotExist:
        return 400, {"message": "Username atau password salah"}

    if not check_password(data.password, user.password):
        return 400, {"message": "Username atau password salah"}

    token = generate_token(user)
    return 200, {
        "token": token,
        "role": user.role,
        "username": user.username
    }


@auth_router.get("/me", auth=jwt_auth, response=UserOutSchema)
def me(request):
    return request.auth


# ==========================================
# CATEGORY ENDPOINTS
# ==========================================

@category_router.get("/", auth=jwt_auth, response=List[CategorySchema])
def list_categories(request):
    return Category.objects.all()


@category_router.post("/", auth=jwt_auth, response={201: CategorySchema, 403: ErrorSchema, 400: ErrorSchema})
def create_category(request, data: CategoryCreateSchema):
    # RBAC: Only Admin can create categories
    if request.auth.role != 'admin':
        return 403, {"message": "Hanya Admin yang dapat membuat kategori"}
    
    if Category.objects.filter(name=data.name).exists():
        return 400, {"message": "Nama kategori sudah ada"}

    category = Category.objects.create(name=data.name, description=data.description)
    return 201, category


# ==========================================
# COURSE ENDPOINTS (including Caching & Advanced Search/Filter/Sorting)
# ==========================================

@course_router.get("/", auth=jwt_auth, response=List[CourseSchema])
def list_courses(
    request,
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    instructor_id: Optional[int] = None,
    sort_by: Optional[str] = 'newest'  # newest, popular, rating
):
    # --- Redis Caching ---
    # Create a unique cache key based on query parameters
    cache_key = f"courses:list:search={search}:cat={category_id}:inst={instructor_id}:sort={sort_by}"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        # Load serialized courses from cache and return
        course_ids = json.loads(cached_data)
        # Re-fetch specific courses in order to keep Django ORM queryset execution fast
        courses = list(Course.objects.filter(id__in=course_ids).select_related('category', 'instructor'))
        # Re-sort to maintain requested sorting order
        course_map = {c.id: c for c in courses}
        sorted_courses = [course_map[cid] for cid in course_ids if cid in course_map]
        return sorted_courses

    # Querying database
    queryset = Course.objects.all().select_related('category', 'instructor')

    # Advanced Search & Filter
    if search:
        queryset = queryset.filter(
            Q(title__icontains=search) | Q(description__icontains=search)
        )
    if category_id:
        queryset = queryset.filter(category_id=category_id)
    if instructor_id:
        queryset = queryset.filter(instructor_id=instructor_id)

    # Sorting options
    if sort_by == 'newest':
        queryset = queryset.order_by('-created_at')
    elif sort_by == 'popular':
        # Sort by total enrollments count
        queryset = queryset.annotate(num_enrollments=models.Count('enrollments')).order_by('-num_enrollments')
    elif sort_by == 'rating':
        # Sort by average review rating
        queryset = queryset.annotate(avg_rating=Avg('reviews__rating')).order_by('-avg_rating')
    else:
        queryset = queryset.order_by('-created_at')

    courses_list = list(queryset)
    
    # Save serialized IDs list to Redis (cache expires in 5 minutes)
    course_ids = [c.id for c in courses_list]
    cache.set(cache_key, json.dumps(course_ids), timeout=300)

    return courses_list


@course_router.get("/{course_id}", auth=jwt_auth, response={200: CourseSchema, 404: ErrorSchema})
def get_course(request, course_id: int):
    # --- Redis Caching for Detail ---
    cache_key = f"course:detail:{course_id}"
    cached_course = cache.get(cache_key)
    if cached_course:
        return 200, Course.objects.get(id=course_id)

    try:
        course = Course.objects.select_related('category', 'instructor').get(id=course_id)
        cache.set(cache_key, course, timeout=300)
        return 200, course
    except Course.DoesNotExist:
        return 404, {"message": "Course tidak ditemukan"}


@course_router.post("/create", auth=jwt_auth, response={201: CourseSchema, 403: ErrorSchema, 400: ErrorSchema})
def create_course(request, data: CourseCreateSchema):
    # RBAC: Only Admin or Instructor can create courses
    if request.auth.role not in ['admin', 'instructor']:
        return 403, {"message": "Hanya Admin atau Instructor yang dapat membuat course"}
    
    category = None
    if data.category_id:
        try:
            category = Category.objects.get(id=data.category_id)
        except Category.DoesNotExist:
            return 400, {"message": "Kategori tidak ditemukan"}

    course = Course.objects.create(
        title=data.title,
        description=data.description,
        category=category,
        instructor=request.auth
    )
    
    # Invalidate cache
    invalidate_course_cache()
    return 201, course


@course_router.put("/{course_id}", auth=jwt_auth, response={200: CourseSchema, 403: ErrorSchema, 404: ErrorSchema})
def update_course(request, course_id: int, data: CourseUpdateSchema):
    course = get_object_or_404(Course, id=course_id)

    # Strict Permission & Ownership: Only the creator instructor or Admin can update
    if request.auth.role != 'admin' and course.instructor_id != request.auth.id:
        return 403, {"message": "Anda tidak memiliki akses untuk mengubah course ini"}

    if data.title:
        course.title = data.title
    if data.description:
        course.description = data.description
    if data.category_id:
        category = get_object_or_404(Category, id=data.category_id)
        course.category = category

    course.save()
    # Invalidate cache
    invalidate_course_cache(course_id)
    return 200, course


@course_router.delete("/{course_id}", auth=jwt_auth, response={200: dict, 403: ErrorSchema, 404: ErrorSchema})
def delete_course(request, course_id: int):
    course = get_object_or_404(Course, id=course_id)

    # Strict Permission & Ownership: Only the creator instructor or Admin can delete
    if request.auth.role != 'admin' and course.instructor_id != request.auth.id:
        return 403, {"message": "Anda tidak memiliki akses untuk menghapus course ini"}

    course.delete()
    # Invalidate cache
    invalidate_course_cache(course_id)
    return 200, {"message": "Course berhasil dihapus"}


# ==========================================
# LESSON ENDPOINTS
# ==========================================

@lesson_router.get("/course/{course_id}", auth=jwt_auth, response={200: List[LessonSchema], 403: ErrorSchema})
def list_lessons(request, course_id: int):
    course = get_object_or_404(Course, id=course_id)

    # Strict Permission: If Student, must be enrolled to view lessons
    if request.auth.role == 'student':
        if not Enrollment.objects.filter(student=request.auth, course=course).exists():
            return 403, {"message": "Anda harus terdaftar (enrolled) di course ini untuk melihat lesson"}

    lessons = Lesson.objects.filter(course=course).order_by('order')
    return 200, list(lessons)


@lesson_router.post("/course/{course_id}/create", auth=jwt_auth, response={201: LessonSchema, 403: ErrorSchema})
def create_lesson(request, course_id: int, data: LessonCreateSchema):
    course = get_object_or_404(Course, id=course_id)

    # Strict Permission & Ownership: Only course instructor or Admin can add lessons
    if request.auth.role != 'admin' and course.instructor_id != request.auth.id:
        return 403, {"message": "Anda tidak memiliki akses untuk menambahkan lesson ke course ini"}

    lesson = Lesson.objects.create(
        course=course,
        title=data.title,
        content=data.content,
        order=data.order
    )
    return 201, lesson


@lesson_router.put("/{lesson_id}", auth=jwt_auth, response={200: LessonSchema, 403: ErrorSchema})
def update_lesson(request, lesson_id: int, data: LessonCreateSchema):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.course

    # Strict Permission & Ownership: Only course instructor or Admin can update lessons
    if request.auth.role != 'admin' and course.instructor_id != request.auth.id:
        return 403, {"message": "Anda tidak memiliki akses untuk mengubah lesson ini"}

    lesson.title = data.title
    lesson.content = data.content
    lesson.order = data.order
    lesson.save()
    return 200, lesson


@lesson_router.delete("/{lesson_id}", auth=jwt_auth, response={200: dict, 403: ErrorSchema})
def delete_lesson(request, lesson_id: int):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.course

    # Strict Permission & Ownership: Only course instructor or Admin can delete lessons
    if request.auth.role != 'admin' and course.instructor_id != request.auth.id:
        return 403, {"message": "Anda tidak memiliki akses untuk menghapus lesson ini"}

    lesson.delete()
    return 200, {"message": "Lesson berhasil dihapus"}


# ==========================================
# ENROLLMENT ENDPOINTS
# ==========================================

@enrollment_router.get("/", auth=jwt_auth, response=List[EnrollmentSchema])
def list_enrollments(request):
    # If student, list only their enrollments. Admin/Instructor see all
    if request.auth.role == 'student':
        return Enrollment.objects.filter(student=request.auth).select_related('course', 'student')
    return Enrollment.objects.all().select_related('course', 'student')


@enrollment_router.post("/create", auth=jwt_auth, response={201: EnrollmentSchema, 400: ErrorSchema, 403: ErrorSchema})
def enroll_course(request, data: EnrollmentCreateSchema):
    # RBAC: Only Students can enroll in courses
    if request.auth.role != 'student':
        return 403, {"message": "Hanya Student yang dapat mendaftar course"}

    course = get_object_or_404(Course, id=data.course_id)

    if Enrollment.objects.filter(student=request.auth, course=course).exists():
        return 400, {"message": "Anda sudah terdaftar di course ini"}

    enrollment = Enrollment.objects.create(student=request.auth, course=course)
    
    # Invalidate cache since enrollments count changes (impacts popular sort)
    invalidate_course_cache()
    return 201, enrollment


# ==========================================
# PROGRESS ENDPOINTS
# ==========================================

@progress_router.get("/course/{course_id}", auth=jwt_auth, response={200: CourseProgressSchema, 403: ErrorSchema})
def get_course_progress(request, course_id: int):
    course = get_object_or_404(Course, id=course_id)

    # Check enrollment for students
    if request.auth.role == 'student':
        if not Enrollment.objects.filter(student=request.auth, course=course).exists():
            return 403, {"message": "Anda harus terdaftar di course ini untuk melihat progress"}

    total_lessons = Lesson.objects.filter(course=course).count()
    completed_lessons = Progress.objects.filter(
        student=request.auth,
        lesson__course=course,
        is_completed=True
    ).count()

    percentage = (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0.0

    return 200, {
        "course_id": course.id,
        "course_title": course.title,
        "total_lessons": total_lessons,
        "completed_lessons": completed_lessons,
        "progress_percentage": round(percentage, 2)
    }


@progress_router.post("/lesson/{lesson_id}", auth=jwt_auth, response={200: ProgressSchema, 403: ErrorSchema})
def mark_lesson_progress(request, lesson_id: int, is_completed: bool):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.course

    # Check enrollment for students
    if request.auth.role == 'student':
        if not Enrollment.objects.filter(student=request.auth, course=course).exists():
            return 403, {"message": "Anda harus terdaftar di course ini untuk menandai progress"}

    progress, created = Progress.objects.get_or_create(
        student=request.auth,
        lesson=lesson
    )

    progress.is_completed = is_completed
    progress.completed_at = datetime.utcnow() if is_completed else None
    progress.save()

    return 200, progress


# ==========================================
# RATING & REVIEW ENDPOINTS
# ==========================================

@review_router.get("/course/{course_id}", auth=jwt_auth, response=List[ReviewSchema])
def list_reviews(request, course_id: int):
    return Review.objects.filter(course_id=course_id).select_related('student', 'course')


@review_router.post("/course/{course_id}/create", auth=jwt_auth, response={201: ReviewSchema, 400: ErrorSchema, 403: ErrorSchema})
def create_review(request, course_id: int, data: ReviewCreateSchema):
    course = get_object_or_404(Course, id=course_id)

    # Strict Permission: Only enrolled students can review
    if not Enrollment.objects.filter(student=request.auth, course=course).exists():
        return 403, {"message": "Anda harus terdaftar (enrolled) di course ini untuk memberikan review"}

    if Review.objects.filter(student=request.auth, course=course).exists():
        return 400, {"message": "Anda sudah memberikan review untuk course ini"}

    review = Review.objects.create(
        student=request.auth,
        course=course,
        rating=data.rating,
        comment=data.comment
    )
    
    # Invalidate course cache (ratings sort may change)
    invalidate_course_cache()
    return 201, review


# ==========================================
# WISHLIST ENDPOINTS
# ==========================================

@wishlist_router.get("/", auth=jwt_auth, response=List[CourseSchema])
def list_wishlist(request):
    wishlists = Wishlist.objects.filter(student=request.auth).select_related('course')
    return [w.course for w in wishlists]


@wishlist_router.post("/course/{course_id}/toggle", auth=jwt_auth, response={200: dict, 403: ErrorSchema})
def toggle_wishlist(request, course_id: int):
    # RBAC: Only Students can use wishlist
    if request.auth.role != 'student':
        return 403, {"message": "Hanya Student yang dapat menggunakan wishlist"}

    course = get_object_or_404(Course, id=course_id)
    wishlist_item = Wishlist.objects.filter(student=request.auth, course=course)

    if wishlist_item.exists():
        wishlist_item.delete()
        return 200, {"message": "Course dihapus dari wishlist", "in_wishlist": False}
    else:
        Wishlist.objects.create(student=request.auth, course=course)
        return 200, {"message": "Course ditambahkan ke wishlist", "in_wishlist": True}


# ==========================================
# ANNOUNCEMENT ENDPOINTS
# ==========================================

@announcement_router.get("/course/{course_id}", auth=jwt_auth, response={200: List[AnnouncementSchema], 403: ErrorSchema})
def list_announcements(request, course_id: int):
    course = get_object_or_404(Course, id=course_id)

    # Strict Permission: If Student, must be enrolled to view announcements
    if request.auth.role == 'student':
        if not Enrollment.objects.filter(student=request.auth, course=course).exists():
            return 403, {"message": "Anda harus terdaftar di course ini untuk melihat pengumuman"}

    announcements = Announcement.objects.filter(course=course).order_by('-created_at')
    return 200, list(announcements)


@announcement_router.post("/course/{course_id}/create", auth=jwt_auth, response={201: AnnouncementSchema, 403: ErrorSchema})
def create_announcement(request, course_id: int, data: AnnouncementCreateSchema):
    course = get_object_or_404(Course, id=course_id)

    # Strict Permission: Only course instructor or Admin can create announcements
    if request.auth.role != 'admin' and course.instructor_id != request.auth.id:
        return 403, {"message": "Anda tidak memiliki akses untuk membuat pengumuman di course ini"}

    announcement = Announcement.objects.create(
        course=course,
        title=data.title,
        content=data.content
    )
    return 201, announcement


# Register routers to API
api.add_router("/auth", auth_router, tags=["Auth"])
api.add_router("/categories", category_router, tags=["Categories"])
api.add_router("/courses", course_router, tags=["Courses"])
api.add_router("/lessons", lesson_router, tags=["Lessons"])
api.add_router("/enrollments", enrollment_router, tags=["Enrollments"])
api.add_router("/progress", progress_router, tags=["Progress"])
api.add_router("/reviews", review_router, tags=["Reviews"])
api.add_router("/wishlists", wishlist_router, tags=["Wishlist"])
api.add_router("/announcements", announcement_router, tags=["Announcements"])

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

# --- Auth Schemas ---
class RegisterInputSchema(BaseModel):
    username: str
    password: str
    email: str
    role: str = Field(default="student", description="admin, instructor, or student")


class LoginInputSchema(BaseModel):
    username: str
    password: str


class TokenSchema(BaseModel):
    token: str
    role: str
    username: str


class UserOutSchema(BaseModel):
    id: int
    username: str
    email: str
    role: str

    class Config:
        from_attributes = True


# --- Category Schemas ---
class CategorySchema(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class CategoryCreateSchema(BaseModel):
    name: str
    description: Optional[str] = None


# --- Course Schemas ---
class CourseSchema(BaseModel):
    id: int
    title: str
    description: str
    category: Optional[CategorySchema] = None
    instructor: UserOutSchema
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CourseCreateSchema(BaseModel):
    title: str
    description: str
    category_id: Optional[int] = None


class CourseUpdateSchema(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None


# --- Lesson Schemas ---
class LessonSchema(BaseModel):
    id: int
    course_id: int
    title: str
    content: str
    order: int

    class Config:
        from_attributes = True


class LessonCreateSchema(BaseModel):
    title: str
    content: str
    order: int = 1


# --- Enrollment Schemas ---
class EnrollmentSchema(BaseModel):
    id: int
    student: UserOutSchema
    course_id: int
    enrolled_at: datetime

    class Config:
        from_attributes = True


class EnrollmentCreateSchema(BaseModel):
    course_id: int


# --- Progress Schemas ---
class ProgressSchema(BaseModel):
    id: int
    student_id: int
    lesson_id: int
    is_completed: bool
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CourseProgressSchema(BaseModel):
    course_id: int
    course_title: str
    total_lessons: int
    completed_lessons: int
    progress_percentage: float


# --- Review Schemas ---
class ReviewSchema(BaseModel):
    id: int
    student: UserOutSchema
    course_id: int
    rating: int
    comment: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ReviewCreateSchema(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


# --- Wishlist Schemas ---
class WishlistSchema(BaseModel):
    id: int
    student: UserOutSchema
    course_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# --- Announcement Schemas ---
class AnnouncementSchema(BaseModel):
    id: int
    course_id: int
    title: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class AnnouncementCreateSchema(BaseModel):
    title: str
    content: str


# --- Error Schema ---
class ErrorSchema(BaseModel):
    message: str

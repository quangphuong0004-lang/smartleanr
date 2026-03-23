from django.db import models
from django.conf import settings
import uuid
import random, string

User = settings.AUTH_USER_MODEL

#Tạo mã tham gia khóa học với 8 ký tự ngẫu nhiên
def generate_join_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))


#Khóa học
class Course(models.Model):
    LEVEL_CHOICE = [
        ('basic', 'Cơ bản'),
        ('intermediate', 'Trung bình'),
        ('advanced', 'Nâng cao')
    ]
    STATUS_CHOICES = [
        ('public', 'Công khai'),
        ('private', 'Riêng tư'),
        ('pending', 'Chờ duyệt'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    thumbnail = models.ImageField(upload_to='courses/thumbnails/', null=True, blank=True)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses_taught', limit_choices_to={'role': 'teacher'},)
    subject = models.CharField(max_length=100, blank=True, )
    level = models.CharField(max_length=20, choices=LEVEL_CHOICE, default='basic')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='public')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    join_code = models.CharField(max_length=8, unique=True, default=generate_join_code, editable=False)
    
    class Meta:
        db_table = 'courses'
        ordering = ['-created_at']
        verbose_name = 'Khóa học'
        verbose_name_plural = 'Khóa học'
        
    def __str__(self):
        return self.title

    @property
    def student_count(self):
        return self.enrollments.filter(status='approved').count()
    
    @property
    def lesson_count(self):
        return self.lessons.count()
    
    def get_thumbnail_url(self):
        if self.thumbnail:
            return self.thumbnail.url
        return None
    

#Đăng ký khóa học
class Enrollment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'chờ duyệt'),
        ('approved', 'đã duyệt'),
        ('rejected', 'từ chối')
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='approved')
    enrolled_at = models.DateField(auto_now_add=True)
    
    class Meta:
        db_table = 'enrollments'
        unique_together = ('student', 'course') #Mỗi học sinh chỉ đăng ký 1 khóa học
        verbose_name = 'Đăng ký học'
        verbose_name_plural = 'Đăng ký học'
        
    def __str__(self):
        return f"{self.student.username} -> {self.course.title}"
    

#Bài học
class Lesson(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True)
    video_url = models.URLField(blank=True)
    order_index = models.PositiveIntegerField(default=0)
    is_locked = models.BooleanField(default=False)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)
    
    class Meta:
        db_table = 'lesson'
        ordering = ['order_index']
        verbose_name = 'Bài học'
        verbose_name_plural = 'Bài học'
        
    def __str__(self):
        return f"[{self.course.title}] {self.title}"
    

#Tiến độ bài học
class LessonProgress(models.Model):
    STATUS_CHOICES = [
        ('not_started', 'Chưa học'),
        ('in_progress', 'Đang học'),
        ('complete', 'Hoàn thành')
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='progress')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    complete_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'lesson_progress'
        unique_together = ('student', 'lesson')
        verbose_name = 'Tiến độ bài học'
        verbose_name_plural = 'Tiến độ bài học'
        
    def __str__(self):
        return f"{self.student.username} - {self.lesson.title} ({self.status})"
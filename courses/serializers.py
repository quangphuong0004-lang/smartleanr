from rest_framework import serializers
from .models import Course, Lesson, LessonProgress, Enrollment
from django.conf import settings

class TeacherSerializer(serializers.Serializer):
    id         = serializers.UUIDField()
    username   = serializers.CharField()
    full_name  = serializers.CharField()
    avatar_url = serializers.SerializerMethodField()
 
    def get_avatar_url(self, obj):
        request = self.context.get('request')
        if obj.avatar:
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Lesson
        fields = [
            'id', 'course', 'title', 'content',
            'video_url', 'order_index', 'is_locked',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
 
    def validate_course(self, value): #Chỉ teacher sở hữu khóa học mới được tạo bài học
        request = self.context.get('request')
        if request and value.teacher != request.user:
            raise serializers.ValidationError("Bạn không có quyền thêm bài học cho khóa học này.")
        return value


class LessonListSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Lesson
        fields = ['id', 'title', 'video_url', 'order_index', 'is_locked', 'created_at']
        read_only_fields = ['id', 'created_at']
        

class LessonProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model  = LessonProgress
        fields = ['id', 'lesson', 'status', 'completed_at']
        read_only_fields = ['id', 'completed_at']
        

class CourseSerializer(serializers.ModelSerializer):
    teacher       = TeacherSerializer(read_only=True)
    student_count = serializers.IntegerField(read_only=True)
    lesson_count  = serializers.IntegerField(read_only=True)
    thumbnail_url = serializers.SerializerMethodField()
    is_enrolled   = serializers.SerializerMethodField()
    progress_pct  = serializers.SerializerMethodField()
 
    class Meta:
        model  = Course
        fields = [
            'id', 'title', 'description', 'thumbnail', 'thumbnail_url',
            'teacher', 'subject', 'level', 'status',
            'student_count', 'lesson_count',
            'is_enrolled', 'progress_pct',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'teacher', 'created_at', 'updated_at']
 
    def get_thumbnail_url(self, obj):
        request = self.context.get('request')
        if obj.thumbnail:
            if request:
                return request.build_absolute_uri(obj.thumbnail.url)
            return obj.thumbnail.url
        return None
 
    def get_is_enrolled(self, obj): #Học sinh đã đăng ký khóa học này chưa
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.enrollments.filter(
            student=request.user, status='approved'
        ).exists()
 
    def get_progress_pct(self, obj):  #Tính % tiến độ học của student hiện tại
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return 0
        total = obj.lessons.count()
        if total == 0:
            return 0
        completed = LessonProgress.objects.filter(
            student=request.user,
            lesson__course=obj,
            status='completed',
        ).count()
        return round(completed / total * 100)
    

class CourseCreateSerializer(serializers.ModelSerializer): # Khi teacher tạo/sửa khóa học
    class Meta:
        model  = Course
        fields = ['title', 'description', 'thumbnail', 'subject', 'level', 'status']
 
    def create(self, validated_data):
        validated_data['teacher'] = self.context['request'].user
        return super().create(validated_data)
    

class EnrollmentSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', read_only=True)
    student_name = serializers.CharField(source='student.full_name', read_only=True)
 
    class Meta:
        model  = Enrollment
        fields = ['id', 'student', 'student_name', 'course', 'course_title', 'status', 'enrolled_at']
        read_only_fields = ['id', 'student', 'enrolled_at']
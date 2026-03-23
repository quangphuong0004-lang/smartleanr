from django.conf import settings
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .models import Course, Enrollment, Lesson, LessonProgress, generate_join_code
from .serializers import (
    CourseSerializer,
    CourseCreateSerializer,
    LessonSerializer,
    LessonListSerializer,
    LessonProgressSerializer,
    EnrollmentSerializer,
)

def is_teacher(user):
    return user.is_authenticated and user.role == 'teacher'

def is_admin(user):
    return user.is_authenticated and user.role == 'admin'

def is_teacher_or_admin(user):
    return user.is_authenticated and user.role in ('teacher', 'admin')


#Khóa học
class CourseListView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]
    
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def get(self, request):
        courses = Course.objects.filter(status='public').select_related('teacher')
        
        #Lọc theo môn học
        subject = request.query_params.get('subject')
        if subject:
            courses = courses.filter(subject__icontains=subject)
            
        #Lọc theo level
        level = request.query_params.get('level')
        if level:
            courses = courses.filter(level=level)
            
        #Tìm kiếm theo tên
        search = request.query_params.get('search')
        if search:
            courses = courses.filter(title__icontains=search)
            
        serializer = CourseSerializer(courses, many = True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        if not is_teacher_or_admin(request.user):
            return Response(
                {"error": "Chỉ giáo viên mới có thể tạo khóa học."},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = CourseCreateSerializer(data=request.data, context={'request':request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        course = serializer.save()
        return Response(
            {
                'message':'Tạo khóa học thành công!',
                'course': CourseSerializer(course, context={'request': request}).data
            }, status=status.HTTP_201_CREATED
        )


#Chi tiết khóa học
class CourseDetailView(APIView):
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def get_object(self, pk):
        try:
            return Course.objects.select_related('teacher').get(pk=pk)
        
        except Course.DoesNotExist:
            return None
        
    def get(self, request, pk):
        course = self.get_object(pk)
        if not course:
            return Response({'error': 'Khóa học không tồn tại!'}, 
                            status=status.HTTP_404_NOT_FOUND)
        serializer = CourseSerializer(course, context={'request':request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def patch(self, request, pk):
        course = self.get_object(pk)
        if not course:
            return Response({'error': 'Khóa học không tồn tại!'},
                            status=status.HTTP_404_NOT_FOUND)
        if course.teacher != request.user and not is_admin(request.user):
            return Response({'error': 'Bạn không có quyền chỉnh sửa!'}, status=status.HTTP_403_FORBIDDEN)
        serializer = CourseCreateSerializer(course, data=request.data, partial=True, context = {'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response({
            'message': 'Cập nhật khóa học thành công!',
            'course': CourseSerializer(course, context = {'request': request}).data,
            }, status= status.HTTP_200_OK)
        
    def delete(self, request, pk):
        course = self.get_object(pk)
        if not course:
            return Response({'error': "Khóa học không tồn tại!"},
                            status=status.HTTP_404_NOT_FOUND)
            
        if course.teacher != request.user and not is_admin(request.user):
            return Response({'error':'Bạn không có quyền xóa khóa học này!'}, status=status.HTTP_403_FORBIDDEN)
        course.delete()
        return Response({'message': 'Xóa khóa học thành công!'}, status=status.HTTP_200_OK)



class MyCourseListView(APIView):
    
    permission_classes = [IsAuthenticated]
 
    def get(self, request):
        if is_teacher_or_admin(request.user):
            courses = Course.objects.filter(teacher=request.user).select_related('teacher')
        else:
            enrolled_ids = Enrollment.objects.filter(
                student=request.user, status='approved'
            ).values_list('course_id', flat=True)
            courses = Course.objects.filter(id__in=enrolled_ids).select_related('teacher')
 
        serializer = CourseSerializer(courses, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    


class EnrollView(APIView):
    permission_classes = [IsAuthenticated]
 
    def get_object(self, pk):
        try:
            return Course.objects.get(pk=pk)
        except Course.DoesNotExist:
            return None
 
    def post(self, request, pk):
        course = self.get_object(pk)
        if not course:
            return Response({"error": "Khóa học không tồn tại."}, status=status.HTTP_404_NOT_FOUND)
 
        # Giáo viên không được đăng ký khóa học
        if is_teacher_or_admin(request.user):
            return Response({"error": "Giáo viên không thể đăng ký khóa học."}, status=status.HTTP_400_BAD_REQUEST)
 
        # Kiểm tra đã đăng ký chưa
        if Enrollment.objects.filter(student=request.user, course=course).exists():
            return Response({"error": "Bạn đã đăng ký khóa học này rồi."}, status=status.HTTP_400_BAD_REQUEST)
 
        # Khóa học private → chờ duyệt
        enroll_status = 'pending' if course.status == 'private' else 'approved'
        enrollment = Enrollment.objects.create(
            student=request.user,
            course=course,
            status=enroll_status,
        )
        msg = "Đăng ký thành công! Chờ giáo viên duyệt." if enroll_status == 'pending' else "Đăng ký khóa học thành công!"
        return Response({"message": msg, "status": enroll_status}, status=status.HTTP_201_CREATED)
 
    def delete(self, request, pk):
        course = self.get_object(pk)
        if not course:
            return Response({"error": "Khóa học không tồn tại."}, status=status.HTTP_404_NOT_FOUND)
 
        enrollment = Enrollment.objects.filter(student=request.user, course=course).first()
        if not enrollment:
            return Response({"error": "Bạn chưa đăng ký khóa học này."}, status=status.HTTP_400_BAD_REQUEST)
 
        enrollment.delete()
        return Response({"message": "Hủy đăng ký thành công."}, status=status.HTTP_200_OK)
    

#Danh sách học sinh( của giáo viên) + Duyệt/từ chối ( giáo viên)
class EnrollmentManageView(APIView):
    permission_classes = [IsAuthenticated]
 
    def get(self, request, pk):
        try:
            course = Course.objects.get(pk=pk)
        except Course.DoesNotExist:
            return Response({"error": "Khóa học không tồn tại."}, status=status.HTTP_404_NOT_FOUND)
 
        if course.teacher != request.user and not is_admin(request.user):
            return Response({"error": "Bạn không có quyền xem danh sách này."}, status=status.HTTP_403_FORBIDDEN)
 
        enrollments = Enrollment.objects.filter(course=course).select_related('student')
        serializer  = EnrollmentSerializer(enrollments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
 
    def patch(self, request, pk, enroll_id):
        try:
            course = Course.objects.get(pk=pk)
        except Course.DoesNotExist:
            return Response({"error": "Khóa học không tồn tại."}, status=status.HTTP_404_NOT_FOUND)
 
        if course.teacher != request.user and not is_admin(request.user):
            return Response({"error": "Bạn không có quyền duyệt đăng ký."}, status=status.HTTP_403_FORBIDDEN)
 
        try:
            enrollment = Enrollment.objects.get(pk=enroll_id, course=course)
        except Enrollment.DoesNotExist:
            return Response({"error": "Không tìm thấy đăng ký."}, status=status.HTTP_404_NOT_FOUND)
 
        new_status = request.data.get('status')
        if new_status not in ('approved', 'rejected'):
            return Response({"error": "Trạng thái không hợp lệ."}, status=status.HTTP_400_BAD_REQUEST)
 
        enrollment.status = new_status
        enrollment.save()
        return Response({"message": f"Đã {'duyệt' if new_status == 'approved' else 'từ chối'} đăng ký."}, status=status.HTTP_200_OK)


#Danh sách bài học + tạo bài học ( giáo viên )
class LessonListView(APIView):
    
    permission_classes = [IsAuthenticated]
 
    def get(self, request, pk):
        try:
            course = Course.objects.get(pk=pk)
        except Course.DoesNotExist:
            return Response({"error": "Khóa học không tồn tại."}, status=status.HTTP_404_NOT_FOUND)
 
        # Kiểm tra quyền truy cập
        is_owner  = course.teacher == request.user
        is_member = Enrollment.objects.filter(
            student=request.user, course=course, status='approved'
        ).exists()
 
        if not is_owner and not is_member and not is_admin(request.user):
            return Response({"error": "Bạn cần đăng ký khóa học để xem bài học."}, status=status.HTTP_403_FORBIDDEN)
 
        lessons    = course.lessons.all()
        serializer = LessonListSerializer(lessons, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
 
    def post(self, request, pk):
        try:
            course = Course.objects.get(pk=pk)
        except Course.DoesNotExist:
            return Response({"error": "Khóa học không tồn tại."}, status=status.HTTP_404_NOT_FOUND)
 
        if course.teacher != request.user and not is_admin(request.user):
            return Response({"error": "Bạn không có quyền thêm bài học."}, status=status.HTTP_403_FORBIDDEN)
 
        data = request.data.copy()
        data['course'] = str(pk)
        serializer = LessonSerializer(data=data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        lesson = serializer.save()
        return Response(
            {"message": "Tạo bài học thành công!", "lesson": LessonSerializer(lesson).data},
            status=status.HTTP_201_CREATED,
        )
 


#Chi tiết bài học, sửa bài học, xóa bài học
class LessonDetailView(APIView):
    permission_classes = [IsAuthenticated]
 
    def get_objects(self, pk, lesson_id):
        try:
            course = Course.objects.get(pk=pk)
            lesson = Lesson.objects.get(pk=lesson_id, course=course)
            return course, lesson
        except (Course.DoesNotExist, Lesson.DoesNotExist):
            return None, None
 
    def get(self, request, pk, lesson_id):
        course, lesson = self.get_objects(pk, lesson_id)
        if not lesson:
            return Response({"error": "Bài học không tồn tại."}, status=status.HTTP_404_NOT_FOUND)
 
        # Kiểm tra quyền
        is_owner  = course.teacher == request.user
        is_member = Enrollment.objects.filter(
            student=request.user, course=course, status='approved'
        ).exists()
 
        if not is_owner and not is_member and not is_admin(request.user):
            return Response({"error": "Bạn cần đăng ký khóa học."}, status=status.HTTP_403_FORBIDDEN)
 
        # Tự động tạo/cập nhật tiến độ sang in_progress
        if not is_owner:
            LessonProgress.objects.get_or_create(
                student=request.user,
                lesson=lesson,
                defaults={'status': 'in_progress'},
            )
 
        serializer = LessonSerializer(lesson)
        return Response(serializer.data, status=status.HTTP_200_OK)
 
    def patch(self, request, pk, lesson_id):
        course, lesson = self.get_objects(pk, lesson_id)
        if not lesson:
            return Response({"error": "Bài học không tồn tại."}, status=status.HTTP_404_NOT_FOUND)
 
        if course.teacher != request.user and not is_admin(request.user):
            return Response({"error": "Bạn không có quyền chỉnh sửa bài học này."}, status=status.HTTP_403_FORBIDDEN)
 
        serializer = LessonSerializer(lesson, data=request.data, partial=True, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response({"message": "Cập nhật bài học thành công!", "lesson": serializer.data}, status=status.HTTP_200_OK)
 
    def delete(self, request, pk, lesson_id):
        course, lesson = self.get_objects(pk, lesson_id)
        if not lesson:
            return Response({"error": "Bài học không tồn tại."}, status=status.HTTP_404_NOT_FOUND)
 
        if course.teacher != request.user and not is_admin(request.user):
            return Response({"error": "Bạn không có quyền xóa bài học này."}, status=status.HTTP_403_FORBIDDEN)
 
        lesson.delete()
        return Response({"message": "Xóa bài học thành công."}, status=status.HTTP_200_OK)


#Đánh dấu bài học hoàn thành
class LessonCompleteView(APIView):
    permission_classes = [IsAuthenticated]
 
    def post(self, request, pk, lesson_id):
        try:
            lesson = Lesson.objects.get(pk=lesson_id, course_id=pk)
        except Lesson.DoesNotExist:
            return Response({"error": "Bài học không tồn tại."}, status=status.HTTP_404_NOT_FOUND)
 
        # Kiểm tra đã đăng ký khóa học chưa
        if not Enrollment.objects.filter(
            student=request.user, course_id=pk, status='approved'
        ).exists():
            return Response({"error": "Bạn cần đăng ký khóa học trước."}, status=status.HTTP_403_FORBIDDEN)
 
        progress, _ = LessonProgress.objects.get_or_create(
            student=request.user,
            lesson=lesson,
        )
        progress.status       = 'completed'
        progress.completed_at = timezone.now()
        progress.save()
 
        return Response({"message": "Đã đánh dấu hoàn thành bài học!"}, status=status.HTTP_200_OK)
 

#Lấy tiến độ học tập của học sinh trong khóa học
class CourseProgressView(APIView):

    permission_classes = [IsAuthenticated]
 
    def get(self, request, pk):
        try:
            course = Course.objects.get(pk=pk)
        except Course.DoesNotExist:
            return Response({"error": "Khóa học không tồn tại."}, status=status.HTTP_404_NOT_FOUND)
 
        lessons = course.lessons.all()
        total    = lessons.count()
        if total == 0:
            return Response({"total": 0, "completed": 0, "percentage": 0, "lessons": []})
 
        progresses = LessonProgress.objects.filter(
            student=request.user,
            lesson__course=course,
        ).select_related('lesson')
 
        progress_map = {p.lesson_id: p.status for p in progresses}
 
        lesson_data = []
        for lesson in lessons:
            lesson_data.append({
                "lesson_id":   str(lesson.id),
                "title":       lesson.title,
                "order_index": lesson.order_index,
                "status":      progress_map.get(lesson.id, 'not_started'),
            })
 
        completed  = sum(1 for p in lesson_data if p['status'] == 'completed')
        percentage = round(completed / total * 100)
 
        return Response({
            "total":      total,
            "completed":  completed,
            "percentage": percentage,
            "lessons":    lesson_data,
        }, status=status.HTTP_200_OK)


#Tham gia khóa học bằng mã
class JoinByCodeView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):
        code = request.data.get('code', '').strip().upper()
        if not code:
            return Response({"error": "Vui lòng nhập mã khóa học."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            course = Course.objects.get(join_code=code)
        except Course.DoesNotExist:
            return Response({"error": "Mã khóa học không tồn tại."}, status=status.HTTP_404_NOT_FOUND)

        # Kiểm tra đã đăng ký chưa
        if Enrollment.objects.filter(student=request.user, course=course).exists():
            return Response({
                "message": "Bạn đã đăng ký khóa học này rồi.",
                "course": CourseSerializer(course, context={'request': request}).data,
                "already_enrolled": True,
            }, status=status.HTTP_200_OK)

        # Tự đăng ký
        enroll_status = 'pending' if course.status == 'private' else 'approved'
        Enrollment.objects.create(student=request.user, course=course, status=enroll_status)

        return Response({
            "message": "Đăng ký thành công!" if enroll_status == 'approved' else "Đã gửi yêu cầu, chờ duyệt.",
            "course": CourseSerializer(course, context={'request': request}).data,
            "already_enrolled": False,
        }, status=status.HTTP_201_CREATED)


class CourseQRView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            course = Course.objects.get(pk=pk)
        except Course.DoesNotExist:
            return Response({"error": "Khóa học không tồn tại."}, status=status.HTTP_404_NOT_FOUND)

        # Chỉ teacher sở hữu mới xem được QR
        if course.teacher != request.user and not is_admin(request.user):
            return Response({"error": "Không có quyền."}, status=status.HTTP_403_FORBIDDEN)

        import qrcode, io, base64
        join_url = f"{settings.FRONTEND_URL}/courses/join/?code={course.join_code}"
        qr = qrcode.QRCode(version=1, box_size=8, border=4)
        qr.add_data(join_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#4ade80", back_color="#0a0e1a")

        buf = io.BytesIO()
        img.save(buf, format='PNG')
        b64 = base64.b64encode(buf.getvalue()).decode()

        return Response({
            "join_code": course.join_code,
            "join_url":  join_url,
            "qr_base64": f"data:image/png;base64,{b64}",
        })


#Tạo mã mới
class RegenerateCodeView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            course = Course.objects.get(pk=pk)
        except Course.DoesNotExist:
            return Response({"error": "Khóa học không tồn tại."}, status=status.HTTP_404_NOT_FOUND)

        if course.teacher != request.user and not is_admin(request.user):
            return Response({"error": "Không có quyền."}, status=status.HTTP_403_FORBIDDEN)

        course.join_code = generate_join_code()
        course.save()
        return Response({"message": "Đã tạo mã mới!", "join_code": course.join_code})
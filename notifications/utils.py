def create_notification(recipient, type, title, message='', url=''):
    """Tạo notification. Import và gọi hàm này từ các app khác."""
    from .models import Notification
    return Notification.objects.create(
        recipient=recipient,
        type=type,
        title=title,
        message=message,
        url=url,
    )
 
def notify_enroll_request(course, student):
    create_notification(
        recipient=course.teacher,
        type='enroll_request',
        title=f'{student.full_name or student.username} muốn tham gia "{course.title}"',
        message='Vào trang quản lý để duyệt yêu cầu.',
        url=f'/courses/{course.id}/enrollments/',
    )
 
def notify_enroll_approved(enrollment):
    create_notification(
        recipient=enrollment.student,
        type='enroll_approved',
        title=f'Đăng ký "{enrollment.course.title}" được duyệt!',
        message='Bạn có thể bắt đầu học ngay bây giờ.',
        url=f'/courses/{enrollment.course.id}/',
    )
 
def notify_enroll_rejected(enrollment):
    create_notification(
        recipient=enrollment.student,
        type='enroll_rejected',
        title=f'Đăng ký "{enrollment.course.title}" bị từ chối.',
        message='Liên hệ giáo viên để biết thêm thông tin.',
        url=f'/courses/{enrollment.course.id}/',
    )
 
def notify_new_lesson(lesson):
    """Gửi cho tất cả học sinh đã đăng ký khóa học."""
    from courses.models import Enrollment
    enrollments = Enrollment.objects.filter(
        course=lesson.course, status='approved'
    ).select_related('student')
    for e in enrollments:
        create_notification(
            recipient=e.student,
            type='new_lesson',
            title=f'Bài học mới: "{lesson.title}"',
            message=f'Khóa học {lesson.course.title} vừa có bài học mới.',
            url=f'/courses/{lesson.course.id}/lessons/{lesson.id}/',
        )
 
def notify_new_quiz(quiz):
    """Gửi cho tất cả học sinh đã đăng ký."""
    from courses.models import Enrollment
    enrollments = Enrollment.objects.filter(
        course=quiz.course, status='approved'
    ).select_related('student')
    for e in enrollments:
        create_notification(
            recipient=e.student,
            type='new_quiz',
            title=f'Quiz mới: "{quiz.title}"',
            message=f'Khóa học {quiz.course.title} vừa có bài kiểm tra mới.',
            url=f'/courses/{quiz.course.id}/quizzes/{quiz.id}/',
        )
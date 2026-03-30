from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from courses.models import Course, Enrollment, Lesson, LessonProgress
from quizzes.models import Quiz, QuizAttempt


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.role in ('teacher', 'admin'):
            return self._teacher_dashboard(request)
        return self._student_dashboard(request)

    # ── Student dashboard ─────────────────────────────────────
    def _student_dashboard(self, request):
        user = request.user

        # Khóa học đã đăng ký
        enrollments = Enrollment.objects.filter(
            student=user, status='approved'
        ).select_related('course', 'course__teacher')
        enrolled_courses = [e.course for e in enrollments]
        total_courses    = len(enrolled_courses)

        # Tiến độ từng khóa học
        course_progress = []
        total_completed_lessons = 0
        total_lessons           = 0

        for course in enrolled_courses:
            lessons     = course.lessons.all()
            count       = lessons.count()
            completed   = LessonProgress.objects.filter(
                student=user, lesson__course=course, status='completed'
            ).count()
            pct = round(completed / count * 100) if count > 0 else 0
            total_lessons           += count
            total_completed_lessons += completed
            course_progress.append({
                'id':          str(course.id),
                'title':       course.title,
                'subject':     course.subject,
                'teacher':     course.teacher.full_name or course.teacher.username,
                'lesson_count':count,
                'completed':   completed,
                'percentage':  pct,
                'thumbnail_url': request.build_absolute_uri(course.thumbnail.url) if course.thumbnail else None,
            })

        # Tính streak — số ngày liên tiếp có hoạt động học tập
        streak = self._calculate_streak(user)

        # Quiz attempts
        attempts = QuizAttempt.objects.filter(
            student=user, status='completed'
        ).select_related('quiz', 'quiz__course')
        total_quizzes = attempts.count()
        passed_quizzes = attempts.filter(
            score__gte=models_pass_score(attempts)
        ).count()

        # Tính passed đúng cách
        passed_count = sum(1 for a in attempts if a.is_passed)
        avg_score    = round(sum(a.score for a in attempts) / total_quizzes, 1) if total_quizzes else 0

        # Hoạt động gần đây (7 ngày)
        week_ago = timezone.now() - timedelta(days=7)
        recent_progress = LessonProgress.objects.filter(
            student=user, status='completed',
            complete_at__gte=week_ago
        ).select_related('lesson', 'lesson__course').order_by('-complete_at')[:10]

        recent_activity = [{
            'type':       'lesson_complete',
            'title':      p.lesson.title,
            'course':     p.lesson.course.title,
            'course_id':  str(p.lesson.course.id),
            'lesson_id':  str(p.lesson.id),
            'time':       p.complete_at,
        } for p in recent_progress]

        return Response({
            'role': 'student',
            'stats': {
                'total_courses':    total_courses,
                'total_lessons':    total_lessons,
                'completed_lessons':total_completed_lessons,
                'total_quizzes':    total_quizzes,
                'passed_quizzes':   passed_count,
                'avg_quiz_score':   avg_score,
                'overall_progress': round(total_completed_lessons / total_lessons * 100) if total_lessons else 0,
                'streak':           streak,
            },
            'course_progress': sorted(course_progress, key=lambda x: x['percentage'], reverse=True),
            'recent_activity': recent_activity,
            'quiz_attempts': [{
                'quiz_title':   a.quiz.title,
                'course_title': a.quiz.course.title,
                'course_id':    str(a.quiz.course.id),
                'quiz_id':      str(a.quiz.id),
                'attempt_id':   str(a.id),
                'score':        a.score,
                'is_passed':    a.is_passed,
                'ended_at':     a.ended_at,
            } for a in attempts.order_by('-ended_at')[:5]],
        })

    def _calculate_streak(self, user):
        """Đếm số ngày liên tiếp user có hoàn thành ít nhất 1 bài học"""
        from django.db.models.functions import TruncDate
        # Lấy danh sách các ngày có activity (distinct)
        active_days = (
            LessonProgress.objects.filter(student=user, status='completed', complete_at__isnull=False)
            .annotate(day=TruncDate('complete_at'))
            .values_list('day', flat=True)
            .distinct()
            .order_by('-day')
        )
        if not active_days:
            return 0

        today   = timezone.now().date()
        streak  = 0
        current = today

        for day in active_days:
            if day == current or day == current - timedelta(days=1):
                streak  += 1
                current  = day - timedelta(days=1) if day == current else day - timedelta(days=1)
                current  = day
                # Điều chỉnh lại: nếu day == current thì ngày tiếp theo là day-1
                current  = day - timedelta(days=1)
            else:
                break

        return streak

    # ── Teacher dashboard ─────────────────────────────────────
    def _teacher_dashboard(self, request):
        user = request.user

        courses = Course.objects.filter(teacher=user).prefetch_related('lessons', 'enrollments')
        total_courses  = courses.count()
        total_students = Enrollment.objects.filter(
            course__teacher=user, status='approved'
        ).values('student').distinct().count()
        total_lessons  = Lesson.objects.filter(course__teacher=user).count()
        total_quizzes  = Quiz.objects.filter(course__teacher=user).count()

        # Thống kê từng khóa học
        course_stats = []
        for c in courses:
            enrolled = c.enrollments.filter(status='approved').count()
            lessons  = c.lessons.count()
            course_stats.append({
                'id':             str(c.id),
                'title':          c.title,
                'subject':        c.subject,
                'student_count':  enrolled,
                'lesson_count':   lessons,
                'status':         c.status,
                'thumbnail_url':  request.build_absolute_uri(c.thumbnail.url) if c.thumbnail else None,
            })

        # Quiz performance
        quiz_stats = []
        for quiz in Quiz.objects.filter(course__teacher=user, is_published=True):
            attempts = QuizAttempt.objects.filter(quiz=quiz, status='completed')
            count    = attempts.count()
            if count:
                passed  = sum(1 for a in attempts if a.is_passed)
                avg     = round(sum(a.score for a in attempts) / count, 1)
            else:
                passed = avg = 0
            quiz_stats.append({
                'id':         str(quiz.id),
                'title':      quiz.title,
                'course':     quiz.course.title,
                'course_id':  str(quiz.course.id),
                'total':      count,
                'passed':     passed,
                'pass_rate':  round(passed / count * 100) if count else 0,
                'avg_score':  avg,
            })

        # Đăng ký chờ duyệt
        pending = Enrollment.objects.filter(
            course__teacher=user, status='pending'
        ).select_related('student', 'course').order_by('-enrolled_at')[:10]

        return Response({
            'role': 'teacher',
            'stats': {
                'total_courses':  total_courses,
                'total_students': total_students,
                'total_lessons':  total_lessons,
                'total_quizzes':  total_quizzes,
            },
            'course_stats':  course_stats,
            'quiz_stats':    quiz_stats[:5],
            'pending_enrollments': [{
                'id':         str(e.id),
                'student':    e.student.full_name or e.student.username,
                'course':     e.course.title,
                'course_id':  str(e.course.id),
                'enrolled_at':e.enrolled_at,
            } for e in pending],
        })


def models_pass_score(attempts):
    # helper — không dùng, tính inline
    return 0
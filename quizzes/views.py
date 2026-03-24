from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

from courses.models import Course, Enrollment
from courses.views import is_admin, is_teacher_or_admin
from .models import Quiz, Question, Choice, QuizAttempt, QuizAnswer
from .serializers import (
    QuizListSerializer, QuizDetailSerializer, QuizCreateSerializer,
    QuestionCreateSerializer, ChoiceCreateSerializer, AttemptResultSerializer,
)


def get_course_or_404(pk):
    try:
        return Course.objects.get(pk=pk)
    except Course.DoesNotExist:
        return None

def is_enrolled(user, course):
    return Enrollment.objects.filter(
        student=user, course=course, status='approved'
    ).exists()
    
# Quiz List + Create
class QuizListView(APIView):

    def get_permissions(self):
        return [IsAuthenticated()] if self.request.method == 'POST' else [AllowAny()]

    def get(self, request, course_pk):
        course = get_course_or_404(course_pk)
        if not course:
            return Response({'error': 'Khóa học không tồn tại.'}, status=404)

        # Học sinh chỉ thấy quiz đã publish + đã đăng ký
        is_owner = course.teacher == request.user or is_admin(request.user)
        if is_owner:
            quizzes = course.quizzes.all()
        else:
            if not request.user.is_authenticated or not is_enrolled(request.user, course):
                return Response({'error': 'Bạn cần đăng ký khóa học.'}, status=403)
            quizzes = course.quizzes.filter(is_published=True)

        serializer = QuizListSerializer(quizzes, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request, course_pk):
        course = get_course_or_404(course_pk)
        if not course:
            return Response({'error': 'Khóa học không tồn tại.'}, status=404)
        if course.teacher != request.user and not is_admin(request.user):
            return Response({'error': 'Không có quyền.'}, status=403)

        data = request.data.copy()
        data['course'] = str(course_pk)
        serializer = QuizCreateSerializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        quiz = serializer.save()
        return Response(
            {'message': 'Tạo quiz thành công!', 'quiz': QuizListSerializer(quiz, context={'request': request}).data},
            status=201
        )


# Quiz Detail + Edit + Delete 
class QuizDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_quiz(self, course_pk, quiz_pk):
        try:
            return Quiz.objects.get(pk=quiz_pk, course_id=course_pk)
        except Quiz.DoesNotExist:
            return None

    def get(self, request, course_pk, quiz_pk):
        quiz   = self.get_quiz(course_pk, quiz_pk)
        if not quiz:
            return Response({'error': 'Quiz không tồn tại.'}, status=404)

        course   = quiz.course
        is_owner = course.teacher == request.user or is_admin(request.user)

        if not is_owner:
            if not is_enrolled(request.user, course):
                return Response({'error': 'Bạn cần đăng ký khóa học.'}, status=403)
            if not quiz.is_published:
                return Response({'error': 'Quiz chưa được mở.'}, status=403)

        serializer = QuizDetailSerializer(quiz)
        return Response(serializer.data)

    def patch(self, request, course_pk, quiz_pk):
        quiz = self.get_quiz(course_pk, quiz_pk)
        if not quiz:
            return Response({'error': 'Quiz không tồn tại.'}, status=404)
        if quiz.course.teacher != request.user and not is_admin(request.user):
            return Response({'error': 'Không có quyền.'}, status=403)

        serializer = QuizCreateSerializer(quiz, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        serializer.save()
        return Response({'message': 'Cập nhật quiz thành công!'})

    def delete(self, request, course_pk, quiz_pk):
        quiz = self.get_quiz(course_pk, quiz_pk)
        if not quiz:
            return Response({'error': 'Quiz không tồn tại.'}, status=404)
        if quiz.course.teacher != request.user and not is_admin(request.user):
            return Response({'error': 'Không có quyền.'}, status=403)
        quiz.delete()
        return Response({'message': 'Đã xóa quiz.'})



# ── Question CRUD ─────────────────────────────────────────────
class QuestionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get_quiz(self, course_pk, quiz_pk):
        try:
            return Quiz.objects.get(pk=quiz_pk, course_id=course_pk)
        except Quiz.DoesNotExist:
            return None

    def post(self, request, course_pk, quiz_pk):
        quiz = self.get_quiz(course_pk, quiz_pk)
        if not quiz:
            return Response({'error': 'Quiz không tồn tại.'}, status=404)
        if quiz.course.teacher != request.user and not is_admin(request.user):
            return Response({'error': 'Không có quyền.'}, status=403)

        serializer = QuestionCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        question = serializer.save(quiz=quiz)

        # Tạo choices kèm theo nếu có
        choices_data = request.data.get('choices', [])
        for c in choices_data:
            Choice.objects.create(
                question   = question,
                text       = c.get('text', ''),
                is_correct = c.get('is_correct', False),
            )

        return Response({'message': 'Thêm câu hỏi thành công!', 'question_id': str(question.id)}, status=201)


class QuestionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_question(self, course_pk, quiz_pk, question_pk):
        try:
            return Question.objects.get(pk=question_pk, quiz_id=quiz_pk, quiz__course_id=course_pk)
        except Question.DoesNotExist:
            return None

    def patch(self, request, course_pk, quiz_pk, question_pk):
        question = self.get_question(course_pk, quiz_pk, question_pk)
        if not question:
            return Response({'error': 'Câu hỏi không tồn tại.'}, status=404)
        if question.quiz.course.teacher != request.user and not is_admin(request.user):
            return Response({'error': 'Không có quyền.'}, status=403)

        serializer = QuestionCreateSerializer(question, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        serializer.save()

        # Cập nhật choices nếu có
        choices_data = request.data.get('choices')
        if choices_data is not None:
            question.choices.all().delete()
            for c in choices_data:
                Choice.objects.create(
                    question   = question,
                    text       = c.get('text', ''),
                    is_correct = c.get('is_correct', False),
                )

        return Response({'message': 'Cập nhật câu hỏi thành công!'})

    def delete(self, request, course_pk, quiz_pk, question_pk):
        question = self.get_question(course_pk, quiz_pk, question_pk)
        if not question:
            return Response({'error': 'Câu hỏi không tồn tại.'}, status=404)
        if question.quiz.course.teacher != request.user and not is_admin(request.user):
            return Response({'error': 'Không có quyền.'}, status=403)
        question.delete()
        return Response({'message': 'Đã xóa câu hỏi.'})


# ── Attempt: Bắt đầu + Nộp bài ───────────────────────────────
class QuizStartView(APIView):
    """POST → tạo attempt mới, trả về quiz + câu hỏi"""
    permission_classes = [IsAuthenticated]

    def post(self, request, course_pk, quiz_pk):
        try:
            quiz = Quiz.objects.get(pk=quiz_pk, course_id=course_pk, is_published=True)
        except Quiz.DoesNotExist:
            return Response({'error': 'Quiz không tồn tại hoặc chưa mở.'}, status=404)

        if not is_enrolled(request.user, quiz.course):
            return Response({'error': 'Bạn cần đăng ký khóa học.'}, status=403)

        # Kiểm tra đã làm chưa
        if QuizAttempt.objects.filter(quiz=quiz, student=request.user, status='completed').exists():
            return Response({'error': 'Bạn đã hoàn thành quiz này rồi.'}, status=400)

        # Xóa attempt cũ nếu đang dở (in_progress)
        QuizAttempt.objects.filter(quiz=quiz, student=request.user, status='in_progress').delete()

        attempt = QuizAttempt.objects.create(quiz=quiz, student=request.user)
        return Response({
            'attempt_id': str(attempt.id),
            'quiz':       QuizDetailSerializer(quiz).data,
            'started_at': attempt.started_at,
        }, status=201)


class QuizSubmitView(APIView):
    """POST → nộp bài, tính điểm, trả về kết quả"""
    permission_classes = [IsAuthenticated]

    def post(self, request, course_pk, quiz_pk, attempt_pk):
        try:
            attempt = QuizAttempt.objects.get(
                pk=attempt_pk, quiz_id=quiz_pk,
                student=request.user, status='in_progress'
            )
        except QuizAttempt.DoesNotExist:
            return Response({'error': 'Không tìm thấy attempt.'}, status=404)

        quiz = attempt.quiz

        # Kiểm tra hết giờ
        if quiz.time_limit:
            elapsed = (timezone.now() - attempt.started_at).total_seconds()
            if elapsed > quiz.time_limit + 10:  # +10s tolerance
                attempt.status = 'timed_out'
                attempt.ended_at = timezone.now()
                attempt.save()
                return Response({'error': 'Hết thời gian làm bài.'}, status=400)

        # answers: [{ question_id, choice_id }, ...]
        answers_data = request.data.get('answers', [])

        total_points  = 0
        earned_points = 0

        for q in quiz.questions.prefetch_related('choices').all():
            total_points += q.points
            # Tìm câu trả lời của học sinh cho câu hỏi này
            student_answer = next(
                (a for a in answers_data if str(a.get('question_id')) == str(q.id)),
                None
            )
            choice_id = student_answer.get('choice_id') if student_answer else None

            # Lưu câu trả lời
            if choice_id:
                try:
                    choice = q.choices.get(pk=choice_id)
                    QuizAnswer.objects.update_or_create(
                        attempt=attempt, question=q,
                        defaults={'choice': choice}
                    )
                    if choice.is_correct:
                        earned_points += q.points
                except Choice.DoesNotExist:
                    pass
            else:
                # Không trả lời — vẫn lưu với choice=None
                QuizAnswer.objects.update_or_create(
                    attempt=attempt, question=q,
                    defaults={'choice': None}
                )

        # Tính điểm %
        score = round(earned_points / total_points * 100, 1) if total_points > 0 else 0

        attempt.score    = score
        attempt.status   = 'completed'
        attempt.ended_at = timezone.now()
        attempt.save()

        serializer = AttemptResultSerializer(attempt)
        return Response({
            'message':  'Nộp bài thành công!',
            'result':   serializer.data,
        })


class QuizResultView(APIView):
    """GET → xem lại kết quả của attempt đã hoàn thành"""
    permission_classes = [IsAuthenticated]

    def get(self, request, course_pk, quiz_pk, attempt_pk):
        try:
            attempt = QuizAttempt.objects.get(
                pk=attempt_pk, quiz_id=quiz_pk,
                student=request.user, status='completed'
            )
        except QuizAttempt.DoesNotExist:
            return Response({'error': 'Không tìm thấy kết quả.'}, status=404)

        serializer = AttemptResultSerializer(attempt)
        return Response(serializer.data)


# ── Teacher: xem tất cả kết quả của một quiz ─────────────────
class QuizAttemptsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, course_pk, quiz_pk):
        try:
            quiz = Quiz.objects.get(pk=quiz_pk, course_id=course_pk)
        except Quiz.DoesNotExist:
            return Response({'error': 'Quiz không tồn tại.'}, status=404)

        if quiz.course.teacher != request.user and not is_admin(request.user):
            return Response({'error': 'Không có quyền.'}, status=403)

        attempts = quiz.attempts.filter(status='completed').select_related('student')
        data = [{
            'student':    attempts_item.student.full_name or attempts_item.student.username,
            'score':      attempts_item.score,
            'is_passed':  attempts_item.is_passed,
            'duration':   attempts_item.duration_seconds,
            'ended_at':   attempts_item.ended_at,
        } for attempts_item in attempts]

        return Response({
            'quiz':        quiz.title,
            'pass_score':  quiz.pass_score,
            'total':       attempts.count(),
            'passed':      sum(1 for a in attempts if a.is_passed),
            'attempts':    data,
        })
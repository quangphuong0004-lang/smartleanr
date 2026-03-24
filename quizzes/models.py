from django.db import models
import uuid
from django.utils import timezone


class Quiz(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='quizzes')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    time_limit = models.PositiveIntegerField(null=True, blank=True, help_text='Giây. Null = không giới hạn')
    pass_score = models.PositiveIntegerField(default=70, help_text='% điểm đạt')
    is_published = models.BooleanField(default=False) #Trạng thái xuất bản, mặc định False
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.title} — {self.course.title}'

    @property
    def question_count(self):
        return self.questions.count()


class Question(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    order = models.PositiveIntegerField(default=0) #Thứ tự câu hỏi
    points = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'Q{self.order}: {self.text[:60]}'
    
    
class Choice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f'{"✓" if self.is_correct else "✗"} {self.text[:60]}'
    
#Lượt làm quiz
class QuizAttempt(models.Model):
    STATUS = [
        ('in_progress', 'Đang làm'),
        ('completed',   'Hoàn thành'),
        ('timed_out',   'Hết giờ'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    student = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='quiz_attempts')
    status = models.CharField(max_length=20, choices=STATUS, default='in_progress')
    score = models.FloatField(null=True, blank=True)        # % điểm
    started_at = models.DateTimeField(auto_now_add=True) #thời gian bắt đầu
    ended_at = models.DateTimeField(null=True, blank=True) #thời gian kết thúc

    class Meta:
        # unique_together = ('quiz', 'student') trường hợp mỗi học sinh chỉ làm 1 lần.
        ordering = ['-started_at']

    @property
    def is_passed(self):
        return self.score is not None and self.score >= self.quiz.pass_score

    @property #Thời gian làm bài
    def duration_seconds(self):
        if self.ended_at:
            return int((self.ended_at - self.started_at).total_seconds())
        return None


#Lưu câu trả lời của học sinh
class QuizAnswer(models.Model):
    id       = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt  = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice   = models.ForeignKey(Choice, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        unique_together = ('attempt', 'question') #một câu hỏi chỉ có một câu trả lời
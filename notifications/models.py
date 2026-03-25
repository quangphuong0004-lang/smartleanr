import uuid
from django.db import models


class Notification(models.Model):
    TYPES = [
        ('enroll_request', 'Yêu cầu đăng ký'),
        ('enroll_approved', 'Đăng ký được duyệt'),
        ('enroll_rejected', 'Đăng ký bị từ chối'),
        ('new_lesson', 'Bài học mới'),
        ('new_quiz', 'Quiz mới'),
        ('quiz_result','Kết quả quiz'),
        ('system', 'Hệ thống'),
    ]

    id  = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='notifications')
    type  = models.CharField(max_length=30, choices=TYPES, default='system')
    title  = models.CharField(max_length=255)
    message = models.TextField(blank=True)
    url = models.CharField(max_length=500, blank=True)  # link điều hướng
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.recipient} — {self.title}'



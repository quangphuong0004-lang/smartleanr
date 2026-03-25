import uuid
from django.db import models
 
 
class TutorSession(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user       = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='tutor_sessions')
    course     = models.ForeignKey('courses.Course', on_delete=models.SET_NULL, null=True, blank=True)
    title      = models.CharField(max_length=255, default='Phiên mới')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
 
    class Meta:
        ordering = ['-updated_at']
 
    def __str__(self):
        return f'{self.user.username} — {self.title}'
 
 
class TutorMessage(models.Model):
    ROLES = [('user', 'User'), ('assistant', 'Assistant')]
 
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session    = models.ForeignKey(TutorSession, on_delete=models.CASCADE, related_name='messages')
    role       = models.CharField(max_length=10, choices=ROLES)
    content    = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        ordering = ['created_at']
 
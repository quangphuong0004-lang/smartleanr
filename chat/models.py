import uuid
from django.db import models
 
 
class ChatRoom(models.Model):
    """Mỗi khóa học có 1 chat room"""
    id      = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course  = models.OneToOneField('courses.Course', on_delete=models.CASCADE, related_name='chat_room')
    created_at = models.DateTimeField(auto_now_add=True)
 
    def __str__(self):
        return f'Chat — {self.course.title}'
 
 
class Message(models.Model):
    id        = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room      = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender    = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='chat_messages')
    content   = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        ordering = ['created_at']
 
    def __str__(self):
        return f'{self.sender.username}: {self.content[:50]}'
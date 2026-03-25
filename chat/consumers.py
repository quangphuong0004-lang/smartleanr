import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
 
 
class ChatConsumer(AsyncWebsocketConsumer):
 
    async def connect(self):
        self.course_id  = self.scope['url_route']['kwargs']['course_id']
        self.room_group = f'chat_{self.course_id}'
        self.user       = self.scope['user']
 
        # Kiểm tra đăng nhập
        if not self.user.is_authenticated:
            await self.close()
            return
 
        # Kiểm tra quyền truy cập phòng chat
        if not await self.has_access():
            await self.close()
            return
 
        await self.channel_layer.group_add(self.room_group, self.channel_name)
        await self.accept()
 
        # Gửi 30 tin nhắn gần nhất
        messages = await self.get_recent_messages()
        await self.send(text_data=json.dumps({
            'type':     'history',
            'messages': messages,
        }))
 
        # Thông báo user online
        await self.channel_layer.group_send(self.room_group, {
            'type':     'user_join',
            'username': self.user.full_name or self.user.username,
            'user_id':  str(self.user.id),
        })
 
    async def disconnect(self, close_code):
        if hasattr(self, 'room_group'):
            await self.channel_layer.group_discard(self.room_group, self.channel_name)
            await self.channel_layer.group_send(self.room_group, {
                'type':     'user_leave',
                'username': self.user.full_name or self.user.username,
                'user_id':  str(self.user.id),
            })
 
    async def receive(self, text_data):
        data = json.loads(text_data)
        msg_type = data.get('type', 'message')
 
        if msg_type == 'message':
            content = data.get('content', '').strip()
            if not content or len(content) > 2000:
                return
 
            # Lưu vào DB
            message = await self.save_message(content)
 
            # Broadcast
            await self.channel_layer.group_send(self.room_group, {
                'type':       'chat_message',
                'id':         str(message.id),
                'content':    message.content,
                'sender_id':  str(self.user.id),
                'sender_name':self.user.full_name or self.user.username,
                'avatar_url': await self.get_avatar_url(),
                'created_at': message.created_at.isoformat(),
            })
 
    # ── Handlers ──────────────────────────────────────────────
    async def chat_message(self, event):
        await self.send(text_data=json.dumps({'type': 'message', **{k:v for k,v in event.items() if k!='type'}}))
 
    async def user_join(self, event):
        await self.send(text_data=json.dumps({'type': 'user_join', 'username': event['username'], 'user_id': event['user_id']}))
 
    async def user_leave(self, event):
        await self.send(text_data=json.dumps({'type': 'user_leave', 'username': event['username'], 'user_id': event['user_id']}))
 
    # ── DB helpers ────────────────────────────────────────────
    @database_sync_to_async
    def has_access(self):
        from courses.models import Course, Enrollment
        try:
            course = Course.objects.get(pk=self.course_id)
            if course.teacher == self.user:
                return True
            return Enrollment.objects.filter(
                student=self.user, course=course, status='approved'
            ).exists()
        except Course.DoesNotExist:
            return False
 
    @database_sync_to_async
    def get_recent_messages(self):
        from .models import ChatRoom, Message
        room, _ = ChatRoom.objects.get_or_create(course_id=self.course_id)
        msgs = Message.objects.filter(room=room).select_related('sender').order_by('-created_at')[:30]
        return [{
            'id':          str(m.id),
            'content':     m.content,
            'sender_id':   str(m.sender.id),
            'sender_name': m.sender.full_name or m.sender.username,
            'avatar_url':  m.sender.avatar.url if m.sender.avatar else None,
            'created_at':  m.created_at.isoformat(),
        } for m in reversed(list(msgs))]
 
    @database_sync_to_async
    def save_message(self, content):
        from .models import ChatRoom, Message
        room, _ = ChatRoom.objects.get_or_create(course_id=self.course_id)
        return Message.objects.create(room=room, sender=self.user, content=content)
 
    @database_sync_to_async
    def get_avatar_url(self):
        if self.user.avatar:
            return self.user.avatar.url
        return None
 
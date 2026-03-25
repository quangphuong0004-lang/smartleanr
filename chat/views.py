from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from courses.models import Course, Enrollment
 
 
class ChatHistoryView(APIView):
    permission_classes = [IsAuthenticated]
 
    def get(self, request, course_id):
        try:
            course = Course.objects.get(pk=course_id)
        except Course.DoesNotExist:
            return Response({'error': 'Không tìm thấy.'}, status=404)
 
        is_owner = course.teacher == request.user
        is_member = Enrollment.objects.filter(
            student=request.user, course=course, status='approved'
        ).exists()
 
        if not is_owner and not is_member:
            return Response({'error': 'Không có quyền.'}, status=403)
 
        from .models import ChatRoom, Message
        room, _ = ChatRoom.objects.get_or_create(course=course)
        msgs = Message.objects.filter(room=room).select_related('sender').order_by('-created_at')[:50]
 
        return Response([{
            'id':          str(m.id),
            'content':     m.content,
            'sender_id':   str(m.sender.id),
            'sender_name': m.sender.full_name or m.sender.username,
            'avatar_url':  request.build_absolute_uri(m.sender.avatar.url) if m.sender.avatar else None,
            'created_at':  m.created_at.isoformat(),
            'is_me':       m.sender == request.user,
        } for m in reversed(list(msgs))])
 
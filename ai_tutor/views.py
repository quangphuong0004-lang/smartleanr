from google import genai
import json
from django.conf import settings
from django.http import StreamingHttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import TutorSession, TutorMessage

 
SYSTEM_PROMPT = """Bạn là SmartLearn AI Tutor — trợ lý học tập thông minh.
Nhiệm vụ của bạn:
- Giải thích khái niệm một cách rõ ràng, dễ hiểu
- Hỗ trợ học sinh làm bài tập và ôn tập
- Khuyến khích tư duy phản biện
- Trả lời bằng tiếng Việt, ngắn gọn và súc tích
- Dùng ví dụ cụ thể, thực tế khi giải thích
- Nếu câu hỏi ngoài phạm vi học tập, lịch sự từ chối
 
Định dạng: dùng markdown khi cần (in đậm, danh sách, code block).
"""
 
 
class SessionListView(APIView):
    permission_classes = [IsAuthenticated]
 
    def get(self, request):
        sessions = TutorSession.objects.filter(user=request.user)[:20]
        return Response([{
            'id':         str(s.id),
            'title':      s.title,
            'course':     s.course.title if s.course else None,
            'updated_at': s.updated_at,
        } for s in sessions])
 
    def post(self, request):
        course_id = request.data.get('course_id')
        course    = None
        if course_id:
            from courses.models import Course
            try:
                course = Course.objects.get(pk=course_id)
            except Course.DoesNotExist:
                pass
 
        session = TutorSession.objects.create(
            user=request.user,
            course=course,
            title=request.data.get('title', 'Phiên mới'),
        )
        return Response({'id': str(session.id), 'title': session.title}, status=201)
 
 
class SessionDetailView(APIView):
    permission_classes = [IsAuthenticated]
 
    def get(self, request, session_id):
        try:
            session = TutorSession.objects.get(pk=session_id, user=request.user)
        except TutorSession.DoesNotExist:
            return Response({'error': 'Không tìm thấy.'}, status=404)
 
        messages = session.messages.all()
        return Response({
            'id':       str(session.id),
            'title':    session.title,
            'course':   session.course.title if session.course else None,
            'messages': [{'role': m.role, 'content': m.content, 'created_at': m.created_at} for m in messages],
        })
 
    def delete(self, request, session_id):
        try:
            session = TutorSession.objects.get(pk=session_id, user=request.user)
            session.delete()
            return Response({'message': 'Đã xóa phiên.'})
        except TutorSession.DoesNotExist:
            return Response({'error': 'Không tìm thấy.'}, status=404)
 
 
class ChatView(APIView):
    """POST: gửi tin nhắn, nhận phản hồi từ AI"""
    permission_classes = [IsAuthenticated]
 
    def post(self, request, session_id):
        try:
            session = TutorSession.objects.get(pk=session_id, user=request.user)
        except TutorSession.DoesNotExist:
            return Response({'error': 'Không tìm thấy phiên.'}, status=404)
 
        user_message = request.data.get('message', '').strip()
        if not user_message:
            return Response({'error': 'Vui lòng nhập câu hỏi.'}, status=400)
        if len(user_message) > 2000:
            return Response({'error': 'Tin nhắn quá dài (tối đa 2000 ký tự).'}, status=400)
 
        # Lưu tin nhắn của user
        TutorMessage.objects.create(session=session, role='user', content=user_message)
 
        # Cập nhật title phiên nếu là tin nhắn đầu tiên
        if session.messages.count() == 1:
            session.title = user_message[:60] + ('...' if len(user_message) > 60 else '')
            session.save()
 
        # Build messages history cho OpenAI
        history = list(session.messages.order_by('created_at'))
        openai_messages = [{'role': 'system', 'content': SYSTEM_PROMPT}]
 
        # Context từ khóa học nếu có
        if session.course:
            openai_messages[0]['content'] += f'\n\nKhóa học hiện tại: {session.course.title} — {session.course.subject or ""}'
 
        for m in history:
            openai_messages.append({'role': m.role, 'content': m.content})
 
        # Gọi OpenAI API
        try:
            if not settings.GEMINI_API_KEY:
                return Response({'error': 'Thiếu GEMINI_API_KEY'}, status=500)

            client = genai.Client(api_key=settings.GEMINI_API_KEY)

            prompt = SYSTEM_PROMPT + "\n\n"

            if session.course:
                prompt += f"Khóa học: {session.course.title} — {session.course.subject or ''}\n\n"

            for m in history:
                if m.role == "user":
                    prompt += f"User: {m.content}\n"
                else:
                    prompt += f"Assistant: {m.content}\n"

            response = client.models.generate_content(
                model="gemini-2.0-flash-lite",
                contents=prompt
            )

            ai_content = response.text or "Xin lỗi, tôi chưa trả lời được."

        except Exception as e:
            print("GEMINI ERROR:", e)
            ai_content = f'Xin lỗi, tôi đang gặp sự cố kỹ thuật. Vui lòng thử lại sau.\n\n_(Lỗi: {str(e)[:100]})_'
        # Lưu phản hồi AI
        ai_msg = TutorMessage.objects.create(session=session, role='assistant', content=ai_content)
 
        return Response({
            'message':    ai_content,
            'created_at': ai_msg.created_at,
            'session_title': session.title,
        })
 
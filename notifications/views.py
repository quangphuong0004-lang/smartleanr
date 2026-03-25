from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Notification
 
 
class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]
 
    def get(self, request):
        notifs = Notification.objects.filter(
            recipient=request.user
        ).order_by('-created_at')[:50]
 
        unread_count = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).count()
 
        data = [{
            'id': str(n.id),
            'type': n.type,
            'title': n.title,
            'message': n.message,
            'url': n.url,
            'is_read': n.is_read,
            'created_at': n.created_at,
        } for n in notifs]
 
        return Response({'notifications': data, 'unread_count': unread_count})
 
 
class NotificationReadView(APIView):
    permission_classes = [IsAuthenticated]
 
    def patch(self, request, pk):
        """Đánh dấu 1 notification là đã đọc"""
        try:
            n = Notification.objects.get(pk=pk, recipient=request.user)
            n.is_read = True
            n.save()
            return Response({'message': 'Đã đánh dấu đọc.'})
        except Notification.DoesNotExist:
            return Response({'error': 'Không tìm thấy.'}, status=404)
 
 
class NotificationReadAllView(APIView):
    permission_classes = [IsAuthenticated]
 
    def post(self, request):
        """Đánh dấu tất cả là đã đọc"""
        Notification.objects.filter(
            recipient=request.user, is_read=False
        ).update(is_read=True)
        return Response({'message': 'Đã đánh dấu tất cả là đã đọc.'})
 
 
class NotificationDeleteView(APIView):
    permission_classes = [IsAuthenticated]
 
    def delete(self, request, pk):
        try:
            n = Notification.objects.get(pk=pk, recipient=request.user)
            n.delete()
            return Response({'message': 'Đã xóa.'})
        except Notification.DoesNotExist:
            return Response({'error': 'Không tìm thấy.'}, status=404)
 
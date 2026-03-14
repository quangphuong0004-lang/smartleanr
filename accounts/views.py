from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import authenticate

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from datetime import timedelta

from .models import User, EmailVerificationToken, PasswordResetToken
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
)

#Tạo token cho user đăng nhập
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    refresh['role'] = user.role
    refresh['username'] = user.username
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }
  
#Đăng ký  
class RegisterView(APIView):
    permission_classes = [AllowAny] #cho phép mọi người truy cập api

    def post(self, request):
        serializer = RegisterSerializer(data=request.data) #Gửi data và serializer để kiểm tra
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()

        # Tạo token xác thực email (hết hạn sau 24h)
        token_obj = EmailVerificationToken.objects.create(
            user=user,
            expires_at=timezone.now() + timedelta(hours=24)
        )

        # Gửi email xác thực
        verify_url = f"{settings.FRONTEND_URL}/accounts/verify-email/{token_obj.token}/"
        send_mail(
            subject="[SmartLearn] Xác nhận tài khoản của bạn",
            message=(
                f"Xin chào {user.username},\n\n"
                f"Vui lòng click vào link sau để xác nhận email:\n{verify_url}\n\n"
                f"Link sẽ hết hạn sau 24 giờ.\n\nSmartLearn Team"
            ),
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
            fail_silently=True,
        )

        return Response(
            {
                "message": "Đăng ký thành công! Vui lòng kiểm tra email để xác nhận tài khoản.",
                "email": user.email,
            },
            status=status.HTTP_201_CREATED,
        )


#Xác thực email
class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, token):
        try:
            token_obj = EmailVerificationToken.objects.select_related('user').get(token=token) #Tìm token tương ứng
        except EmailVerificationToken.DoesNotExist:
            return Response(
                {"error": "Token không hợp lệ."}, status=status.HTTP_400_BAD_REQUEST
            )

        if not token_obj.is_valid():
            return Response(
                {"error": "Token đã hết hạn. Vui lòng đăng ký lại."}, status=status.HTTP_400_BAD_REQUEST
            )

        user = token_obj.user
        user.is_active = True #Cho phép login
        user.is_verified = True #Đánh dấu email đã xác thực
        user.save()
        token_obj.delete() #Xóa token sau khi dùng

        return Response(
            {"message": "Xác thực email thành công! Bạn có thể đăng nhập ngay bây giờ.",
             "email": user.email,
            },
            
            status=status.HTTP_200_OK,
        )
        

#Đăng nhập
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        #Lấy dữ liệu đã validate
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        #Kiểm tra user tồn tại
        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"error": "Email hoặc mật khẩu không đúng."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Kiểm tra đã xác thực email chưa
        if not user_obj.is_verified:
            return Response(
                {"error": "Tài khoản chưa được xác thực. Vui lòng kiểm tra email."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Xác thực mật khẩu
        user = authenticate(request, username=email, password=password)
        if not user:
            return Response(
                {"error": "Email hoặc mật khẩu không đúng."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        tokens = get_tokens_for_user(user)
        return Response(
            {
                "message": "Đăng nhập thành công!",
                "tokens": tokens,
                "user": UserProfileSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )


#Đăng xuất
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response(
                    {"error": "Refresh token là bắt buộc."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            token = RefreshToken(refresh_token)
            token.blacklist()  # Vô hiệu hóa token
            return Response({"message": "Đăng xuất thành công."}, status=status.HTTP_200_OK)
        except TokenError:
            return Response({"error": "Token không hợp lệ."}, status=status.HTTP_400_BAD_REQUEST)


#Refresh token
class TokenRefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"error": "Refresh token là bắt buộc."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            refresh = RefreshToken(refresh_token)
            return Response(
                {"access": str(refresh.access_token)},
                status=status.HTTP_200_OK,
            )
        except TokenError:
            return Response({"error": "Token không hợp lệ hoặc đã hết hạn."}, status=status.HTTP_401_UNAUTHORIZED)



#Hồ sơ cá nhân
class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser] #Cho phép nhận data dạng form + upload file

    def get(self, request):
        serializer = UserProfileSerializer(request.user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        serializer = UserProfileSerializer(
            request.user, data=request.data, partial=True, context={'request': request} #Cho phép update từng field
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(
            {"message": "Cập nhật hồ sơ thành công!", "user": serializer.data},
            status=status.HTTP_200_OK,
        )


#Đổi mật khẩu
class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        #Kiểm tra password cũ
        if not user.check_password(serializer.validated_data['old_password']):
            return Response(
                {"error": "Mật khẩu cũ không đúng."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        #hash + lưu mật khẩu mới
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({"message": "Đổi mật khẩu thành công!"}, status=status.HTTP_200_OK)


#Quên mật khẩu
class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']

        # Luôn trả về thông báo thành công dù email có tồn tại hay không
        # (bảo mật: không tiết lộ email nào đã đăng ký)
        try:
            user = User.objects.get(email=email, is_active=True)
            token_obj = PasswordResetToken.objects.create(
                user=user,
                expires_at=timezone.now() + timedelta(hours=1)
            )
            reset_url = f"{settings.FRONTEND_URL}/accounts/reset-password/?token={token_obj.token}"
            send_mail(
                subject="[SmartLearn] Đặt lại mật khẩu",
                message=(
                    f"Xin chào {user.username},\n\n"
                    f"Click vào link sau để đặt lại mật khẩu:\n{reset_url}\n\n"
                    f"Link hết hạn sau 1 giờ. Nếu bạn không yêu cầu, hãy bỏ qua email này.\n\nSmartLearn Team"
                ),
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[user.email],
                fail_silently=True,
            )
        except User.DoesNotExist:
            pass

        return Response(
            {"message": "Nếu email tồn tại, chúng tôi đã gửi link đặt lại mật khẩu."},
            status=status.HTTP_200_OK,
        )


#Đặt lại mật khẩu
class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            token_obj = PasswordResetToken.objects.select_related('user').get(
                token=serializer.validated_data['token']
            )
        except PasswordResetToken.DoesNotExist:
            return Response({"error": "Token không hợp lệ."}, status=status.HTTP_400_BAD_REQUEST)

        if not token_obj.is_valid():
            return Response({"error": "Token đã hết hạn hoặc đã được sử dụng."}, status=status.HTTP_400_BAD_REQUEST)

        user = token_obj.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()

        token_obj.is_used = True
        token_obj.save()

        return Response({"message": "Đặt lại mật khẩu thành công! Bạn có thể đăng nhập ngay."}, status=status.HTTP_200_OK)

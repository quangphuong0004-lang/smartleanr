from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password] #Chỉ nhận input, không trả response, bắt buộc nhập, password đảm bảo đạt chuẩn django
    )
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['email', 'username', 'full_name', 'password', 'password2', 'role']
        extra_kwargs = {
            'full_name': {'required': False},
            'role': {'required': False},
        } #Field không bắt buộc

    def validate(self, attrs):#Kiểm tra trùng khớp password
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Mật khẩu không khớp."})

        # Không cho phép tự đăng ký role admin
        if attrs.get('role') == 'admin':
            raise serializers.ValidationError({"role": "Không thể đăng ký role admin."})

        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')#Loại password 2 khỏi database
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password) #hash password
        user.is_active = False   # Chờ xác thực email
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class UserProfileSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'full_name',
            'avatar', 'avatar_url', 'bio', 'role',
            'is_verified', 'created_at'
        ]
        read_only_fields = ['id', 'email', 'role', 'is_verified', 'created_at'] # Các field chỉ đọc, không update

    def get_avatar_url(self, obj):
        return obj.get_avatar_url()


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password2 = serializers.CharField(write_only=True)

    def validate(self, attrs): #Kiểm tra 2 password có giống nhau không
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password": "Mật khẩu mới không khớp."})
        return attrs


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password2 = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password": "Mật khẩu không khớp."})
        return attrs
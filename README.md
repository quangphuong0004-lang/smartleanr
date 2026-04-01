SmartLearn — Nền tảng học tập thông minh
Ứng dụng web học tập trực tuyến, chat thời gian thực, quiz kiểm tra và dashboard theo dõi tiến độ.
________________________________________
Công nghệ sử dụng
Backend
•	Python 3.11+ / Django 4.2
•	Django REST Framework — REST API
•	djangorestframework-simplejwt — Xác thực JWT
•	Django Channels + Redis — WebSocket (chat real-time)
•	MySQL — Cơ sở dữ liệu
•	qrcode[pil] — Tạo mã QR
Frontend
•	HTML / CSS / JavaScript thuần
•	Font: Be Vietnam Pro
•	Design system tùy chỉnh (base.css)
________________________________________
Cài đặt
1. Clone & tạo môi trường ảo
git clone <repo-url>
cd smartlearn
python -m venv venv
#Windows: venv\Scripts\activate
2. Cài dependencies
pip install django djangorestframework djangorestframework-simplejwt
pip install channels channels-redis
pip install mysqlclient
pip install qrcode[pil]
pip install django-cors-headers
3. Cấu hình .env / settings.py
# settings.py
SECRET_KEY = 'your-secret-key'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'smartlearn',
        'USER': 'root',
        'PASSWORD': 'yourpassword',
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {'charset': 'utf8mb4'},
    }
}

OPENAI_API_KEY = 'sk-...'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {'hosts': [('127.0.0.1', 6379)]},
    }
}

FRONTEND_URL = 'http://localhost:8000'
4. Tạo database & migrate
mysql -u root -p -e "CREATE DATABASE smartlearn CHARACTER SET utf8mb4;"
python manage.py makemigrations
python manage.py migrate
5. Tạo superuser
python manage.py createsuperuser
6. Chạy Redis (cần cho WebSocket chat)
# Docker
docker run -p 6379:6379 redis

# Hoặc cài trực tiếp và chạy
redis-server
7. Chạy server
python manage.py runserver
Truy cập: http://localhost:8000
________________________________________
Cấu trúc dự án
smartlearn/
├── smartlearn/          # Cấu hình Django (settings, urls, asgi)
├── accounts/            # Xác thực người dùng
├── courses/             # Khóa học & bài học
├── quizzes/             # Bài kiểm tra
├── dashboard/           # Dashboard thống kê
├── notifications/       # Hệ thống thông báo
├── chat/                # Chat real-time (WebSocket)
├── ai_tutor/            # AI Tutor (OpenAI)
├── static/
│   ├── css/base.css     # Design system
│   └── js/auth.js       # Auth utilities & navbar
└── templates/
    ├── accounts/        # Đăng nhập, đăng ký, hồ sơ
    ├── courses/         # Khóa học, bài học
    ├── quizzes/         # Quiz, làm bài, kết quả
    ├── dashboard/       # Dashboard
    ├── chat/            # Phòng chat
    ├── ai_tutor/        # AI Tutor – (phát triển thêm)
    └── notifications/   # Thông báo
________________________________________
Tính năng
Người dùng
Role	Mô tả
student	Đăng ký khóa học, học bài, làm quiz, chat.
teacher	Tạo khóa học, bài học, quiz, quản lý học sinh
admin	Toàn quyền
Accounts
•	Đăng ký → xác thực email → đăng nhập
•	JWT access token (60 phút) + refresh token (7 ngày)
•	Chỉnh sửa hồ sơ, upload avatar, đổi mật khẩu
•	Quên mật khẩu qua email
Courses
•	Tạo/sửa/xóa khóa học (thumbnail, môn học, cấp độ)
•	Bài học text + video YouTube embed
•	Đăng ký khóa học bằng mã 8 ký tự hoặc quét QR
•	Theo dõi tiến độ từng bài học
•	Chat phòng học theo từng khóa
Quizzes
•	Trắc nghiệm 1 đáp án đúng, có thể giới hạn thời gian
•	Đồng hồ đếm ngược khi làm bài
•	Kết quả chi tiết: xem lại đáp án đúng/sai, điểm số
•	Bảng xếp hạng cho giáo viên
Dashboard
•	Student: tiến độ từng khóa, streak học tập, điểm quiz, hoạt động gần đây
•	Teacher: tổng số học sinh, hiệu suất quiz, yêu cầu chờ duyệt
Chat
•	WebSocket real-time qua Django Channels
•	Lịch sử 30 tin nhắn khi vào phòng
•	Mini chat panel ngay trên trang khóa học
Notifications
•	Thông báo tự động: duyệt đăng ký, bài học mới, quiz mới
•	Chuông thông báo trên navbar, badge số chưa đọc
•	Poll tự động mỗi 30 giây
________________________________________
API chính
Method	Endpoint	Mô tả
POST	/accounts/api/register/	Đăng ký
POST	/accounts/api/login/	Đăng nhập
GET/PATCH	/accounts/api/profile/	Hồ sơ
GET	/courses/api/	Danh sách khóa học
POST	/courses/api/join/	Tham gia bằng mã
GET	/courses/api/<id>/lessons/	Danh sách bài học
POST	/courses/api/<id>/lessons/<id>/complete/	Hoàn thành bài
POST	/api/courses/<id>/quizzes/<id>/start/	Bắt đầu quiz
POST	/api/courses/<id>/quizzes/<id>/attempts/<id>/submit/	Nộp bài
GET	/dashboard/api/	Dữ liệu dashboard
GET	/api/notifications/	Thông báo
POST	/api/ai-tutor/sessions/<id>/chat/	Hỏi AI
WS	ws://localhost:8000/ws/chat/<course_id>/	Chat WebSocket
________________________________________
Biến môi trường cần thiết
SECRET_KEY=
DB_NAME=smartlearn
DB_USER=
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=3306
OPENAI_API_KEY=
REDIS_URL=redis://localhost:6379
FRONTEND_URL=http://localhost:8000
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
________________________________________
Yêu cầu hệ thống
•	Python 3.11+
•	MySQL 8.0+
•	Redis 6.0+

# 🚀 Web243 - Hệ Thống Quản Lý Cửa Hàng Trực Tuyến

## 📋 Mô Tả Dự Án

Web243 là một hệ thống quản lý cửa hàng trực tuyến hoàn chỉnh với các tính năng:
- **Quản lý sản phẩm** - Thêm, sửa, xóa sản phẩm
- **Quản lý bài viết** - Hệ thống blog với upload ảnh
- **Quản lý người dùng** - Đăng ký, đăng nhập, phân quyền
- **Hệ thống thanh toán** - Nạp tiền, mua hàng, lịch sử giao dịch
- **Admin Panel** - Giao diện quản trị chuyên nghiệp
- **Responsive Design** - Tương thích mọi thiết bị

## 👥 Thành Viên Nhóm

| STT | Họ và Tên | MSSV | Vai Trò |
|-----|------------|------|---------|
| 1 | **Trần Quang Vinh** | 2374802010564 | Frontend Developer & UI/UX & Backend Developer & Database | 100% |
| 2 | **Nguyễn Thanh Sơn** | 2374802010436 | Slide Canva | 5% |

## 🛠️ Công Nghệ Sử Dụng

### Backend
- **Python 3.8+** - Ngôn ngữ lập trình chính
- **Flask** - Web framework
- **MongoDB Atlas** - Cloud database
- **PyMongo** - MongoDB driver
- **Flask-JWT-Extended** - Authentication
- **Flask-CORS** - Cross-origin resource sharing

### Frontend
- **HTML5** - Cấu trúc trang web
- **CSS3** - Styling và responsive design
- **JavaScript (ES6+)** - Tương tác client-side
- **Bootstrap 5** - UI framework
- **Bootstrap Icons** - Icon library

### Database
- **MongoDB Atlas** - Cloud NoSQL database
- **Collections**: users, products, articles, orders, transactions

## 📦 Cài Đặt Môi Trường

### 1. Cài Đặt Python

```bash
# Kiểm tra Python version (yêu cầu 3.8+)
python --version

# Nếu chưa có Python, tải từ: https://python.org
```

### 2. Clone Repository

```bash
# Clone project về máy
git clone <repository-url>
cd web243
```

### 3. Tạo Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 4. Cài Đặt Dependencies

```bash
# Cài đặt các thư viện cần thiết
pip install -r requirements.txt
```

### 5. Cấu Hình Database

```bash
# Tạo file .env (nếu cần)
# MongoDB Atlas connection string đã được cấu hình sẵn trong app.py
```

## 🚀 Khởi Chạy Ứng Dụng

### 1. Khởi Động Backend

```bash
# Cách 1: Chạy trực tiếp
python app.py

# Cách 2: Sử dụng script (Windows)
start_backend.bat

# Cách 3: Chạy với debug mode
python app.py --debug
```

Backend sẽ chạy tại: `http://localhost:5000`

### 2. Khởi Động Frontend

```bash
# Sử dụng Live Server (VS Code extension)
# Hoặc mở trực tiếp file HTML trong browser

# Cách 1: Mở file index.html
# Cách 2: Sử dụng Python HTTP server
python -m http.server 5500
```

Frontend sẽ chạy tại: `http://localhost:5500`

### 3. Truy Cập Ứng Dụng

| Trang | URL | Mô Tả |
|-------|-----|-------|
| **Trang Chủ** | `http://localhost:5500/index.html` | Giao diện chính |
| **Đăng Nhập** | `http://localhost:5500/login.html` | Trang đăng nhập |
| **Admin Panel** | `http://localhost:5500/admin.html` | Quản trị hệ thống |
| **Quản Lý Bài Viết** | `http://localhost:5500/baiviet.html` | CRUD bài viết |
| **Hiển Thị Bài Viết** | `http://localhost:5500/baiviet_action.html` | Xem bài viết |

## 📁 Cấu Trúc Thư Mục

```
web243/
├── 📄 app.py                 # Backend Flask server
├── 📄 server.js              # Node.js server (backup)
├── 📄 requirements.txt       # Python dependencies
├── 📄 start_backend.bat     # Script khởi động (Windows)
├── 📁 uploads/              # Thư mục upload files
│   └── 📁 img_post/         # Ảnh bài viết
├── 📁 css/                  # Stylesheets
├── 📁 img/                  # Static images
└── 📄 *.html               # Frontend pages
```

## 🔧 Cấu Hình Database

### MongoDB Atlas Connection
```python
# Trong app.py
client = MongoClient("mongodb+srv://admin:971012@admin.7oi2tx6.mongodb.net/?retryWrites=true&w=majority&appName=admin")
db = client.web243
```

### Collections
- `users` - Thông tin người dùng
- `products` - Sản phẩm
- `articles` - Bài viết
- `orders` - Đơn hàng
- `transactions` - Giao dịch
- `categories` - Danh mục

## 🔐 Authentication

### JWT Token
- **Access Token**: 1 giờ
- **Refresh Token**: 7 ngày
- **Algorithm**: HS256

### User Roles
- **Admin**: Quản trị toàn bộ hệ thống
- **User**: Khách hàng mua hàng

## 📱 Tính Năng Chính

### 1. Quản Lý Bài Viết
- ✅ Thêm, sửa, xóa bài viết
- ✅ Upload ảnh với preview
- ✅ Markdown support
- ✅ Trạng thái: Draft/Published
- ✅ Thống kê lượt xem

### 2. Quản Lý Sản Phẩm
- ✅ CRUD sản phẩm
- ✅ Upload ảnh sản phẩm
- ✅ Phân loại danh mục
- ✅ Quản lý giá cả

### 3. Hệ Thống Thanh Toán
- ✅ Nạp tiền qua thẻ
- ✅ Mua hàng online
- ✅ Lịch sử giao dịch
- ✅ Quản lý ví điện tử

### 4. Admin Panel
- ✅ Dashboard thống kê
- ✅ Quản lý người dùng
- ✅ Quản lý đơn hàng
- ✅ Báo cáo doanh thu

## 🐛 Troubleshooting

### Lỗi Thường Gặp

#### 1. "Failed to fetch"
```bash
# Kiểm tra backend có chạy không
curl http://localhost:5000/api/test

# Kiểm tra CORS
# Đảm bảo frontend và backend cùng domain
```

#### 2. "Database không khả dụng"
```bash
# Kiểm tra kết nối MongoDB Atlas
# Kiểm tra internet connection
# Kiểm tra connection string trong app.py
```

#### 3. "Upload ảnh thất bại"
```bash
# Kiểm tra thư mục uploads/img_post/
# Kiểm tra quyền ghi file
# Kiểm tra dung lượng ổ cứng
```

### Debug Mode
```bash
# Chạy với debug logs
python app.py --debug

# Xem logs chi tiết trong terminal
```

## 📊 API Endpoints

### Articles
- `GET /api/articles` - Lấy danh sách bài viết
- `POST /api/articles` - Tạo bài viết mới
- `PUT /api/articles/<id>` - Cập nhật bài viết
- `DELETE /api/articles/<id>` - Xóa bài viết
- `POST /api/upload-image` - Upload ảnh

### Users
- `POST /api/register` - Đăng ký
- `POST /api/login` - Đăng nhập
- `GET /api/users` - Lấy danh sách users

### Products
- `GET /api/products` - Lấy danh sách sản phẩm
- `POST /api/products` - Tạo sản phẩm mới
- `PUT /api/products/<id>` - Cập nhật sản phẩm
- `DELETE /api/products/<id>` - Xóa sản phẩm

## 🤝 Đóng Góp

### Quy Trình Development
1. **Fork** repository
2. **Tạo branch** mới: `git checkout -b feature/new-feature`
3. **Commit** thay đổi: `git commit -m 'Add new feature'`
4. **Push** lên branch: `git push origin feature/new-feature`
5. **Tạo Pull Request**

### Coding Standards
- **Python**: PEP 8
- **JavaScript**: ESLint
- **HTML**: W3C Validator
- **CSS**: Prettier

## 📄 License

Dự án này được phát triển cho mục đích học tập và nghiên cứu.

## 📞 Liên Hệ

- **Trần Quang Vinh**: vinh.tq@example.com
- **Nguyễn Thanh Sơn**: son.nt@example.com

---

## 🎯 Roadmap

### Phase 1 ✅ (Hoàn thành)
- [x] Setup project structure
- [x] Basic CRUD operations
- [x] User authentication
- [x] File upload system

### Phase 2 🔄 (Đang phát triển)
- [ ] Payment integration
- [ ] Email notifications
- [ ] Advanced search
- [ ] Mobile app

### Phase 3 📋 (Kế hoạch)
- [ ] Real-time chat
- [ ] Analytics dashboard
- [ ] Multi-language support
- [ ] API documentation

---

**Made with ❤️ by TranQuangVinh** 

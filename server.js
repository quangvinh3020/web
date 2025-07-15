const express = require("express");
const mongoose = require("mongoose");
const cors = require("cors");
const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");
const app = express();

app.use(cors());
app.use(express.json());

// Thay chuỗi bên dưới bằng chuỗi kết nối MongoDB Atlas của bạn
const uri = "mongodb+srv://admin:0123Cam0123%40@admin.7oi2tx6.mongodb.net/?retryWrites=true&w=majority&appName=admin";

// Kết nối MongoDB
mongoose.connect(uri, {
  useNewUrlParser: true,
  useUnifiedTopology: true,
}).then(() => console.log("✅ MongoDB Connected"))
  .catch(err => console.error("❌ MongoDB Connection Error:", err));

// Schema người dùng
const User = mongoose.model("User", new mongoose.Schema({
  username: { type: String, required: true, unique: true },
  password: { type: String, required: true },
  role: { type: String, required: true, enum: ['Admin', 'User'] }  // Thêm trường role
}));

// API Đăng nhập
app.post("/api/login", async (req, res) => {
  const { username, password } = req.body;

  try {
    const user = await User.findOne({ username });
    if (!user) {
      return res.status(401).json({ message: "Tài khoản không tồn tại" });
    }

    // Kiểm tra mật khẩu
    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) {
      return res.status(401).json({ message: "Sai tài khoản hoặc mật khẩu" });
    }

    // Tạo token JWT
    const token = jwt.sign({ userId: user._id, username: user.username, role: user.role }, 'your_jwt_secret', { expiresIn: '1h' });
    res.json({ message: "Đăng nhập thành công", token, role: user.role });
  } catch (error) {
    console.error(error);
    res.status(500).json({ message: "Lỗi hệ thống, vui lòng thử lại sau." });
  }
});

// Middleware kiểm tra xác thực JWT
const authenticateJWT = (req, res, next) => {
  const token = req.header('Authorization')?.split(' ')[1]; // Lấy token từ header

  if (!token) {
    return res.status(403).json({ message: "Không có quyền truy cập" });
  }

  jwt.verify(token, 'your_jwt_secret', (err, decoded) => {
    if (err) {
      return res.status(403).json({ message: "Lỗi xác thực token" });
    }
    req.user = decoded;  // Lưu thông tin người dùng vào request
    next();
  });
};

// Middleware kiểm tra quyền Admin
const checkAdmin = (req, res, next) => {
  if (req.user.role !== 'Admin') {
    return res.status(403).json({ message: "Bạn không có quyền truy cập trang Admin" });
  }
  next();
};

// Route dành cho Admin, chỉ cho phép Admin truy cập
app.get("/api/admin", authenticateJWT, checkAdmin, (req, res) => {
  res.json({ message: "Chào mừng Admin đến với trang quản lý!" });
});

// API Đăng ký
app.post("/api/register", async (req, res) => {
  const { username, password, role } = req.body;  // Lấy username, password và role từ request

  try {
    // Kiểm tra tài khoản đã tồn tại
    const existing = await User.findOne({ username });
    if (existing) {
      return res.status(400).json({ message: "Tài khoản đã tồn tại" });
    }

    // Mã hóa mật khẩu trước khi lưu vào cơ sở dữ liệu
    const hashedPassword = await bcrypt.hash(password, 10);

    // Nếu không có role, mặc định là "User" (hoặc bạn có thể thay đổi theo yêu cầu)
    const userRole = role || "User";  // Gán role mặc định là "User" nếu không có role

    // Tạo và lưu người dùng mới
    const user = new User({ username, password: hashedPassword, role: userRole });
    await user.save();

    res.json({ message: "Đăng ký thành công" });
  } catch (error) {
    console.error(error);
    res.status(500).json({ message: "Lỗi hệ thống, vui lòng thử lại sau." });
  }
});

app.listen(3000, () => console.log("🚀 Server chạy tại http://localhost:3000"));

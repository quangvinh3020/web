const Category = require("./models/Category");
const Product = require("./models/Product");
const express = require("express");
const mongoose = require("mongoose");
const cors = require("cors");
const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");
const Transaction = require("./models/Transaction");  // Import Transaction model
const multer = require('multer');
const upload = multer({ dest: 'uploads/' });
const path = require('path');
const axios = require('axios');
const crypto = require('crypto');
const fs = require('fs');
const Order = require("./models/Order");
const TopupCard = require('./models/TopupCard');
const WalletTopup = require('./models/WalletTopup');

// Thông tin test lấy từ https://developers.momo.vn
const partnerCode = 'MOMO...';      // Thay bằng mã test của bạn
const accessKey = '...';
const secretKey = '...';
const endpoint = 'https://test-payment.momo.vn/v2/gateway/api/create';

// Khởi tạo app và middleware
const app = express();
app.use(cors());
app.use(express.json());

// Route tạo đơn hàng Momo ảo
app.post('/api/momo/create', async (req, res) => {
  const { amount, username } = req.body;
  const orderId = 'ORDER' + Date.now();
  const requestId = orderId + Math.floor(Math.random() * 1000);
  const orderInfo = `Nạp ví cho user ${username}`;
  const redirectUrl = 'http://localhost:3000/vidientu.html'; // Sau khi thanh toán xong sẽ về đây
  const ipnUrl = 'http://localhost:3000/api/momo/ipn'; // Địa chỉ nhận notify từ Momo

  // Tạo signature
  const rawSignature = `accessKey=${accessKey}&amount=${amount}&extraData=&ipnUrl=${ipnUrl}&orderId=${orderId}&orderInfo=${orderInfo}&partnerCode=${partnerCode}&redirectUrl=${redirectUrl}&requestId=${requestId}&requestType=captureWallet`;
  const signature = crypto.createHmac('sha256', secretKey)
    .update(rawSignature)
    .digest('hex');

  const body = {
    partnerCode,
    accessKey,
    requestId,
    amount: amount.toString(),
    orderId,
    orderInfo,
    redirectUrl,
    ipnUrl,
    extraData: '',
    requestType: 'captureWallet',
    signature
  };

  try {
    const response = await axios.post(endpoint, body);
    // Trả về payUrl cho client redirect sang Momo ảo
    res.json({ payUrl: response.data.payUrl });
  } catch (err) {
    res.status(500).json({ message: 'Lỗi tạo đơn hàng Momo', error: err.message });
  }
});

// Kết nối MongoDB
const uri = "mongodb+srv://admin:971012@admin.7oi2tx6.mongodb.net/?retryWrites=true&w=majority&appName=admin";

mongoose.connect(uri, {
  useNewUrlParser: true,
  useUnifiedTopology: true,
}).then(() => console.log("✅ MongoDB Connected"))
  .catch(err => console.error("❌ MongoDB Connection Error:", err));

// Schema người dùng (✅ Đã thêm balance)
const User = mongoose.model("User", new mongoose.Schema({
  email: { type: String, required: true, unique: true },
  username: { type: String, required: true, unique: true },
  password: { type: String, required: true },
  role: { type: String, required: true, enum: ['Admin', 'User'] },
  balance: { type: Number, default: 0 },
  totalTopup: { type: Number, default: 0 } // Thêm trường tổng nạp
}));

// API Đăng ký
app.post("/api/register", async (req, res) => {
  const { email, username, password } = req.body;

  try {
    // Kiểm tra xem tài khoản đã tồn tại chưa
    const existingUser = await User.findOne({ username });
    if (existingUser) {
      return res.status(400).json({ message: "Tài khoản đã tồn tại!" });
    }

    // Băm mật khẩu trước khi lưu vào cơ sở dữ liệu
    const hashedPassword = await bcrypt.hash(password, 10);

    // Tạo người dùng mới
    const newUser = new User({
      email,
      username,
      password: hashedPassword,
      role: "User", // Mặc định là User
      balance: 0, // Số dư mặc định
      totalTopup: 0 // Thêm trường tổng nạp vào khi đăng ký
    });

    // Lưu người dùng vào cơ sở dữ liệu
    await newUser.save();
    
    res.json({ message: "Đăng ký thành công!" });
  } catch (err) {
    console.error(err);
    res.status(500).json({ message: "Lỗi hệ thống, vui lòng thử lại sau." });
  }
});

// API Đăng nhập
app.post("/api/login", async (req, res) => {
  const { username, password } = req.body;

  try {
    // Tìm người dùng trong cơ sở dữ liệu theo username
    const user = await User.findOne({ username });
    if (!user) {
      return res.status(401).json({ message: "Tài khoản không tồn tại" });
    }

    // Kiểm tra mật khẩu bằng cách so sánh mật khẩu người dùng nhập vào với mật khẩu đã băm
    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) {
      return res.status(401).json({ message: "Sai tài khoản hoặc mật khẩu" });
    }

    // Tạo JWT token cho người dùng
    const token = jwt.sign(
      { userId: user._id, username: user.username, role: user.role },
      'your_jwt_secret',  // Sử dụng khóa bí mật của bạn
      { expiresIn: '1h' }  // Token có hiệu lực trong 1 giờ
    );

    // Trả về thông tin người dùng cùng với token
    res.json({
      message: "Đăng nhập thành công",
      token,  // Trả về token cho người dùng
      role: user.role,
      username: user.username,
      balance: user.balance,  // Trả về số dư người dùng
      totalTopup: user.totalTopup  // Trả về tổng nạp người dùng
    });
  } catch (error) {
    console.error(error);
    res.status(500).json({ message: "Lỗi hệ thống, vui lòng thử lại sau." });
  }
});

// Middleware xác thực
const authenticateJWT = (req, res, next) => {
  const token = req.header('Authorization')?.split(' ')[1];
  if (!token) return res.status(403).json({ message: "Không có quyền truy cập" });

  jwt.verify(token, 'your_jwt_secret', (err, decoded) => {
    if (err) return res.status(403).json({ message: "Lỗi xác thực token" });
    req.user = decoded;
    next();
  });
};

// API cập nhật số dư người dùng và lưu giao dịch
app.post("/api/user/:username/update-balance", authenticateJWT, async (req, res) => {
  const { amount, type, description } = req.body;

  try {
    const user = await User.findOne({ username: req.params.username });
    if (!user) return res.status(404).json({ message: "Không tìm thấy người dùng" });

    if (req.user.username !== user.username && req.user.role !== 'Admin') {
      return res.status(403).json({ message: "Bạn không có quyền cập nhật số dư của người khác." });
    }

    // Cập nhật số dư người dùng và tổng nạp
    if (type === "add") {
      user.balance += amount;
      user.totalTopup += amount;
    } else if (type === "subtract") {
      user.balance -= amount;
      if (user.balance < 0) user.balance = 0;
    }

    await user.save();

    // Lưu lịch sử giao dịch
    const transaction = new Transaction({
      userId: user._id,
      amount,
      transactionType: type,
      adminId: req.user.userId,
      description: description || "Cập nhật số dư",
    });

    await transaction.save();

    // Trả về số dư mới cho client
    res.json({
      message: "Cập nhật số dư thành công",
      balance: user.balance,  // Trả về số dư mới
      totalTopup: user.totalTopup
    });

  } catch (err) {
    console.error("Lỗi khi cập nhật số dư:", err);
    res.status(500).json({ message: "Lỗi khi cập nhật số dư", error: err });
  }
});

// Lấy lịch sử giao dịch của người dùng
app.get("/api/user/:username/transactions", authenticateJWT, async (req, res) => {
  try {
    const user = await User.findOne({ username: req.params.username });
    if (!user) return res.status(404).json({ message: "Không tìm thấy người dùng" });

    // Kiểm tra nếu người dùng yêu cầu lấy lịch sử giao dịch của chính mình
    if (req.user.username !== user.username && req.user.role !== 'Admin') {
      return res.status(403).json({ message: "Bạn không có quyền xem lịch sử giao dịch của người khác." });
    }

    const transactions = await Transaction.find({ userId: user._id }).populate("adminId", "username");
    res.json(transactions);  // Trả về lịch sử giao dịch
  } catch (err) {
    console.error(err);
    res.status(500).json({ message: "Lỗi khi lấy lịch sử giao dịch" });
  }
});

// Lấy tất cả người dùng (Admin)
app.get("/api/users", authenticateJWT, async (req, res) => {
  try {
    // Chỉ admin mới có quyền truy cập tất cả người dùng
    if (req.user.role !== 'Admin') {
      return res.status(403).json({ message: "Không có quyền truy cập" });
    }
    
    const users = await User.find({});
    res.json(users);
  } catch (err) {
    res.status(500).json({ message: "Lỗi server" });
  }
});

// Xóa người dùng (Admin)
app.delete("/api/user/:username", authenticateJWT, async (req, res) => {
  try {
    if (req.user.role !== 'Admin') {
      return res.status(403).json({ message: "Bạn không có quyền xóa người dùng" });
    }

    const deleted = await User.findOneAndDelete({ username: req.params.username });
    if (!deleted) return res.status(404).json({ message: "Không tìm thấy user" });
    res.json({ message: "Xoá thành công" });
  } catch (err) {
    res.status(500).json({ message: "Lỗi server khi xoá" });
  }
});

// Lấy lịch sử mua hàng của người dùng
app.get("/api/user/:username/purchases", authenticateJWT, async (req, res) => {
  try {
    const user = await User.findOne({ username: req.params.username });
    if (!user) return res.status(404).json({ message: "Không tìm thấy người dùng" });
    if (req.user.username !== user.username && req.user.role !== 'Admin') {
      return res.status(403).json({ message: "Bạn không có quyền xem lịch sử mua hàng của người khác." });
    }
    const orders = await Order.find({ userId: user._id }).populate("productId", "name price");
    const result = orders.map(o => ({
      productName: o.productId.name,
      price: o.price,
      createdAt: o.createdAt
    }));
    res.json(result);
  } catch (err) {
    console.error(err);
    res.status(500).json({ message: "Lỗi khi lấy lịch sử mua hàng" });
  }
});

// Cập nhật số dư ngay lập tức sau khi giao dịch
function updateBalance(username, amount, type, description) {
  const token = localStorage.getItem("token");

  // Gửi yêu cầu cập nhật số dư đến server
  fetch(`http://localhost:3000/api/user/${username}/update-balance`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${token}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ amount, type, description })
  })
  .then(response => response.json())
  .then(data => {
  console.log(data);  // Kiểm tra dữ liệu trả về từ API
  if (data.message === "Cập nhật số dư thành công") {
    localStorage.setItem("balance", data.balance);  // Lưu số dư mới vào localStorage
    document.getElementById("balance-display").textContent = `${Number(data.balance).toLocaleString()} ₫`;  // Cập nhật số dư trên giao diện
    alert("Cập nhật số dư thành công!");
  } else {
    alert("Cập nhật số dư thất bại!");
  }
})
  .catch(error => {
    console.error("Lỗi khi cập nhật số dư:", error);
    alert("Lỗi khi cập nhật số dư!");
  });
}

app.get("/api/user/:username/balance", authenticateJWT, async (req, res) => {
  try {
    const user = await User.findOne({ username: req.params.username });
    if (!user) return res.status(404).json({ message: "Không tìm thấy người dùng" });

    // Trả về số dư người dùng
    res.json({ balance: user.balance });
  } catch (err) {
    console.error(err);
    res.status(500).json({ message: "Lỗi hệ thống khi lấy số dư." });
  }
});
// API tạo danh mục (trong server)
app.post('/api/categories', async (req, res) => {
  const { name, order, status } = req.body;

  const newCategory = new Category({
    name,
    order,
    status,
  });

  try {
    await newCategory.save();
    res.status(201).json(newCategory);
  } catch (err) {
    res.status(400).json({ message: 'Không thể tạo danh mục', error: err.message });
  }
});


// Lấy danh sách danh mục
app.get('/api/categories', async (req, res) => {
  const categories = await Category.find({});
  res.json(categories);
});

// Thêm danh mục mới
app.post('/api/categories', async (req, res) => {
  const { name } = req.body;
  if (!name) return res.status(400).json({ error: 'Tên danh mục là bắt buộc' });
  try {
    const newCategory = new Category({ name });
    await newCategory.save();
    res.json(newCategory);
  } catch (err) {
    res.status(400).json({ error: 'Danh mục đã tồn tại hoặc lỗi khác.' });
  }
});

// Lấy danh sách sản phẩm
app.get('/api/products', async (req, res) => {
  const products = await Product.find({}).populate('categoryId', 'name');
  res.json(products);
});

// Thêm sản phẩm mới
app.post('/api/products', upload.single('image'), async (req, res) => {
  const { name, price, categoryId, sale, linkDemo, linkTai, nameKey, content } = req.body;
  // Lấy đường dẫn file ảnh vừa upload
  const image = req.file ? `/uploads/${req.file.filename}` : null;

  if (!name || !price || !categoryId) return res.status(400).json({ error: 'Thiếu thông tin sản phẩm' });
  try {
    const newProduct = new Product({
      name,
      price,
      categoryId,
      image, // Lưu đường dẫn ảnh
      sale,
      linkDemo,
      linkTai,
      nameKey,
      content
    });
    await newProduct.save();
    res.json(newProduct);
  } catch (err) {
    res.status(400).json({ error: 'Lỗi khi thêm sản phẩm.' });
  }
});
app.delete('/api/categories/:id', async (req, res) => {
  try {
    // Lấy tất cả sản phẩm thuộc danh mục này
    const products = await Product.find({ categoryId: req.params.id });
    // Xóa file ảnh của từng sản phẩm
    products.forEach(prod => {
      if (prod.image && prod.image.startsWith('/uploads/')) {
        const filePath = path.join(__dirname, prod.image);
        fs.unlink(filePath, err => {
          // Không cần xử lý lỗi nếu file không tồn tại
        });
      }
    });
    // Xóa tất cả sản phẩm thuộc danh mục này
    await Product.deleteMany({ categoryId: req.params.id });
    // Xóa danh mục
    const deleted = await Category.findByIdAndDelete(req.params.id);
    if (!deleted) return res.status(404).json({ message: "Không tìm thấy danh mục" });
    res.json({ message: "Xóa thành công" });
  } catch (err) {
    res.status(500).json({ message: "Lỗi khi xóa danh mục", error: err });
  }
});

app.post('/api/buy', authenticateJWT, async (req, res) => {
  const { productId } = req.body;
  const userId = req.user.userId;
  try {
    const user = await User.findById(userId);
    const product = await Product.findById(productId);
    if (!user || !product) return res.status(404).json({ message: 'Không tìm thấy user hoặc sản phẩm' });
    if (user.balance < product.price) return res.status(400).json({ message: 'Số dư không đủ' });
    // Trừ tiền
    user.balance -= product.price;
    await user.save();
    // Lưu đơn hàng
    const order = new Order({ userId, productId, price: product.price });
    await order.save();
    res.json({ message: 'Mua sản phẩm thành công!' });
  } catch (err) {
    console.error(err);
    res.status(500).json({ message: 'Lỗi khi mua sản phẩm' });
  }
});

app.post('/api/momo/ipn', (req, res) => {
  // Momo sẽ gửi thông tin giao dịch về đây
  // Bạn kiểm tra signature, trạng thái, sau đó cộng tiền cho user
  // Ví dụ:
  const { orderId, resultCode, amount } = req.body;
  if (resultCode === 0) {
    // Thành công: cập nhật số dư cho user tương ứng với orderId
    // ... (tùy bạn xử lý)
  }
  res.status(200).send('OK');
});
app.use('/uploads', express.static('uploads'));
// Chạy server
app.listen(3000, () => console.log("🚀 Server chạy tại http://localhost:3000"));

// Nạp thẻ cào
app.post('/api/topup-card', authenticateJWT, async (req, res) => {
  const { cardType, amount, serial, code } = req.body;
  try {
    const topup = new TopupCard({
      userId: req.user.userId,
      cardType,
      amount,
      serial,
      code,
      status: 'Đang duyệt'
    });
    await topup.save();
    res.json({ success: true, message: 'Nạp thẻ thành công! Đang duyệt...' });
  } catch (err) {
    res.status(500).json({ success: false, message: 'Lỗi server khi nạp thẻ.' });
  }
});
// Lịch sử nạp thẻ cào
app.get('/api/topup-card/history', authenticateJWT, async (req, res) => {
  try {
    const history = await TopupCard.find({ userId: req.user.userId }).sort({ createdAt: -1 });
    res.json(history);
  } catch (err) {
    res.status(500).json({ message: 'Lỗi server khi lấy lịch sử nạp thẻ.' });
  }
});
// Nạp ví điện tử
app.post('/api/wallet-topup', authenticateJWT, async (req, res) => {
  const { accountId, amount, content } = req.body;
  if (!accountId || !amount || !content) {
    return res.status(400).json({ success: false, message: 'Thiếu thông tin nạp ví.' });
  }
  try {
    const topup = new WalletTopup({
      userId: req.user.userId,
      accountId,
      amount,
      content,
      status: 'Đang duyệt'
    });
    await topup.save();
    res.json({ success: true, message: 'Gửi yêu cầu nạp ví thành công! Đang duyệt...' });
  } catch (err) {
    res.status(500).json({ success: false, message: 'Lỗi server khi nạp ví.' });
  }
});
// Lịch sử nạp ví điện tử
app.get('/api/wallet-topup/history', authenticateJWT, async (req, res) => {
  try {
    const history = await WalletTopup.find({ userId: req.user.userId }).sort({ createdAt: -1 });
    res.json(history);
  } catch (err) {
    res.status(500).json({ message: 'Lỗi server khi lấy lịch sử nạp ví.' });
  }
});

app.post('/api/wallet-topup/:id/status', authenticateJWT, async (req, res) => {
  const { status } = req.body;
  try {
    const topup = await WalletTopup.findById(req.params.id);
    if (!topup) return res.status(404).json({ message: 'Không tìm thấy giao dịch nạp ví.' });

    // Nếu chuyển sang thành công và trước đó chưa cộng tiền
    if (status === 'Thành công' && topup.status !== 'Thành công') {
      const user = await User.findById(topup.userId);
      if (!user) return res.status(404).json({ message: 'Không tìm thấy user.' });

      user.balance += topup.amount;
      user.totalTopup += topup.amount;
      await user.save();

      // Lưu lịch sử giao dịch
      const transaction = new Transaction({
        userId: user._id,
        amount: topup.amount,
        transactionType: 'add',
        adminId: req.user.userId,
        description: `Nạp ví: ${topup.content || ''}`
      });
      await transaction.save();
    }

    topup.status = status;
    await topup.save();
    res.json({ success: true, message: 'Cập nhật trạng thái thành công.' });
  } catch (err) {
    res.status(500).json({ message: 'Lỗi server khi cập nhật trạng thái.' });
  }
});

app.post('/api/topup-card/:id/status', authenticateJWT, async (req, res) => {
  const { status } = req.body;
  try {
    const topup = await TopupCard.findById(req.params.id);
    if (!topup) return res.status(404).json({ message: 'Không tìm thấy giao dịch nạp thẻ.' });

    // Nếu chuyển sang thành công và trước đó chưa cộng tiền
    if (status === 'Thành công' && topup.status !== 'Thành công') {
      const user = await User.findById(topup.userId);
      if (!user) return res.status(404).json({ message: 'Không tìm thấy user.' });

      user.balance += topup.amount;
      user.totalTopup += topup.amount;
      await user.save();

      // Lưu lịch sử giao dịch
      const transaction = new Transaction({
        userId: user._id,
        amount: topup.amount,
        transactionType: 'add',
        adminId: req.user.userId,
        description: `Nạp thẻ: ${topup.cardType || ''}`
      });
      await transaction.save();
    }

    topup.status = status;
    await topup.save();
    res.json({ success: true, message: 'Cập nhật trạng thái thành công.' });
  } catch (err) {
    res.status(500).json({ message: 'Lỗi server khi cập nhật trạng thái.' });
  }
});

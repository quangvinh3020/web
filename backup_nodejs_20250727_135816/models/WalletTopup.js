const mongoose = require('mongoose');
const WalletTopupSchema = new mongoose.Schema({
  userId: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
  accountId: { type: String, required: true },
  amount: { type: Number, required: true },
  content: { type: String, required: true },
  status: { type: String, enum: ['Đang duyệt', 'Thành công', 'Thất bại'], default: 'Đang duyệt' },
  createdAt: { type: Date, default: Date.now }
});
module.exports = mongoose.model('WalletTopup', WalletTopupSchema); 
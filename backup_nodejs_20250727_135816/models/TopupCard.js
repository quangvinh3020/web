const mongoose = require('mongoose');
const TopupCardSchema = new mongoose.Schema({
  userId: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
  cardType: { type: String, required: true },
  amount: { type: Number, required: true },
  serial: { type: String, required: true },
  code: { type: String, required: true },
  status: { type: String, enum: ['Đang duyệt', 'Thành công', 'Thất bại'], default: 'Đang duyệt' },
  createdAt: { type: Date, default: Date.now }
});
module.exports = mongoose.model('TopupCard', TopupCardSchema); 
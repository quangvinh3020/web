const mongoose = require("mongoose");

// Định nghĩa schema cho Transaction
const transactionSchema = new mongoose.Schema({
  userId: { 
    type: mongoose.Schema.Types.ObjectId, 
    ref: "User", 
    required: true 
  },
  amount: { 
    type: Number, 
    required: true 
  },
  transactionType: { 
    type: String, 
    enum: ["add", "subtract"], 
    required: true 
  },
  adminId: { 
    type: mongoose.Schema.Types.ObjectId, 
    ref: "User", 
    required: true 
  },
  description: { 
    type: String, 
    required: false 
  },
  createdAt: { 
    type: Date, 
    default: Date.now 
  }
});

// Tạo model từ schema
const Transaction = mongoose.model("Transaction", transactionSchema);

module.exports = Transaction;

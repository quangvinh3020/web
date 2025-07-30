// Script debug API stats
async function debugStats() {
    console.log("🔍 Debugging stats API...");
    
    // Kiểm tra token
    const token = localStorage.getItem('token');
    console.log("Token:", token ? "Có" : "Không");
    
    if (!token) {
        console.error("❌ Không có token, cần đăng nhập");
        return;
    }
    
    try {
        // Test API stats
        const response = await fetch('http://localhost:5000/api/stats', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        console.log("Response status:", response.status);
        console.log("Response headers:", response.headers);
        
        if (response.ok) {
            const stats = await response.json();
            console.log("✅ Stats data:", stats);
            
            // Cập nhật UI
            document.getElementById('users-count').textContent = stats.users_count;
            document.getElementById('products-count').textContent = stats.products_count;
            document.getElementById('revenue-amount').textContent = formatCurrency(stats.total_revenue);
            document.getElementById('orders-count').textContent = stats.completed_orders_count;
            
            console.log("✅ UI updated successfully");
        } else {
            const errorText = await response.text();
            console.error("❌ API Error:", response.status, errorText);
        }
    } catch (error) {
        console.error("❌ Network Error:", error);
    }
}

// Format tiền tệ
function formatCurrency(amount) {
    if (amount >= 1000000) {
        return (amount / 1000000).toFixed(1) + 'M';
    } else if (amount >= 1000) {
        return (amount / 1000).toFixed(0) + 'K';
    }
    return amount.toString();
}

// Chạy debug khi load trang
document.addEventListener('DOMContentLoaded', function() {
    console.log("🚀 Page loaded, starting debug...");
    debugStats();
});

// Thêm button debug
document.addEventListener('DOMContentLoaded', function() {
    const debugButton = document.createElement('button');
    debugButton.textContent = 'Debug Stats';
    debugButton.className = 'btn btn-warning btn-sm';
    debugButton.onclick = debugStats;
    debugButton.style.position = 'fixed';
    debugButton.style.top = '10px';
    debugButton.style.right = '10px';
    debugButton.style.zIndex = '9999';
    document.body.appendChild(debugButton);
}); 
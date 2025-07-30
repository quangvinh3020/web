// Script để cập nhật thống kê thực từ database
async function updateStats() {
    try {
        // Lấy thống kê từ API
        const response = await fetch('http://localhost:5000/api/stats', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`,
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            const stats = await response.json();
            
            // Cập nhật các số liệu
            document.getElementById('users-count').textContent = stats.users_count;
            document.getElementById('products-count').textContent = stats.products_count;
            document.getElementById('revenue-amount').textContent = formatCurrency(stats.total_revenue);
            document.getElementById('orders-count').textContent = stats.completed_orders_count;
            
            console.log('Thống kê đã được cập nhật:', stats);
        } else {
            console.error('Lỗi khi lấy thống kê:', response.status);
        }
    } catch (error) {
        console.error('Lỗi kết nối:', error);
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

// Cập nhật thống kê khi trang load
document.addEventListener('DOMContentLoaded', function() {
    updateStats();
    
    // Cập nhật mỗi 30 giây
    setInterval(updateStats, 30000);
}); 
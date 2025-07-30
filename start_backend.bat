@echo off
echo 🐍 Kiểm tra Python...

py --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python chưa được cài đặt hoặc không có trong PATH
    echo.
    echo 📥 Vui lòng:
    echo 1. Tải Python từ: https://www.python.org/downloads/
    echo 2. Cài đặt với tùy chọn "Add Python to PATH"
    echo 3. Chạy lại script này
    echo.
    pause
    exit /b 1
)

echo ✅ Python đã được cài đặt!
echo.

echo 📦 Kiểm tra dependencies...
py -m pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo ❌ Lỗi cài đặt dependencies
    pause
    exit /b 1
)

echo ✅ Dependencies đã được cài đặt!
echo.

echo 🚀 Khởi động Flask backend...
echo 📍 Server sẽ chạy tại: http://localhost:5000
echo.
py app.py

pause 
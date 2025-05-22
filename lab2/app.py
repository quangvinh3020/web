from flask import Flask, render_template

app = Flask(__name__)

@app.route("/student")
def student_info():
    student = {
        "name": "Trần Quang Vinh",
        "student_id": "2374802010564",
        "year": "Năm 2",
        "major": "Công nghệ thông tin",
        "hobbies": ["Nghe nhạc", "Đọc sách", "Chơi game"]
    }
    return render_template("student.html", student=student)

if __name__ == "__main__":
    app.run(debug=True)

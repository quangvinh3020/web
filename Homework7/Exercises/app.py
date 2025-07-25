from flask import Flask, render_template, request, redirect, url_for, Response
from pymongo import MongoClient
from bson.objectid import ObjectId
import csv

app = Flask(__name__, template_folder='templates')

client = MongoClient("mongodb://localhost:27017/")
db = client["students_db"]
collection = db["students"]

@app.route('/')
def index():
    return render_template('Index.html')

# Exercise 1: Hiển thị danh sách sinh viên
@app.route('/exercise1')
def exercise1():
    students = list(collection.find())
    return render_template('Exercise1.html', students=students)

# Exercise 2: Thêm sinh viên mới
@app.route('/exercise2', methods=['GET', 'POST'])
def exercise2():
    if request.method == 'POST':
        student = {
            'name': request.form['name'],
            'age': int(request.form['age']),
            'gender': request.form['gender'],
            'major': request.form['major'],
            'math': float(request.form['math']),
            'literature': float(request.form['literature']),
            'english': float(request.form['english'])
        }
        student['gpa'] = round((student['math'] + student['literature'] + student['english']) / 3, 2)
        if student['gpa'] >= 8:
            student['rank'] = 'Excellent'
        elif student['gpa'] >= 6.5:
            student['rank'] = 'Good'
        else:
            student['rank'] = 'Average'
        collection.insert_one(student)
        return redirect(url_for('exercise1'))
    return render_template('Exercise2.html')

# Exercise 3: Sửa sinh viên
@app.route('/exercise3/<id>', methods=['GET', 'POST'])
def exercise3(id):
    student = collection.find_one({"_id": ObjectId(id)})
    if request.method == 'POST':
        updated = {
            'name': request.form['name'],
            'age': int(request.form['age']),
            'gender': request.form['gender'],
            'major': request.form['major'],
            'math': float(request.form['math']),
            'literature': float(request.form['literature']),
            'english': float(request.form['english'])
        }
        updated['gpa'] = round((updated['math'] + updated['literature'] + updated['english']) / 3, 2)
        if updated['gpa'] >= 8:
            updated['rank'] = 'Excellent'
        elif updated['gpa'] >= 6.5:
            updated['rank'] = 'Good'
        else:
            updated['rank'] = 'Average'
        collection.update_one({"_id": ObjectId(id)}, {"$set": updated})
        return redirect(url_for('exercise1'))
    return render_template('Exercise3.html', student=student, id=id)

# Exercise 4: Xoá sinh viên và render Exercise4.html để xác nhận
@app.route('/exercise4/<id>')
def exercise4(id):
    student = collection.find_one({"_id": ObjectId(id)})
    collection.delete_one({"_id": ObjectId(id)})
    return render_template('Exercise4.html', student=student)

# Exercise 5: Tìm kiếm theo tên chính xác
@app.route('/exercise5', methods=['GET', 'POST'])
def exercise5():
    students = []
    keyword = ""
    if request.method == 'POST':
        keyword = request.form['keyword']
        students = list(collection.find({'name': keyword}))
    return render_template('Exercise5.html', students=students, keyword=keyword)

# Exercise 6: Tìm kiếm gần đúng theo tên (không phân biệt hoa thường)
@app.route('/exercise6', methods=['GET', 'POST'])
def exercise6():
    students = []
    keyword = ""
    if request.method == 'POST':
        keyword = request.form['keyword']
        students = list(collection.find({'name': {'$regex': keyword, '$options': 'i'}}))
    return render_template('Exercise6.html', students=students, keyword=keyword)

# Exercise 7: Lọc sinh viên theo ngành
@app.route('/exercise7', methods=['GET'])
def exercise7():
    majors = collection.distinct('major')
    selected = request.args.get('major')
    if selected:
        students = list(collection.find({'major': selected}))
    else:
        students = list(collection.find())
    return render_template('Exercise7.html', students=students, majors=majors, selected=selected)

# Exercise 8: Đếm số lượng sinh viên từng ngành
@app.route('/exercise8')
def exercise8():
    stats = list(collection.aggregate([
        {'$group': {'_id': '$major', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}}
    ]))
    return render_template('Exercise8.html', stats=stats)

# Exercise 9: Hiển thị bảng điểm các môn
@app.route('/exercise9')
def exercise9():
    students = list(collection.find())
    return render_template('Exercise9.html', students=students)

# Exercise 10: Hiển thị GPA sinh viên
@app.route('/exercise10')
def exercise10():
    students = list(collection.find())
    return render_template('Exercise10.html', students=students)

# Exercise 11: Xếp loại học lực theo GPA
@app.route('/exercise11')
def exercise11():
    students = list(collection.find())
    return render_template('Exercise11.html', students=students)

# Exercise 12: Lọc sinh viên giỏi (GPA >= 8)
@app.route('/exercise12')
def exercise12():
    students = list(collection.find({'gpa': {'$gte': 8}}))
    return render_template('Exercise12.html', students=students)

# Exercise 13: Sinh viên có GPA cao nhất
@app.route('/exercise13')
def exercise13():
    student = collection.find_one(sort=[('gpa', -1)])
    return render_template('Exercise13.html', student=student)

# Exercise 14: Lọc sinh viên theo độ tuổi
@app.route('/exercise14', methods=['GET', 'POST'])
def exercise14():
    students = []
    min_age = max_age = ""
    if request.method == 'POST':
        min_age = int(request.form['min_age'])
        max_age = int(request.form['max_age'])
        students = list(collection.find({'age': {'$gte': min_age, '$lte': max_age}}))
    return render_template('Exercise14.html', students=students, min_age=min_age, max_age=max_age)

# Exercise 15: Lọc sinh viên theo giới tính
@app.route('/exercise15', methods=['GET'])
def exercise15():
    gender = request.args.get('gender')
    if gender:
        students = list(collection.find({'gender': gender}))
    else:
        students = list(collection.find())
    return render_template('Exercise15.html', students=students, gender=gender)

# Exercise 16: Xuất dữ liệu CSV
@app.route('/exercise16')
def exercise16():
    students = list(collection.find())
    def generate():
        header = ['name', 'age', 'gender', 'major', 'math', 'literature', 'english', 'gpa', 'rank']
        yield ','.join(header) + '\n'
        for s in students:
            row = [str(s.get(h, "")) for h in header]
            yield ','.join(row) + '\n'
    return Response(generate(), mimetype='text/csv',
                    headers={"Content-Disposition": "attachment;filename=students.csv"})

if __name__ == "__main__":
    app.run(debug=True)

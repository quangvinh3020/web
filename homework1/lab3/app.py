from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("form.html")

@app.route("/submit", methods=["POST"])
def submit():
    name = request.form["name"]
    student_id = request.form["student_id"]
    year = request.form["year"]
    major = request.form["major"]
    hobbies = request.form.getlist("hobbies")
    return render_template("result.html", name=name, student_id=student_id, year=year, major=major, hobbies=hobbies)

if __name__ == "__main__":
    app.run(debug=True)

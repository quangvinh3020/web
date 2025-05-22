from flask import Flask, render_template

app = Flask(__name__)

@app.route("/equation")
def equation():
    x = -2
    y = 5 * x + 7
    return render_template("equation.html", x=x, y=y)

if __name__ == "__main__":
    app.run(debug=True)

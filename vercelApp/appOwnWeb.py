from flask import Flask

app  = Flask(__name__)
@app.route("/signup")
def hello_world():
    return "<p>DOCTOR HELP</p>"
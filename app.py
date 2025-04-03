from flask import Flask, render_template, request, session

import sqlite3
import hashlib

app = Flask(__name__)
app.secret_key = "random"

con = sqlite3.connect("login.db")
cur = con.cursor()
cur.execute(""" CREATE TABLE IF NOT EXISTS Users ( 
                UserName VARCHAR(10) NOT NULL PRIMARY KEY,
                UserPassword VARCHAR(20) NOT NULL
                )""")
con.commit()
con.close()


@app.route("/signup", methods=["GET","POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")
    else:
        
        con = sqlite3.connect("login.db")
        cur = con.cursor()
        hash=hashlib.sha256(request.form["password"].encode()).hexdigest()
        cur.execute(""" INSERT INTO Users(UserName, UserPassword)
            VALUES (?,?)""", 
            (request.form["username"], hash))
        con.commit()
        con.close()

        return "signup success"



@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    else:
            con = sqlite3.connect("login.db")
            cur = con.cursor()
            hash=hashlib.sha256(request.form["password"].encode()).hexdigest()
            cur.execute(" SELECT * FROM Users WHERE UserName = ? AND UserPassword = ?",
                        (request.form["username"], hash))
            
            user = cur.fetchone()
            print(user)
            if user:
                 session["username"] = request.form["username"]
                 return render_template("welcome.html")
            else:
                return "login failed"

@app.route("/password", methods = ["GET","POST"])
def password():
     if request.method == "GET":
        if "username" in session:
            return render_template("password.html")
        else:
            return render_template("login.html")
     else:
        con = sqlite3.connect("login.db")
        cur = con.cursor()
        hash=hashlib.sha256(request.form["password"].encode()).hexdigest()
        cur.execute(""" UPDATE Users SET UserPassword=? WHERE UserName=?""",
                        (hash, session["username"]))
        con.commit()
        con.close()

        return "password updated successfully"

@app.route("/w")
def welcome():
     return render_template("welcome.html")

@app.route("/logout")
def logout():
     session.pop("username", None)
     return render_template("login.html")

@app.route("/")
def home():
     return render_template("homepage.html")

@app.route("/doctors")
def doctors():
     return render_template("pages/doctors.html")

@app.route("/appointment")
def appointment():
     return render_template("pages/appointment.html")

@app.route("/assistant")
def assistant():
     return render_template("pages/assistant.html")

@app.route("/contact")
def contact():
     return render_template("pages/contact.html")

@app.route("/reviews")
def reviews():
     return render_template("pages/reviews.html") 

@app.route("/services")
def services():
     return render_template("pages/services.html")







if __name__ == "__main__":
    app.run(debug = True)


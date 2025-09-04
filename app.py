from flask import Flask, render_template, request, session

import sqlite3
import hashlib

app = Flask(__name__)
app.secret_key = "random"

con = sqlite3.connect("main.db")
cur = con.cursor()
cur.execute(""" CREATE TABLE IF NOT EXISTS Users ( 
                UserName VARCHAR(10) NOT NULL PRIMARY KEY,
                UserFirstName VARCHAR(30) NOT NULL,
                UserSurname VARCHAR(30) NOT NULL, 
                UserEmail VARCHAR(30) NOT NULL,    
                UserPassword VARCHAR(20) NOT NULL 
                )""")


cur.execute(""" CREATE TABLE IF NOT EXISTS Reviews ( 
                ReviewID INTEGER PRIMARY KEY AUTOINCREMENT,
                UserName VARCHAR(10) NOT NULL,
                Comment VARCHAR(1000) NOT NULL,
                StarRating INTEGER NOT NULL,
                FOREIGN KEY (UserName) REFERENCES Users(UserName)
                )""")
con.commit()
con.close() 

@app.route("/signup", methods=["GET","POST"])
def signup():
    if request.method == "GET":
        return render_template("authorisedUsers/signup.html")
    else:
        
        con = sqlite3.connect("main.db")
        cur = con.cursor()
        hash=hashlib.sha256(request.form["password"].encode()).hexdigest()
        cur.execute(""" INSERT INTO Users(UserName, UserFirstName, UserSurname, UserEmail, UserPassword)
            VALUES (?, ?, ?, ?, ?)""", 
            (request.form["username"],request.form["userfirstname"], request.form["usersurname"], request.form["useremail"],hash))
        con.commit()
        con.close()

        return "signup success"



@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "GET":
        return render_template("authorisedUsers/login.html")
    else:
            con = sqlite3.connect("main.db")
            cur = con.cursor()
            hash=hashlib.sha256(request.form["password"].encode()).hexdigest()
            cur.execute(" SELECT * FROM Users WHERE UserName = ? AND UserPassword = ?",
                        (request.form["username"], hash))
            
            user = cur.fetchone()
            print(user)
            if user:
                 session["username"] = request.form["username"]
                 return render_template("pages/reviews.html")
            else:
                return "login failed"

@app.route("/password", methods = ["GET","POST"])
def password():
    if request.method == "GET":
        if "username" in session:
            return render_template("authorisedUsers/password.html")
        else:
            return render_template("authorisedUsers/login.html")
    else:
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        if password != confirm_password:
            return "Passwords do not match!"
        con = sqlite3.connect("main.db")
        cur = con.cursor()
        hash = hashlib.sha256(password.encode()).hexdigest()
        cur.execute(""" UPDATE Users SET UserPassword=? WHERE UserName=?""",
                    (hash, session["username"]))
        con.commit()
        con.close()
        return "password updated successfully"

@app.route("/w")
def welcome():
     return render_template("authorisedUsers/welcome.html")

@app.route("/logout")
def logout():
     session.pop("username", None)
     return render_template("authorisedUsers/login.html")

@app.route("/")
def home():
     return render_template("pages/homepage.html")

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

@app.route("/reviews", methods=["GET", "POST"])
def reviews():
         if "username" not in session:
            return render_template("authorisedUsers/login.html")
         
         if request.method == "POST": 
              rating = request.form.get("rating")
              comment = request.form.get("review")
              username = session["username"]

              if rating and comment:
                   con = sqlite3.connect("main.db")
                   cur = con.cursor()
                   cur.execute("""INSERT INTO Reviews (UserName, Comment, StarRating) 
                                  VALUES (?, ?, ?)""", (username, comment, int(rating)))
                   con.commit()
                   con.close()
                   return render_template("pages/reviews.html", message="Review submitted successfully")
         return render_template("pages/reviews.html")
@app.route("/services")
def services():
     return render_template("pages/services.html")

@app.route("/allreviews")
def allreviews():

    if request.method == "POST":

        if "username" not in session:
            return render_template("pages/login.html")
 
        rating = request.form.get("rating")
        comment = request.form.get("comment")
        username = session["username"]

        con = sqlite3.connect("main.db")
        cur = con.cursor()
        cur.execute("SELECT UserFirstName, UserSurname FROM Users WHERE UserName=?", (username,))
        result = cur.fetchone()
        con.close()

        fname, lname = result if result else ("Unknown", "User")

        con = sqlite3.connect("main.db")
        cur = con.cursor()
        cur.execute("""INSERT INTO Reviews (UserName, UserFirstName, UserSurname, Comment, StarRating)
                       VALUES (?, ?, ?, ?, ?)""",
                    (username, fname, lname, comment, int(rating)))
        con.commit()
        con.close()

        return render_template("pages/allreviews.html")  

    else:

        con = sqlite3.connect("main.db")
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("""SELECT Users.UserFirstName, Reviews.StarRating, Reviews.Comment 
                   FROM Reviews, Users
                   WHERE (Reviews.UserName = Users.UserName) 
                   ORDER BY ReviewID DESC""")
        reviews = cur.fetchall()
        con.close()

        return render_template("pages/allreviews.html", reviews=reviews)







if __name__ == "__main__":
    app.run(debug = True)


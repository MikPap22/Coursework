#Imports and initial setup
from flask import Flask, render_template, request, session,redirect
from datetime import datetime, timedelta
import sqlite3
import hashlib

#Flask app configuration
app = Flask(__name__)
app.secret_key = "random"

#Database initialization
con = sqlite3.connect("main.db", timeout=30)
cur = con.cursor()

#Users Table
cur.execute(""" CREATE TABLE IF NOT EXISTS Users ( 
                UserName VARCHAR(10) NOT NULL PRIMARY KEY,
                UserFirstName VARCHAR(30) NOT NULL,
                UserSurname VARCHAR(30) NOT NULL, 
                UserEmail VARCHAR(30) NOT NULL,    
                UserPassword VARCHAR(20) NOT NULL 
                )""")

#Reviews Table
cur.execute(""" CREATE TABLE IF NOT EXISTS Reviews ( 
                ReviewID INTEGER PRIMARY KEY AUTOINCREMENT,
                UserName VARCHAR(10) NOT NULL,
                Comment VARCHAR(1000) NOT NULL,
                StarRating INTEGER NOT NULL,
                FOREIGN KEY (UserName) REFERENCES Users(UserName)
                )""")

#Appointments Table
cur.execute (""" CREATE TABLE IF NOT EXISTS Appointments (
                 AppointmentID INTEGER PRIMARY KEY AUTOINCREMENT,
                 UserName VARCHAR(10) NOT NULL,
                 DoctorName VARCHAR(50) NOT NULL,
                 AppointmentDate DATE NOT NULL,
                 FOREIGN KEY (UserName) REFERENCES Users(UserName)
                )""")
con.commit()
con.close() 

#Signup route
@app.route("/signup", methods=["GET","POST"])
def signup():

    #Show sign up page
    if request.method == "GET":
        return render_template("authorisedUsers/signup.html")
    else:
        
        #Connect to database
        con = sqlite3.connect("main.db", timeout=30)
        cur = con.cursor()

        #Hash password with SHA-256 for security
        hash=hashlib.sha256(request.form["password"].encode()).hexdigest()
        
        #Insert new user into Users table
        cur.execute(""" INSERT INTO Users(UserName, UserFirstName, UserSurname, UserEmail, UserPassword)
            VALUES (?, ?, ?, ?, ?)""", 
            (request.form["username"],request.form["userfirstname"], request.form["usersurname"], request.form["useremail"],hash))
        
        #Save changes and close connection
        con.commit()
        con.close()

        #Success message
        return "signup success"

#Login route
@app.route("/login", methods=["GET","POST"])
def login():

    #If user opens the login page nromally, show the login template
    if request.method == "GET":
        return render_template("authorisedUsers/login.html")
    else:

        #Deterrmine where the user should be redirected after logging in
        next_page = request.form.get("next") or "/reviews"

        #Connecting to the database
        con = sqlite3.connect("main.db", timeout=30)
        cur = con.cursor()

        #Hashing the password, so it can be compared with the stored hashed password
        hash = hashlib.sha256(request.form["password"].encode()).hexdigest()
        
        #Checking database to find matching username and hashed password
        cur.execute("SELECT * FROM Users WHERE UserName=? AND UserPassword=?",
                    (request.form["username"], hash))
        user = cur.fetchone()

        #Closing the database connection
        con.close()

        #If user exists, create session and redirect to the internded page
        if user:
            session["username"] = request.form["username"]
            return redirect(next_page) 

        #If credentials are incorrect, show error message 
        else:
            return "login failed"

#Password update route
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
        con = sqlite3.connect("main.db", timeout=30)
        cur = con.cursor()
        hash = hashlib.sha256(password.encode()).hexdigest()
        cur.execute(""" UPDATE Users SET UserPassword=? WHERE UserName=?""",
                    (hash, session["username"]))
        con.commit()
        con.close()
        return "password updated successfully"

#Logout route
@app.route("/logout")
def logout():
     session.pop("username", None)
     return render_template("authorisedUsers/homepage.html")

#Basic page routes

#Homepage route
@app.route("/")
def home():
     return render_template("pages/homepage.html")

#Doctors page route
@app.route("/doctors")
def doctors():
     return render_template("pages/doctors.html")

#Contact information page route
@app.route("/contact")
def contact():
     return render_template("pages/contact.html")

#Services and Specialties route
@app.route("/services")
def services():
     return render_template("pages/services.html")

#Appointment booking route
@app.route("/appointment", methods=["GET", "POST"])
def appointment():
    con = sqlite3.connect("main.db", timeout=30)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    message = None

    #Cancel appointment
    if request.method == "POST" and "cancel_id" in request.form and "username" in session:
        cancel_id = request.form.get("cancel_id")
        cur.execute("DELETE FROM Appointments WHERE AppointmentID=? AND UserName=?",
                    (cancel_id, session["username"]))
        con.commit()
        message = "Appointment cancelled."

    #Book appointment
    elif request.method == "POST" and "username" in session:
        doctor = request.form.get("doctor")
        date = request.form.get("date")
        time = request.form.get("time")

        try:
            appointment_datetime = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        except ValueError:
            con.close()
            return render_template("pages/appointment.html",
                                   message="Invalid date or time",
                                   available_times=[],
                                   appointments=[],
                                   logged_in="username" in session)

        cur.execute("""SELECT 1 FROM Appointments 
                       WHERE DoctorName=? AND AppointmentDate=?""",
                    (doctor, appointment_datetime))
        if cur.fetchone():
            message = "That time slot is already booked!"
        else:
            cur.execute("""INSERT INTO Appointments(UserName, DoctorName, AppointmentDate)
                           VALUES (?, ?, ?)""",
                        (session["username"], doctor, appointment_datetime))
            con.commit()
            message = "Appointment booked successfully!"

    #Generate available time slots
    date = request.args.get("date") or datetime.now().strftime("%Y-%m-%d")
    doctor = request.args.get("doctor") or "Dr. Smith"

    start = datetime.strptime(date + " 09:00", "%Y-%m-%d %H:%M")
    end = datetime.strptime(date + " 17:00", "%Y-%m-%d %H:%M")
    slots = []
    while start < end:
        slots.append(start.strftime("%H:%M"))
        start += timedelta(minutes=15)

    cur.execute("""SELECT strftime('%H:%M', AppointmentDate) 
                   FROM Appointments 
                   WHERE DoctorName=? AND date(AppointmentDate)=?""",
                (doctor, date))
    booked = [row[0] for row in cur.fetchall()]
    available_times = [s for s in slots if s not in booked]

    #Retrieve User appointments
    my_appointments = []
    if "username" in session:
        cur.execute("""SELECT AppointmentID, DoctorName, AppointmentDate
                       FROM Appointments
                       WHERE UserName=?
                       ORDER BY AppointmentDate ASC""",
                    (session["username"],))
        my_appointments = cur.fetchall()

    con.close()
    return render_template("pages/appointment.html",
                           available_times=available_times,
                           appointments=my_appointments,
                           message=message,
                           logged_in="username" in session,
                           chosen_date=date,
                           chosen_doctor=doctor)

#AI Assistant route
@app.route("/assistant")
def assistant():
     import os
     api_chat = os.environ.get("API_KEY", "")
     return render_template("pages/assistant.html", api_key=api_chat)

#User reviews route
@app.route("/reviews", methods=["GET", "POST"])
def reviews():
         if "username" not in session:
            return render_template("authorisedUsers/login.html")
         
         if request.method == "POST": 
              rating = request.form.get("rating")
              comment = request.form.get("review")
              username = session["username"]

              if rating and comment:
                   con = sqlite3.connect("main.db", timeout=30)
                   cur = con.cursor()
                   cur.execute("""INSERT INTO Reviews (UserName, Comment, StarRating) 
                                  VALUES (?, ?, ?)""", (username, comment, int(rating)))
                   con.commit()
                   con.close()
                   return render_template("pages/reviews.html", message="Review submitted successfully")
         return render_template("pages/reviews.html")

#View all reviews route
@app.route("/allreviews")
def allreviews():

    if request.method == "POST":

        if "username" not in session:
            return render_template("pages/login.html")
 
        rating = request.form.get("rating")
        comment = request.form.get("comment")
        username = session["username"]

        con = sqlite3.connect("main.db", timeout=30)
        cur = con.cursor()
        cur.execute("SELECT UserFirstName, UserSurname FROM Users WHERE UserName=?", (username,))
        result = cur.fetchone()
        con.close()

        fname, lname = result if result else ("Unknown", "User")

        con = sqlite3.connect("main.db", timeout=30)
        cur = con.cursor()
        cur.execute("""INSERT INTO Reviews (UserName, UserFirstName, UserSurname, Comment, StarRating)
                       VALUES (?, ?, ?, ?, ?)""",
                    (username, fname, lname, comment, int(rating)))
        con.commit()
        con.close()

        return render_template("pages/allreviews.html")  

    else:

        con = sqlite3.connect("main.db", timeout=30)
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("""SELECT Users.UserFirstName, Reviews.StarRating, Reviews.Comment 
                   FROM Reviews, Users
                   WHERE (Reviews.UserName = Users.UserName) 
                   ORDER BY ReviewID DESC""")
        reviews = cur.fetchall()
        con.close()

        return render_template("pages/allreviews.html", reviews=reviews)






#Run the application
if __name__ == "__main__":
    app.run(debug = True)


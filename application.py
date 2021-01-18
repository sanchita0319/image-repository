import os

#Starter library from my intro cs class
from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session, send_from_directory
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from helpers import apology, login_required, lookup, usd


# Configure application
app = Flask(__name__)

#This is the database that will hold all users that register for the repository - will store password and username
db = SQL("sqlite:///users.db")

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

#id = 0
# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


#This is where public images are going to be stored so that all users can view them
app.config["UPLOADS"] = "/home/ubuntu/Shopify/Save_Images"

#These are the valid file formates
app.config["ALLOWED"] = ["jpeg", "png", "jpg"]

# Custom filter
#app.jinja_env.filters["usd"] = usd
#Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

#app.config["SAVE"] = "/Shopify/Save_Images"
Session(app)



#This index page is the first place users can upload an image
@app.route("/index", methods=["GET", "POST"])
@login_required
def index():
    return render_template("index.html")

#Users can register here
@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user for an account."""

    # POST
    if request.method == "POST":

        # Validate form submission - username + password + password confirmation
        if not request.form.get("username"):
            return apology("missing username")
        elif not request.form.get("password"):
            return apology("missing password")
        elif request.form.get("password") != request.form.get("password_confirmation"):
            return apology("passwords don't match")
        try:
            #We save it to table
            id = db.execute("INSERT INTO users (username, hash) VALUES(?, ?)",
                            request.form.get("username"),
                            generate_password_hash(request.form.get("password")))
        except RuntimeError:
            return apology("username taken")

        # Log user in
        session["user_id"] = id
        #This creates a private folder for each user's private images whenever a new person registers
        os.mkdir(os.path.join(app.config["UPLOADS"], str(session["user_id"])))

        # Let user know they're registered
        flash("Registered!")
        return redirect("/")

    # GET
    else:
        return render_template("register.html")

#This is the homepage as a user must login before accessing capabilities
@app.route("/")
@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return render_template("index.html")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


def valid(name):

    if not "." in name:
        return False

    #This pasers to get the extension
    extension = name.rsplit(".", 1)[1]

    #Then we check to see if the file format is valid
    if extension.lower() in app.config["ALLOWED"]:
        return True
    else:
        return False

#This is how we upload an image
@app.route("/upload-image", methods=["GET", "POST"])
def upload_image():

    if request.method == "POST":

        if request.files:

            #We get a series of images to upload multiple images at once
            images = request.files.getlist("image")

            #We get whether its a private or public upload
            security = request.form.get("type")

            compare = security.upper()
            if compare != "PUBLIC" and compare != "PRIVATE":
                return render_template("index.html")

            for image in images:
                if not image:
                    return render_template("index.html")

                if valid(image.filename):
                    #We secure the filename
                    name = secure_filename(image.filename)

                    if security.upper == "PUBLIC":
                        #This is saved to the general Save_Images folder
                        image.save(os.path.join(app.config["UPLOADS"], name))

                    else:
                        #This is saved to the user's public folder
                        image.save(os.path.join(os.path.join(app.config["UPLOADS"], str(session["user_id"])), name))
            #We get the names of both files
            publicNames = os.listdir('/home/ubuntu/Shopify/Save_Images')
            privateNames = os.listdir(os.path.join(app.config["UPLOADS"], str(session["user_id"])))
            #This will render both the public and private images separated by private and public
            return render_template("images.html", publicNames=publicNames, privateNames=privateNames)

#This will display the public images
@app.route('/Save_Images/<name>')
def displayPublic(name):
    return send_from_directory(app.config["UPLOADS"], name)

#This will display the private images.
@app.route('/Save_Images/<name>')
def displayPrivate(name):
    return send_from_directory(os.path.join(app.config["UPLOADS"], str(session["user_id"])), name)
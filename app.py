from flask import Flask, render_template, url_for, redirect, request, flash, send_file
import csv
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

# Create User model
class User(UserMixin):
    def __init__(self, id, username, password,email_id):
        self.id = id
        self.username = username
        self.password = password
        self.email_id = email_id

# Load user from the session
@login_manager.user_loader
def load_user(user_id):
    con = get_db_connection()
    cursor = con.cursor(dictionary=True)
    cursor.execute("SELECT * FROM credentials WHERE ID = %s", (user_id,))
    user = cursor.fetchone()
    con.close()
    if user:
        return User(user['ID'], user['NAME'], user['PASSWORD'], user['EMAIL_ID']) 
    return None

# Function to get DB connection
def get_db_connection():
    try:
        con = mysql.connector.connect(
            host='localhost',  # MySQL host, could be localhost or an IP address
            user='root',  # MySQL user
            password='12345',  # MySQL password
            database='user_management',  # Name of the database
            auth_plugin='mysql_native_password'
        )
        if con.is_connected():
            return con
        else:
            return None
    except Error as e:
        print(f"Error: {str(e)}")
        return None



# Home route (Listing users)
@app.route("/")
def home():
    con = get_db_connection()
    if not con:
        flash('Database connection failed')
        return render_template("home.html")

    cursor = con.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Users_Details")
    users = cursor.fetchall()
    cursor.close()
    con.close()
    return render_template("home.html", users=users)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Query the database to check if the username exists
        con = get_db_connection()
        cursor = con.cursor(dictionary=True)
        cursor.execute("SELECT * FROM credentials WHERE NAME = %s", (username,))
        user = cursor.fetchone()
        con.close()
      
        # If user is found, compare the password using hashed password
        if user and check_password_hash(user['PASSWORD'], password):
            user_obj = User(user['ID'], user['NAME'], user['PASSWORD'], '')  # Email is no longer needed
            login_user(user_obj)
            flash('Login Successful!', 'success')
            return redirect(url_for('home'))  # Redirect to home page after successful login
        else:
            flash('Invalid credentials', 'danger')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Hash the password before storing it in the database
        hashed_password = generate_password_hash(password)

        # Add the user to the database
        con = get_db_connection()
        cursor = con.cursor()
        
        # Insert a new user into the table with the hashed password
        cursor.execute("INSERT INTO credentials (NAME, PASSWORD) VALUES (%s, %s)", (username, hashed_password))
        con.commit()
        con.close()
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

# Add User
@app.route("/addUsers", methods=['GET', 'POST'])
def addUsers():
    if request.method == 'POST':
        name = request.form['name']
        city = request.form['city']
        age = request.form['age']
        email = request.form['email'] 

        con = get_db_connection()  # Get DB connection
        cursor = con.cursor(dictionary=True)
        cursor.execute("SELECT MAX(ID) AS max_id FROM Users_Details")
        result = cursor.fetchone()
        if result['max_id'] is not None:
            new_id = result['max_id'] + 1  # Increment the max ID by 1
        else:
            new_id = 1  # Start with 1 if no records exist

        sql = "INSERT INTO Users_Details (ID, NAME, CITY, AGE, PASSWORD, email) VALUES (%s, %s, %s, %s, %s, %s)"
        cursor.execute(sql, (new_id, name, city, age, '12345', email))  # You can change 'password123' to whatever you like
        con.commit()
        cursor.close()
        con.close()
        flash('User Details Added')
        return redirect(url_for("home"))
    return render_template("addUsers.html")

# Edit User route
@app.route("/editUser/<string:id>", methods=['GET', 'POST'])
def editUser(id):
    con = get_db_connection()  # Get DB connection
    if not con:
        flash('Database connection failed')
        return redirect(url_for("home"))
    cursor = con.cursor(dictionary=True)
    if request.method == 'POST':
        name = request.form['name']
        city = request.form['city']
        age = request.form['age']
        email = request.form['email'] 

        cursor.execute("SELECT * FROM Users_Details WHERE email = %s", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            flash("Email already registered!", "danger")
            return redirect(url_for('addUsers'))

        sql = "UPDATE Users_Details SET NAME=%s, CITY=%s, AGE=%s, email=%s WHERE ID=%s"
        cursor.execute(sql, (name, city, age, email, id)) 
        con.commit()
        cursor.close()
        con.close()
        flash('User Detail Updated')
        return redirect(url_for("home"))

    # Fetch the user details for the edit form
    sql = "SELECT * FROM Users_Details WHERE ID=%s"
    cursor.execute(sql, (id,))
    user = cursor.fetchone()  # Fetch one user with the given ID
    cursor.close()
    con.close()
    
    if user:
        return render_template("editUser.html", user=user)
    else:
        flash("User not found")
        return redirect(url_for("home"))

# Delete User
@app.route("/deleteUser/<string:id>", methods=['GET', 'POST'])
def deleteUser(id):
    con = get_db_connection()

    cursor = con.cursor()
    sql = "DELETE FROM Users_Details WHERE ID=%s"
    cursor.execute(sql, (id,))
    con.commit()
    cursor.close()
    con.close()
    flash('User Details Deleted')
    return redirect(url_for("home"))

#Download file csv
@app.route('/download-csv')
def download_csv():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Query to get data from your table
    cursor.execute("SELECT * FROM Users_Details")
    
    # Create a CSV file in memory
    with open('Users_Details.csv', 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow([desc[0] for desc in cursor.description])  # Write column headers
        csv_writer.writerows(cursor.fetchall())  # Write data rows
    
    conn.close()
    
    # Send the CSV file as a download
    return send_file('Users_Details.csv', as_attachment=True, download_name='user_management.csv', mimetype='text/csv')


#Logout Route
@app.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

# Protected Route (Requires Login)
@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@app.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    # Get data from the form
    email = request.form['email']
    city = request.form['city']
    age = request.form['age']
    
    # Update the user in the database
    con = get_db_connection()
    cursor = con.cursor()
    
    sql = "UPDATE Users_Details SET email=%s, CITY=%s, AGE=%s WHERE ID=%s"
    cursor.execute(sql, (email, city, age, current_user.id))  # Use current_user.id for the logged-in user's ID
    con.commit()
    cursor.close()
    con.close()

    flash('Profile updated successfully!', 'success')
    return redirect(url_for('profile'))


if __name__ == "__main__":
    app.secret_key = "abc123"
    app.run(debug=True)

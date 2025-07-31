from flask import Flask, render_template, request, redirect, session, flash
import psycopg2
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'secret'

# ✅ Updated: Use environment variables for DB connection
conn = psycopg2.connect(
    host=os.environ['DB_HOST'],
    database=os.environ['DB_NAME'],
    user=os.environ['DB_USER'],
    password=os.environ['DB_PASSWORD'],
    port=os.environ['DB_PORT']
)
cursor = conn.cursor()

@app.route('/')
def home():
    return render_template("home.html")

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            flash("Login successful.")
            return redirect('/dashboard')
        else:
            flash("Invalid credentials.")
            return redirect('/')
    
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])

        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            flash("Username already exists.")
            return redirect('/register')

        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
        conn.commit()
        flash("Registered successfully. Please login.")
        return redirect('/')
    
    return render_template("register.html")

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect('/')

@app.route('/student_register', methods=['GET', 'POST'])
def student_register():
    if 'user_id' not in session:
        flash("Please login to register a student.")
        return redirect('/login')

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        course = request.form['course']
        phone = request.form['phone']
        user_id = session['user_id']

        try:
            cursor.execute("""
                INSERT INTO students (name, email, course, phone, user_id)
                VALUES (%s, %s, %s, %s, %s)
            """, (name, email, course, phone, user_id))
            conn.commit()
            flash("Student registered successfully.")
            return redirect('/students')
        except psycopg2.Error as e:
            conn.rollback()
            print("Database error:", e)
            flash("Error while registering student.")
            return redirect('/student_register')

    return render_template("student_register.html")

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/')
    return render_template("dashboard.html")

@app.route('/students')
def students():
    try:
        cursor.execute("""
            SELECT s.id, s.name, s.email, s.course, s.phone, u.username
            FROM students s JOIN users u ON s.user_id = u.id
        """)
        data = cursor.fetchall()
        return render_template("students.html", students=data)
    except psycopg2.Error as e:
        print("Database error:", e)
        return "Unable to fetch student list."

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect('/login')

    try:
        cursor.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
        user = cursor.fetchone()
        return render_template("profile.html", user=user)
    except psycopg2.Error as e:
        print("Database error:", e)
        return "Error loading profile."

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        subject = request.form['subject']
        message = request.form['message']
        
        flash("Thank you for reaching out. We'll get back to you soon.")
        return redirect('/contact')
    
    return render_template("contact.html")

@app.route('/college')
def college():
    return render_template("college.html")

@app.route('/books')
def books():
    cursor.execute("SELECT * FROM books")
    books = cursor.fetchall()
    return render_template("books.html", books=books)

@app.route('/add_to_cart/<int:book_id>')
def add_to_cart(book_id):
    if 'user_id' not in session:
        flash("Please log in to add to cart.")
        return redirect('/login')

    try:
        cursor.execute("SELECT * FROM cart WHERE user_id = %s AND book_id = %s", (session['user_id'], book_id))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO cart (user_id, book_id) VALUES (%s, %s)", (session['user_id'], book_id))
            conn.commit()
            flash("Book added to cart.")
        else:
            flash("Book already in cart.")
    except psycopg2.Error as e:
        print("Database error:", e)
        conn.rollback()
        flash("Error adding to cart.")
    return redirect('/books')

@app.route('/cart')
def view_cart():
    if 'user_id' not in session:
        flash("Please log in to view your cart.")
        return redirect('/login')

    try:
        cursor.execute("""
            SELECT b.id, b.name, b.about, b.author
            FROM cart c
            JOIN books b ON c.book_id = b.id
            WHERE c.user_id = %s
        """, (session['user_id'],))
        cart_items = cursor.fetchall()
        return render_template("cart.html", cart=cart_items)
    except psycopg2.Error as e:
        print("Database error:", e)
        return "Error loading cart."

@app.route('/library')
def library():
    cursor.execute("SELECT id, name, about, author FROM books")
    books = cursor.fetchall()
    return render_template("library.html", books=books)

if __name__ == '__main__':
    app.run(debug=True)

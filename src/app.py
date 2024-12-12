from flask import Flask, render_template, request, redirect, url_for, flash, session, Response
from functools import wraps
import mysql.connector
from mysql.connector import Error
from werkzeug.security import check_password_hash, generate_password_hash
from io import StringIO
import csv
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Required for flash messages

# Database connection configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'CPSC408!',
    'database': 'target_store'
}

# Add this near the top of your file with other configurations
EXPORT_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'exports')
# Create the exports directory if it doesn't exist
os.makedirs(EXPORT_FOLDER, exist_ok=True)

def get_db_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Error connecting to database: {e}")
        return None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/select_role')
def select_role():
    role = request.args.get('role')
    if role == 'customer':
        return redirect(url_for('customer_home'))
    elif role == 'employee':
        return redirect(url_for('employee_home'))
    return redirect(url_for('index'))

@app.route('/employee_home')
def employee_home():
    return render_template('employee_home.html')

@app.route('/employee_login', methods=['POST'])
def employee_login():
    email = request.form.get('email')
    password = request.form.get('password')
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Employee WHERE email = %s", (email,))
        employee = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if employee and check_password_hash(employee['password_hash'], password):
            session['user_id'] = employee['employee_id']
            session['user_type'] = 'employee'
            session['role'] = employee['role']
            return redirect(url_for('employee_dashboard'))
        
    flash('Invalid email or password', 'error')
    return redirect(url_for('employee_home'))

@app.route('/employee_dashboard')
@login_required
def employee_dashboard():
    if session.get('user_type') != 'employee':
        flash('Access denied')
        return redirect(url_for('index'))
    return render_template('employee_dashboard.html')

@app.route('/manage_products', methods=['GET', 'POST'])
def manage_products():
    conn = get_db_connection()
    if not conn:
        flash('Database connection error')
        return redirect(url_for('employee_dashboard'))
    
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        # Handle adding new product
        product_data = {
            'product_name': request.form.get('product_name'),
            'description': request.form.get('description'),
            'price': request.form.get('price'),
            'stock_quantity': request.form.get('stock_quantity'),
            'category_id': request.form.get('category_id')
        }
        
        cursor.execute("""
            INSERT INTO Product (product_name, description, price, stock_quantity, category_id)
            VALUES (%(product_name)s, %(description)s, %(price)s, %(stock_quantity)s, %(category_id)s)
        """, product_data)
        conn.commit()
        flash('Product added successfully')
    
    # Get all active products
    cursor.execute("""
        SELECT p.*, c.category_name 
        FROM Product p 
        JOIN Category c ON p.category_id = c.category_id 
        WHERE p.is_deleted = 0
    """)
    products = cursor.fetchall()
    
    # Get categories for the dropdown
    cursor.execute("SELECT * FROM Category")
    categories = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('manage_products.html', products=products, categories=categories)

@app.route('/edit_product', methods=['GET', 'POST'])
def edit_product():
    conn = get_db_connection()
    if not conn:
        flash('Database connection error')
        return redirect(url_for('manage_products'))
    
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        # Handle product update
        product_data = {
            'product_id': request.form.get('product_id'),
            'product_name': request.form.get('product_name'),
            'description': request.form.get('description'),
            'price': request.form.get('price'),
            'stock_quantity': request.form.get('stock_quantity'),
            'category_id': request.form.get('category_id')
        }
        
        cursor.execute("""
            UPDATE Product 
            SET product_name = %(product_name)s,
                description = %(description)s,
                price = %(price)s,
                stock_quantity = %(stock_quantity)s,
                category_id = %(category_id)s
            WHERE product_id = %(product_id)s
        """, product_data)
        conn.commit()
        flash('Product updated successfully')
        return redirect(url_for('manage_products'))
    
    # GET request - show edit form
    product_id = request.args.get('product_id')
    cursor.execute("SELECT * FROM Product WHERE product_id = %s", (product_id,))
    product = cursor.fetchone()
    
    cursor.execute("SELECT * FROM Category")
    categories = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('edit_product.html', product=product, categories=categories)

@app.route('/delete_product')
def delete_product():
    product_id = request.args.get('product_id')
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE Product SET is_deleted = 1 WHERE product_id = %s", (product_id,))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Product deleted successfully')
    return redirect(url_for('manage_products'))

@app.route('/products')
def products():
    conn = get_db_connection()
    if not conn:
        flash('Database connection error')
        return redirect(url_for('customer_home'))
    
    cursor = conn.cursor(dictionary=True)
    
    category_filter = request.args.get('category')
    if category_filter:
        cursor.execute("""
            SELECT p.*, c.category_name, d.department_name
            FROM Product p
            JOIN Category c ON p.category_id = c.category_id
            JOIN Department d ON c.department_id = d.department_id
            WHERE c.category_name = %s AND p.is_deleted = 0
        """, (category_filter,))
    else:
        cursor.execute("""
            SELECT p.*, c.category_name, d.department_name
            FROM Product p
            JOIN Category c ON p.category_id = c.category_id
            JOIN Department d ON c.department_id = d.department_id
            WHERE p.is_deleted = 0
        """)
    
    products = cursor.fetchall()
    
    cursor.execute("SELECT DISTINCT category_name FROM Category")
    categories = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('products.html', products=products, categories=categories)

@app.route('/reports')
@login_required
def reports():
    return render_template('reports.html')

@app.route('/generate_report/<report_type>')
@login_required
def generate_report(report_type):
    conn = get_db_connection()
    if not conn:
        flash('Database connection error')
        return redirect(url_for('reports'))
    
    cursor = conn.cursor(dictionary=True)
    
    if report_type == 'sales_by_department':
        cursor.execute("""
            SELECT d.department_name, SUM(oi.quantity * oi.unit_price) as total_sales
            FROM OrderItems oi
            JOIN Product p ON oi.product_id = p.product_id
            JOIN Category c ON p.category_id = c.category_id
            JOIN Department d ON c.department_id = d.department_id
            WHERE p.is_deleted = 0
            GROUP BY d.department_name
        """)
    elif report_type == 'popular_products':
        # Modified to handle products with no orders
        cursor.execute("""
            SELECT 
                p.product_name, 
                p.price,
                COALESCE(SUM(oi.quantity), 0) as total_ordered
            FROM Product p
            LEFT JOIN OrderItems oi ON p.product_id = oi.product_id
            WHERE p.is_deleted = 0
            GROUP BY p.product_id, p.product_name, p.price
            ORDER BY total_ordered DESC
        """)
    elif report_type == 'customer_orders':
        # Modified to show more order details
        cursor.execute("""
            SELECT 
                CONCAT(c.first_name, ' ', c.last_name) as customer_name,
                COUNT(DISTINCT o.order_id) as number_of_orders,
                SUM(o.total_price) as total_spent
            FROM Customer c
            LEFT JOIN Orders o ON c.customer_id = o.customer_id
            WHERE o.is_deleted = 0 OR o.is_deleted IS NULL
            GROUP BY c.customer_id, c.first_name, c.last_name
            ORDER BY total_spent DESC
        """)
    
    report_data = cursor.fetchall()
    cursor.close()
    conn.close()
    
    if request.args.get('format') == 'csv':
        # Create CSV in memory
        si = StringIO()
        writer = csv.writer(si)
        # Write headers
        if report_data:
            writer.writerow(report_data[0].keys())
            # Write data
            for row in report_data:
                writer.writerow(row.values())
        
        output = si.getvalue()
        si.close()
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'{report_type}_{timestamp}.csv'
        
        # Save to file system
        filepath = os.path.join(EXPORT_FOLDER, filename)
        with open(filepath, 'w', newline='') as f:
            f.write(output)
        
        # Also send as download
        return Response(
            output,
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename={filename}'
            }
        )
    
    return render_template('report_results.html', 
                         report_type=report_type, 
                         data=report_data)

@app.route('/customer_home')
def customer_home():
    return render_template('customer_home.html')

@app.route('/customer_register', methods=['GET', 'POST'])
def customer_register():
    if request.method == 'POST':
        # Get form data
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Validate passwords match
        if password != confirm_password:
            flash('Passwords do not match')
            return redirect(url_for('customer_register'))

        # Connect to database
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            
            # Check if email already exists
            cursor.execute("SELECT * FROM Customer WHERE email = %s", (email,))
            if cursor.fetchone():
                flash('Email already registered')
                cursor.close()
                conn.close()
                return redirect(url_for('customer_register'))

            # Create new customer
            try:
                cursor.execute("""
                    INSERT INTO Customer (first_name, last_name, email, password_hash)
                    VALUES (%s, %s, %s, %s)
                """, (first_name, last_name, email, generate_password_hash(password)))
                conn.commit()
                flash('Registration successful! Please login.')
                return redirect(url_for('customer_home'))
            except Error as e:
                flash(f'An error occurred: {str(e)}')
            finally:
                cursor.close()
                conn.close()
        else:
            flash('Database connection error')
        
        return redirect(url_for('customer_register'))

    # GET request - show registration form
    return render_template('customer_register.html')

@app.route('/customer_login', methods=['POST'])
def customer_login():
    email = request.form.get('email')
    password = request.form.get('password')
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Customer WHERE email = %s", (email,))
        customer = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if customer and check_password_hash(customer['password_hash'], password):
            session['user_id'] = customer['customer_id']
            session['user_type'] = 'customer'
            return redirect(url_for('products'))
        
    flash('Invalid email or password', 'error')
    return redirect(url_for('customer_home'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out')
    return redirect(url_for('index'))

@app.route('/employee_register', methods=['GET', 'POST'])
def employee_register():
    if request.method == 'POST':
        # Get form data
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role = request.form.get('role')

        # Validate passwords match
        if password != confirm_password:
            flash('Passwords do not match')
            return redirect(url_for('employee_register'))

        # Connect to database
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            
            # Check if email already exists
            cursor.execute("SELECT * FROM Employee WHERE email = %s", (email,))
            if cursor.fetchone():
                flash('Email already registered')
                cursor.close()
                conn.close()
                return redirect(url_for('employee_register'))

            # Create new employee
            try:
                cursor.execute("""
                    INSERT INTO Employee (first_name, last_name, email, password_hash, role)
                    VALUES (%s, %s, %s, %s, %s)
                """, (first_name, last_name, email, generate_password_hash(password), role))
                conn.commit()
                flash('Registration successful! Please login.')
                return redirect(url_for('employee_home'))
            except Error as e:
                flash(f'An error occurred: {str(e)}')
            finally:
                cursor.close()
                conn.close()
        else:
            flash('Database connection error')
        
        return redirect(url_for('employee_register'))

    # GET request - show registration form
    return render_template('employee_register.html')

if __name__ == '__main__':
    app.run(debug=True)
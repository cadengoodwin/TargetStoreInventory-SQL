from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from mysql.connector import Error
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Required for flash messages

# Database connection configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'your_username',
    'password': 'your_password',
    'database': 'target_store'
}

def get_db_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Error connecting to database: {e}")
        return None

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
            return redirect(url_for('employee_dashboard'))
        
    flash('Invalid credentials')
    return redirect(url_for('employee_home'))

@app.route('/employee_dashboard')
def employee_dashboard():
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
def reports():
    return render_template('reports.html')

@app.route('/generate_report')
def generate_report():
    report_type = request.args.get('report_type')
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
            GROUP BY d.department_name
        """)
    elif report_type == 'inventory':
        cursor.execute("""
            SELECT p.product_name, p.stock_quantity, c.category_name
            FROM Product p
            JOIN Category c ON p.category_id = c.category_id
            WHERE p.is_deleted = 0
            ORDER BY p.stock_quantity ASC
        """)
    
    report_data = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('report_results.html', report_type=report_type, data=report_data)

if __name__ == '__main__':
    app.run(debug=True)
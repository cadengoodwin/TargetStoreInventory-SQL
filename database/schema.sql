-- Drop existing tables if needed (CAUTION: only for development)
DROP TABLE IF EXISTS OrderItems;
DROP TABLE IF EXISTS Orders;
DROP TABLE IF EXISTS Product;
DROP TABLE IF EXISTS Category;
DROP TABLE IF EXISTS Department;
DROP TABLE IF EXISTS Customer;
DROP TABLE IF EXISTS Employee;

-- Create Department table
CREATE TABLE Department (
    department_id INT AUTO_INCREMENT PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL
);

-- Create Category table
CREATE TABLE Category (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL,
    department_id INT NOT NULL,
    FOREIGN KEY (department_id) REFERENCES Department(department_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

-- Create Product table
CREATE TABLE Product (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    product_name VARCHAR(150) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    stock_quantity INT NOT NULL DEFAULT 0,
    category_id INT NOT NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    FOREIGN KEY (category_id) REFERENCES Category(category_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

-- Create Customer table
CREATE TABLE Customer (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL
);

-- Create Employee table
CREATE TABLE Employee (
    employee_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL
);

-- Create Orders table
CREATE TABLE Orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    order_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total_price DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    FOREIGN KEY (customer_id) REFERENCES Customer(customer_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

-- Create OrderItems table
CREATE TABLE OrderItems (
    order_item_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES Orders(order_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (product_id) REFERENCES Product(product_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

-- Create Indexes
CREATE INDEX idx_product_name ON Product(product_name);
CREATE INDEX idx_category_name ON Category(category_name);
CREATE INDEX idx_customer_email ON Customer(email);

-- Create a View: active products with their department and category
CREATE VIEW view_active_products AS
SELECT p.product_id, p.product_name, p.price, p.stock_quantity, d.department_name, c.category_name
FROM Product p
JOIN Category c ON p.category_id = c.category_id
JOIN Department d ON c.department_id = d.department_id
WHERE p.is_deleted = FALSE;

-- Example Subquery: (Not a permanent object, just an example query)
-- This subquery finds products in categories that have more than 2 active products.
-- You can run this query as needed:
-- SELECT product_name, price
-- FROM Product
-- WHERE category_id IN (
--     SELECT category_id
--     FROM Product
--     WHERE is_deleted = FALSE
--     GROUP BY category_id
--     HAVING COUNT(product_id) > 2
-- );

-- Transaction Example: (Not a permanent object, just an example of transaction usage)
-- START TRANSACTION;
-- INSERT INTO Orders (customer_id, total_price) VALUES (1, 100.00);
-- INSERT INTO OrderItems (order_id, product_id, quantity, unit_price)
-- VALUES (LAST_INSERT_ID(), 1, 2, 50.00);
-- COMMIT;

-- Optional Seed Data for testing
INSERT INTO Department (department_name) VALUES ('Electronics'), ('Home & Kitchen');
INSERT INTO Category (category_name, department_id) VALUES ('Tablets', 1), ('Laptops', 1), ('Cookware', 2);
INSERT INTO Product (product_name, description, price, stock_quantity, category_id) 
VALUES ('iPad Air', 'Apple tablet with 10.9-inch display', 599.99, 50, 1),
       ('MacBook Air', 'Apple laptop with M1 chip', 999.99, 30, 2),
       ('Non-Stick Pan', 'High-quality non-stick pan', 29.99, 100, 3);

-- Use external scripts or application code to export data from view_active_products to CSV/Excel.

-- seed_data.sql
-- This file inserts some initial data into the already created schema.
-- Run this after running schema.sql.

-- Departments
INSERT INTO Department (department_name) VALUES 
('Electronics'), 
('Home & Kitchen'), 
('Clothing');

-- Categories
INSERT INTO Category (category_name, department_id) VALUES
('Tablets', 1),
('Laptops', 1),
('Cookware', 2),
('Furniture', 2),
('Men’s Apparel', 3),
('Women’s Apparel', 3);

-- Products
INSERT INTO Product (product_name, description, price, stock_quantity, category_id) VALUES
('iPad Air', 'Apple tablet with 10.9-inch display', 599.99, 50, 1),
('MacBook Air', 'Apple laptop with M1 chip', 999.99, 30, 2),
('Non-Stick Pan', 'High-quality non-stick pan', 29.99, 100, 3),
('Dining Table', 'Wooden dining table seats 6', 299.99, 10, 4),
('Men’s T-Shirt', '100% Cotton T-Shirt', 19.99, 200, 5),
('Women’s Dress', 'Summer dress with floral pattern', 49.99, 80, 6);

-- Customers
INSERT INTO Customer (first_name, last_name, email, password_hash) VALUES
('John', 'Doe', 'john.doe@example.com', 'hashedpassword123'),
('Jane', 'Smith', 'jane.smith@example.com', 'hashedpassword456');

-- Employees
INSERT INTO Employee (first_name, last_name, email, password_hash, role) VALUES
('Alice', 'Johnson', 'alice.johnson@example.com', 'hashedpass789', 'Manager'),
('Bob', 'Williams', 'bob.williams@example.com', 'hashedpass101112', 'Inventory Clerk');

-- Orders
INSERT INTO Orders (customer_id, total_price) VALUES
(1, 1199.98),  -- e.g. for a MacBook Air + iPad Air
(2, 49.99);     -- e.g. just a Women’s Dress

-- Order Items (matching the above Orders)
-- Suppose order_id=1 is John Doe’s order, containing an iPad Air and a MacBook Air:
INSERT INTO OrderItems (order_id, product_id, quantity, unit_price) VALUES
(1, 1, 1, 599.99),  -- iPad Air
(1, 2, 1, 999.99),  -- MacBook Air

-- Suppose order_id=2 is Jane Smith’s order, containing just a Women’s Dress:
(2, 6, 1, 49.99);

-- Additional products to facilitate testing subqueries and categories:
INSERT INTO Product (product_name, description, price, stock_quantity, category_id) VALUES
('Android Tablet', 'Samsung Galaxy Tab', 299.99, 40, 1),
('Chef’s Knife', 'Professional kitchen knife', 79.99, 60, 3),
('Laptop Stand', 'Adjustable stand for laptops', 39.99, 25, 2);

-- With this additional data, some categories now have more than 2 active products,
-- allowing you to test the subquery that checks categories with more than 2 active products.

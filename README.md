# Arlington Organic Market Management System

## Project Overview

This is a web-based management system for Arlington Organic Market, built using Flask and PostgreSQL. The system helps manage inventory, vendors, products, and customer data efficiently.

## Developers

- Devrat Patel (Student ID: 1002127189)
- Safiullah Ahmed (Student ID: 1002225279)

## Features

- Product Management (Add, Delete, Update)
- Vendor Management
- Inventory Tracking
- Revenue Analytics
- Customer Loyalty System
- Interactive Dashboard

## Tech Stack

- Backend: Python Flask
- Database: PostgreSQL
- Frontend: HTML, Bootstrap
- ORM: psycopg2

## Prerequisites

- Python 3.x
- PostgreSQL
- pip (Python package manager)

## Installation & Setup

1. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Database Setup:

- Create a PostgreSQL database named 'ArlingtonOrganicMarket'
- Update the database connection details in `app.py`:

```python
def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="ArlingtonOrganicMarket",
        user="your_username",
        password="your_password"
    )
```

- Run the SQL queries in `queries.sql` to set up the views and required database structure

4. Run the application:

```bash
python app.py
```

## Project Structure

### Main Components:

- `app.py`: Main application file containing all routes and business logic
- `queries.sql`: Database queries and view definitions
- `templates/`: Frontend HTML templates
  - `index.html`: Main dashboard and forms
  - `result.html`: Display template for query results

### Key Features Explained:

#### 1. Product Management

##### Add New Products with Vendor Information

```python
@app.route('/add_product', methods=['POST'])
def add_product():
    conn = get_db_connection()
    cur = conn.cursor()

    # Get product information
    product_name = request.form['product_name']
    product_price = float(request.form['product_price'])
    product_quantity = int(request.form['product_quantity'])
    product_category = request.form['product_category']

    # Get vendor information
    vendor_name = request.form['vendor_name']
    vendor_street = request.form['vendor_street']
    vendor_city = request.form['vendor_city']
    vendor_state = request.form['vendor_state']
    vendor_zip = request.form['vendor_zip']

    # Get the next available IDs
    cur.execute("SELECT MAX(iId) FROM ITEM")
    max_item_id = cur.fetchone()[0]
    new_item_id = 1 if max_item_id is None else max_item_id + 1

    cur.execute("SELECT MAX(vId) FROM VENDOR")
    max_vendor_id = cur.fetchone()[0]
    new_vendor_id = 1 if max_vendor_id is None else max_vendor_id + 1

    # Add vendor
    cur.execute("""
        INSERT INTO VENDOR (vId, Vname, Street, City, StateAb, ZipCode)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (vId) DO UPDATE SET
        Vname = %s, Street = %s, City = %s, StateAb = %s, ZipCode = %s
        RETURNING vId;
    """, (new_vendor_id, vendor_name, vendor_street, vendor_city, vendor_state, vendor_zip,
          vendor_name, vendor_street, vendor_city, vendor_state, vendor_zip))

    # Add new item
    cur.execute("""
        INSERT INTO ITEM (iId, Iname, Sprice, Category)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (iId) DO UPDATE SET
        Sprice = %s;
    """, (new_item_id, product_name, product_price, product_category, product_price))

    # Add to store inventory
    cur.execute("""
        INSERT INTO STORE_ITEM (sId, iId, Scount)
        VALUES (1, %s, %s)
        ON CONFLICT (sId, iId) DO UPDATE SET
        Scount = %s;
    """, (new_item_id, product_quantity, product_quantity))
```

##### Delete Products

```python
@app.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    conn = get_db_connection()
    cur = conn.cursor()

    # Get the vendor IDs associated with this product
    cur.execute("""
        SELECT vId
        FROM VENDOR_ITEM
        WHERE iId = %s;
    """, (product_id,))
    vendor_ids = [row[0] for row in cur.fetchall()]

    # Delete from VENDOR_ITEM first
    cur.execute("DELETE FROM VENDOR_ITEM WHERE iId = %s;", (product_id,))

    # Delete from store_item
    cur.execute("DELETE FROM STORE_ITEM WHERE iId = %s;", (product_id,))

    # Delete from item
    cur.execute("DELETE FROM ITEM WHERE iId = %s;", (product_id,))

    # Clean up vendors with no products
    for vendor_id in vendor_ids:
        cur.execute("""
            SELECT COUNT(*)
            FROM VENDOR_ITEM
            WHERE vId = %s;
        """, (vendor_id,))
        if cur.fetchone()[0] == 0:
            cur.execute("DELETE FROM VENDOR_STORE WHERE vId = %s;", (vendor_id,))
            cur.execute("DELETE FROM VENDOR WHERE vId = %s;", (vendor_id,))
```

##### Update Product Prices

```python
@app.route('/update_price/<int:product_id>', methods=['POST'])
def update_product_price(product_id):
    conn = get_db_connection()
    cur = conn.cursor()

    new_price = float(request.form['new_price'])
    cur.execute("""
        UPDATE ITEM
        SET Sprice = %s
        WHERE iId = %s;
    """, (new_price, product_id))

    conn.commit()
    cur.close()
    conn.close()
```

#### 2. Analytics Views

##### View Definitions (from queries.sql)

```sql
-- ItemSalesSummary View
CREATE VIEW ItemSalesSummary AS
SELECT
    i.iId,
    i.Iname,
    SUM(o.Amount) AS TotalRevenue,
    SUM(oi.Icount) AS TotalQuantitySold
FROM order_item oi
JOIN item i ON oi.iId = i.iId
JOIN "ORDER" o ON oi.oId = o.oId
GROUP BY i.iId, i.Iname;

-- TopLoyalCustomers View
CREATE VIEW TopLoyalCustomers AS
SELECT cId, Cname, LoyaltyScore
FROM customer
ORDER BY LoyaltyScore DESC
LIMIT 10;
```

##### QV1: Top Revenue Items

```python
@app.route('/top_revenue_items')
def top_revenue_items():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT Iname, TotalRevenue
        FROM ItemSalesSummary
        ORDER BY TotalRevenue DESC
        LIMIT 3;
    """)
    rows = cur.fetchall()
    return render_template('result.html',
                         title="Top 3 Revenue-Generating Items",
                         rows=rows,
                         columns=["Item Name", "Total Revenue"])
```

##### QV2: Popular Items

```python
@app.route('/popular_items')
def popular_items():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT Iname, TotalQuantitySold
        FROM ItemSalesSummary
        WHERE TotalQuantitySold > 50;
    """)
    rows = cur.fetchall()
    return render_template('result.html',
                         title="Items Sold More Than 50 Units",
                         rows=rows,
                         columns=["Item Name", "Total Sold"])
```

##### QV3: Top Customer by Loyalty

```python
@app.route('/top_customer')
def top_customer():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT Cname, LoyaltyScore
        FROM TopLoyalCustomers
        ORDER BY LoyaltyScore DESC
        LIMIT 1;
    """)
    rows = cur.fetchall()
    return render_template('result.html',
                         title="Top Customer by Loyalty",
                         rows=rows,
                         columns=["Customer Name", "Loyalty Score"])
```

##### QV4: Loyal Customers Range

```python
@app.route('/loyal_customers_4_5')
def loyal_customers_4_5():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT Cname, LoyaltyScore
        FROM TopLoyalCustomers
        WHERE LoyaltyScore BETWEEN 4 AND 5;
    """)
    rows = cur.fetchall()
    return render_template('result.html',
                         title="Customers with Loyalty Score 4-5",
                         rows=rows,
                         columns=["Customer Name", "Loyalty Score"])
```

##### QV5: Total Revenue

```python
@app.route('/total_revenue')
def total_revenue():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT SUM(TotalRevenue)
        FROM ItemSalesSummary;
    """)
    total = cur.fetchone()[0]
    return render_template('result.html',
                         title="Total Revenue",
                         rows=[[total]],
                         columns=["Total Revenue"])
```

## Database Schema

The system uses several interconnected tables:

- ITEM: Product information
- VENDOR: Vendor details
- STORE_ITEM: Inventory tracking
- VENDOR_ITEM: Product-vendor relationships
- VENDOR_STORE: Vendor-store relationships
- CUSTOMER: Customer information
- ORDER: Sales transactions

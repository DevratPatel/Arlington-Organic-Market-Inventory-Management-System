from flask import Flask, render_template, request, redirect
import psycopg2
import os

app = Flask(__name__)

# --- DATABASE CONNECTION SETUP ---
def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="ArlingtonOrganicMarket",
        user="devrat",
        password=""
    )

# --- HOME PAGE -ø--
@app.route('/')
def index():
    return render_template('index.html')

# --- ADD NEW PRODUCT ---
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
    
    # Link vendor to store
    cur.execute("""
        INSERT INTO VENDOR_STORE (vId, sId)
        VALUES (%s, 1)
        ON CONFLICT (vId, sId) DO NOTHING;
    """, (new_vendor_id,))
    
    # Link vendor to item in VENDOR_ITEM table
    cur.execute("""
        INSERT INTO VENDOR_ITEM (vId, iId)
        VALUES (%s, %s)
        ON CONFLICT (vId, iId) DO NOTHING;
    """, (new_vendor_id, new_item_id))
    
    conn.commit()
    cur.close()
    conn.close()
    return redirect('/store_products')

# --- DELETE PRODUCT ---
@app.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get the vendor IDs associated with this product through VENDOR_ITEM
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
    
    # For each vendor of this product
    for vendor_id in vendor_ids:
        # Check if vendor has any other products
        cur.execute("""
            SELECT COUNT(*) 
            FROM VENDOR_ITEM
            WHERE vId = %s;
        """, (vendor_id,))
        product_count = cur.fetchone()[0]
        
        # If vendor has no other products
        if product_count == 0:
            # Delete from vendor_store first
            cur.execute("DELETE FROM VENDOR_STORE WHERE vId = %s;", (vendor_id,))
            # Then delete the vendor
            cur.execute("DELETE FROM VENDOR WHERE vId = %s;", (vendor_id,))
    
    conn.commit()
    cur.close()
    conn.close()
    return redirect('/store_products')

# --- MODIFY STORE PRODUCTS TO INCLUDE ID ---
@app.route('/store_products')
def store_products():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT i.iId, i.Iname, i.Sprice, si.Scount, i.Category
        FROM STORE_ITEM si
        JOIN ITEM i ON si.iId = i.iId
        WHERE si.sId = 1;
    """)
    products = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('result.html', title="Store Products", 
                         rows=products, 
                         columns=["ID", "Name", "Price", "Stock", "Category"])

# --- QV1: Top 3 items by revenue ---
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
    cur.close()
    conn.close()
    return render_template('result.html', title="Top 3 Revenue-Generating Items", rows=rows, columns=["Item Name", "Total Revenue"])

# --- QV2: Items sold more than 50 units ---
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
    cur.close()
    conn.close()
    return render_template('result.html', title="Items Sold More Than 50 Units", rows=rows, columns=["Item Name", "Total Sold"])

# --- QV3: Customer with highest loyalty score ---
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
    cur.close()
    conn.close()
    return render_template('result.html', title="Top Loyal Customer", rows=rows, columns=["Customer Name", "Loyalty Score"])

# --- QV4: Customers with loyalty between 4 and 5 ---
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
    cur.close()
    conn.close()
    return render_template('result.html', title="Loyalty Score Between 4 and 5", rows=rows, columns=["Customer Name", "Loyalty Score"])

# --- QV5: Total revenue from all items ---
@app.route('/total_revenue')
def total_revenue():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT SUM(TotalRevenue)
        FROM ItemSalesSummary;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('result.html', title="Total Revenue Across All Items", rows=rows, columns=["Total Revenue"])

@app.route('/update_price/<int:product_id>', methods=['POST'])
def update_product_price(product_id):
    new_price = float(request.form['new_price'])
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        UPDATE ITEM 
        SET Sprice = %s 
        WHERE iId = %s;
    """, (new_price, product_id))
    
    conn.commit()
    cur.close()
    conn.close()
    return redirect('/store_products')

if __name__ == '__main__':
    app.run(debug=True, port=5001)

from flask import Flask, render_template, request
import sqlite3
import uuid

app = Flask(__name__)

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id TEXT PRIMARY KEY,
            customer_name TEXT,
            phone TEXT,
            garment TEXT,
            quantity INTEGER,
            price_per_item INTEGER,
            total INTEGER,
            status TEXT
        )
    ''')

    conn.commit()
    conn.close()

init_db()

# ---------------- PRICE CONFIG ----------------
PRICE = {
    "Shirt": 10,
    "Pants": 15,
    "Saree": 25
}

# ---------------- HOME ----------------
@app.route('/')
def home():
    return render_template('create_order.html')

# ---------------- CREATE ORDER ----------------
@app.route('/create', methods=['POST'])
def create_order():
    name = request.form['name']
    phone = request.form['phone']
    garment = request.form['garment']
    quantity = int(request.form['quantity'])

    price_per_item = PRICE.get(garment, 0)
    total = price_per_item * quantity

    order_id = str(uuid.uuid4())[:8]
    status = "RECEIVED"

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (order_id, name, phone, garment, quantity, price_per_item, total, status))

    conn.commit()
    conn.close()

    return f"""
    <h3>Order Created Successfully!</h3>
    <p><b>Order ID:</b> {order_id}</p>
    <p><b>Total:</b> ₹{total}</p>
    <a href="/">Create Another</a><br>
    <a href="/orders">View Orders</a>
    """

# ---------------- VIEW + FILTER ----------------
@app.route('/orders')
def orders():
    status = request.args.get('status')
    search = request.args.get('search')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    query = "SELECT * FROM orders WHERE 1=1"
    params = []

    if status and status != "ALL":
        query += " AND status=?"
        params.append(status)

    if search:
        query += " AND (customer_name LIKE ? OR phone LIKE ?)"
        params.append(f"%{search}%")
        params.append(f"%{search}%")

    cursor.execute(query, params)
    data = cursor.fetchall()

    conn.close()
    return render_template('orders.html', orders=data)

# ---------------- UPDATE STATUS ----------------
@app.route('/update_status', methods=['POST'])
def update_status():
    order_id = request.form['id']
    status = request.form['status']

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))

    conn.commit()
    conn.close()

    return "<a href='/orders'>Back to Orders</a>"

# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # total orders
    cursor.execute("SELECT COUNT(*) FROM orders")
    total_orders = cursor.fetchone()[0]

    # revenue
    cursor.execute("SELECT SUM(total) FROM orders")
    total_revenue = cursor.fetchone()[0] or 0

    # status wise count
    cursor.execute("SELECT status, COUNT(*) FROM orders GROUP BY status")
    status_data = cursor.fetchall()

    conn.close()

    return render_template(
        'dashboard.html',
        total_orders=total_orders,
        total_revenue=total_revenue,
        status_data=status_data
    )

# ---------------- RUN ----------------
if __name__ == '__main__':
    app.run(debug=True)
from datetime import datetime, timedelta
import random
from app.db.models import Customer, Order, OrderItem, Product
from sqlalchemy.orm import Session


def seed_sales_data(db: Session):
  if db.query(Customer).first():
    return

  rng = random.Random(42)

  first_names = [
      "Alex",
      "Jordan",
      "Taylor",
      "Morgan",
      "Sam",
      "Chris",
      "Pat",
      "Riley",
      "Casey",
      "Jamie",
      "Avery",
      "Logan",
      "Cameron",
      "Reese",
      "Quinn",
      "Dakota",
      "Harper",
      "Rowan",
      "Finley",
      "Emerson",
  ]
  last_names = [
      "Smith",
      "Johnson",
      "Williams",
      "Brown",
      "Jones",
      "Garcia",
      "Miller",
      "Davis",
      "Rodriguez",
      "Martinez",
      "Hernandez",
      "Lopez",
      "Gonzalez",
      "Wilson",
      "Anderson",
      "Thomas",
      "Taylor",
      "Moore",
      "Jackson",
      "Martin",
  ]
  cities = [
      "New York",
      "San Francisco",
      "Chicago",
      "Austin",
      "Seattle",
      "Boston",
      "Denver",
      "Atlanta",
      "Los Angeles",
      "Miami",
  ]

  customers = []
  used_emails = set()
  for i in range(50):
    fn = rng.choice(first_names)
    ln = rng.choice(last_names)
    email = f"{fn.lower()}.{ln.lower()}{i+1}@example.com"
    while email in used_emails:
      email = f"{fn.lower()}.{ln.lower()}{rng.randint(100, 999)}@example.com"
    used_emails.add(email)
    created = datetime.utcnow() - timedelta(days=rng.randint(180, 500))
    cust = Customer(
        name=f"{fn} {ln}", email=email, city=rng.choice(cities), created_at=created
    )
    customers.append(cust)

  db.add_all(customers)
  db.flush()

  product_defs = [
      ("Wireless Headphones", "Electronics", 129.99, 85),
      ("Mechanical Keyboard", "Electronics", 89.50, 120),
      ("Ergonomic Mouse", "Electronics", 49.99, 200),
      ("4K Monitor 27in", "Electronics", 349.00, 45),
      ("USB-C Docking Station", "Electronics", 79.99, 90),
      ("Standing Desk", "Furniture", 499.00, 30),
      ("Mesh Office Chair", "Furniture", 229.00, 50),
      ("Bookshelf Oak", "Furniture", 119.50, 40),
      ("Desk Lamp LED", "Furniture", 34.99, 150),
      ("Filing Cabinet", "Furniture", 89.00, 60),
      ("Coffee Maker", "Home", 65.00, 110),
      ("Stainless Water Bottle", "Home", 24.50, 300),
      ("Air Purifier", "Home", 149.00, 70),
      ("Ceramic Mug Set", "Home", 19.99, 250),
      ("Desk Plant Pot", "Home", 14.50, 180),
      ("Yoga Mat", "Fitness", 29.99, 140),
      ("Adjustable Dumbbells", "Fitness", 199.00, 40),
      ("Resistance Bands Set", "Fitness", 18.00, 220),
      ("Foam Roller", "Fitness", 22.50, 160),
      ("Smart Jump Rope", "Fitness", 39.99, 95),
      ("Python Data Handbook", "Books", 44.99, 80),
      ("System Design Primer", "Books", 39.50, 100),
      ("Clean Code Guide", "Books", 38.00, 90),
      ("Cloud Architecture", "Books", 49.00, 60),
      ("AI Engineering Notes", "Books", 42.00, 75),
  ]

  products = []
  for name, cat, price, stock in product_defs:
    p = Product(name=name, category=cat, price=price, stock=stock)
    products.append(p)

  db.add_all(products)
  db.flush()

  statuses = ["completed", "completed", "completed", "pending", "cancelled"]
  orders = []
  items = []

  for i in range(500):
    cust = rng.choice(customers)
    status = rng.choice(statuses)
    order_date = datetime.utcnow() - timedelta(
        days=rng.randint(1, 365), hours=rng.randint(0, 23)
    )

    num_items = rng.randint(1, 4)
    chosen_products = rng.sample(products, num_items)

    order_total = 0.0
    current_order_items = []
    for prod in chosen_products:
      qty = rng.randint(1, 3)
      item_price = prod.price
      order_total += qty * item_price
      current_order_items.append((prod.id, qty, item_price))

    order = Order(
        customer_id=cust.id,
        status=status,
        total_amount=round(order_total, 2),
        order_date=order_date,
    )
    orders.append((order, current_order_items))

  for ord_obj, ord_items in orders:
    db.add(ord_obj)
    db.flush()
    for prod_id, qty, unit_price in ord_items:
      item = OrderItem(
          order_id=ord_obj.id,
          product_id=prod_id,
          quantity=qty,
          unit_price=unit_price,
      )
      items.append(item)

  db.add_all(items)
  db.commit()

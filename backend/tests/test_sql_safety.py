from app.guardrails.sql import validate_sql


def test_valid_select_queries():
  valid_queries = [
      "SELECT * FROM customers",
      "select id, name, email from customers where city = 'New York'",
      "SELECT count(*), city FROM customers GROUP BY city ORDER BY count(*) DESC",
      "SELECT o.id, c.name, o.total_amount FROM orders o JOIN customers c ON o.customer_id = c.id WHERE o.status = 'completed'",
      "SELECT p.name, sum(oi.quantity) FROM products p JOIN order_items oi ON p.id = oi.product_id GROUP BY p.name",
      "SELECT * FROM products;",
  ]
  for q in valid_queries:
    valid, res = validate_sql(q)
    assert valid is True, f"expected valid for: {q}, got: {res}"


def test_reject_insert_update_delete():
  bad_queries = [
      "INSERT INTO customers (name, email, city) VALUES ('Hacker', 'h@x.com', 'Nowhere')",
      "UPDATE customers SET email = 'pwned@test.com' WHERE id = 1",
      "DELETE FROM orders WHERE id = 10",
      "delete from customers",
  ]
  for q in bad_queries:
    valid, err = validate_sql(q)
    assert valid is False
    assert "only select statements are allowed" in err.lower() or "disallowed keyword" in err.lower()


def test_reject_schema_modifications():
  bad_queries = [
      "DROP TABLE customers",
      "drop database docpilot",
      "ALTER TABLE customers ADD COLUMN secret text",
      "TRUNCATE TABLE products",
      "CREATE TABLE backdoors (id int)",
      "GRANT ALL PRIVILEGES ON DATABASE docpilot TO public",
      "REVOKE SELECT ON customers FROM readonly_user",
  ]
  for q in bad_queries:
    valid, err = validate_sql(q)
    assert valid is False


def test_reject_sql_comments():
  comment_queries = [
      "SELECT * FROM customers -- ignore rest",
      "SELECT * /* hidden */ FROM products",
      "SELECT id FROM orders WHERE status = 'completed' /* comment */",
      "SELECT * FROM customers WHERE name = 'Alex' -- test",
  ]
  for q in comment_queries:
    valid, err = validate_sql(q)
    assert valid is False
    assert "sql comments are not allowed" in err


def test_reject_multiple_statements_and_injections():
  injection_queries = [
      "SELECT * FROM customers; DROP TABLE orders;",
      "SELECT * FROM products; DELETE FROM products WHERE id > 0;",
      "SELECT 1; SELECT 2",
      "SELECT * FROM orders; UPDATE customers SET name = 'hacked'",
  ]
  for q in injection_queries:
    valid, err = validate_sql(q)
    assert valid is False
    assert "multiple statements are not allowed" in err


def test_reject_select_into():
  valid, err = validate_sql("SELECT * INTO new_table FROM customers")
  assert valid is False
  assert "disallowed keyword" in err


def test_reject_empty_and_whitespace():
  for empty in ["", "   ", "\n\t"]:
    valid, err = validate_sql(empty)
    assert valid is False
    assert "query cannot be empty" in err

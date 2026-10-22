from app.guardrails.pii import mask_pii


def test_mask_emails():
  cases = [
      ("contact me at user@example.com", "contact me at [REDACTED_EMAIL]"),
      ("send to john.doe+support@sub.domain.org please", "send to [REDACTED_EMAIL] please"),
      ("multiple: a@b.com, test_123@xyz.co.in", "multiple: [REDACTED_EMAIL], [REDACTED_EMAIL]"),
  ]
  for inp, exp in cases:
    assert mask_pii(inp) == exp


def test_mask_phone_numbers():
  cases = [
      ("call me at 555-123-4567 today", "call me at [REDACTED_PHONE] today"),
      ("my office line is (555) 987-6543", "my office line is [REDACTED_PHONE]"),
      ("dial +1-555-456-7890 immediately", "dial [REDACTED_PHONE] immediately"),
      ("international: +91 9876543210", "international: [REDACTED_PHONE]"),
      ("dotted: 555.333.2222", "dotted: [REDACTED_PHONE]"),
      ("plain ten digit: 5551234567", "plain ten digit: [REDACTED_PHONE]"),
  ]
  for inp, exp in cases:
    assert mask_pii(inp) == exp


def test_mask_card_and_account_numbers():
  cases = [
      ("card 4111 2222 3333 4444 on file", "card [REDACTED_NUMBER] on file"),
      ("account 1234-5678-9012-3456", "account [REDACTED_NUMBER]"),
      ("raw digits 9876543210123456", "raw digits [REDACTED_NUMBER]"),
  ]
  for inp, exp in cases:
    assert mask_pii(inp) == exp


def test_preserve_non_pii_numbers_and_text():
  clean_texts = [
      "what are the top 5 products in category Electronics?",
      "order 42 was placed on 2026-03-27 with total 129.99",
      "how many customers signed up in year 2025?",
      "tell me about policy section 3.2 paragraph 4",
  ]
  for text in clean_texts:
    assert mask_pii(text) == text


def test_mixed_pii_content():
  raw = "Customer Alice (alice.smith@example.com) with phone 555-234-5678 and card 4111-2222-3333-4444 bought 2 items"
  masked = mask_pii(raw)
  assert "alice.smith@example.com" not in masked
  assert "555-234-5678" not in masked
  assert "4111-2222-3333-4444" not in masked
  assert "[REDACTED_EMAIL]" in masked
  assert "[REDACTED_PHONE]" in masked
  assert "[REDACTED_NUMBER]" in masked

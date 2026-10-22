from app.config import settings
import httpx


async def convert_currency(
    amount: float, from_currency: str, to_currency: str
) -> dict:
  # call free frankfurter api for currency conversion
  src = from_currency.strip().upper()
  dst = to_currency.strip().upper()

  if src == dst:
    return {
        "amount": amount,
        "from": src,
        "to": dst,
        "converted_amount": amount,
        "rate": 1.0,
    }

  url = f"{settings.exchange_api_url.rstrip('/')}/v1/latest"
  params = {"amount": amount, "from": src, "to": dst}

  try:
    async with httpx.AsyncClient(timeout=10.0) as client:
      resp = await client.get(url, params=params)
      if resp.status_code == 200:
        data = resp.json()
        rates = data.get("rates", {})
        if dst in rates:
          return {
              "amount": amount,
              "from": src,
              "to": dst,
              "converted_amount": rates[dst],
              "date": data.get("date"),
          }
        return {
            "error": f"target currency {dst} not found in exchange rates"
        }
      return {
          "error": (
              f"currency api returned status {resp.status_code}: {resp.text}"
          )
      }
  except Exception as exc:
    return {"error": f"failed to reach currency service: {str(exc)}"}

# K Khay Python SDK 🐍

Official Python SDK for the **[K Khay Sovereign Crypto Payment Gateway](https://kkhay.com)**.

Accept non-custodial and custodial crypto payments (USDT, USDC, BNB, ETH, and native tokens across BSC, Polygon, Arbitrum, Base, and Ethereum) directly in your Python applications, Django, FastAPI, Flask, or background bots with **zero third-party dependencies**.

---

## 📦 Installation

```bash
pip install kkhay
```

*(Requires Python 3.8 or newer)*

---

## ⚡ Quick Start

### 1. Initialize Client

```python
from kkhay import KkhayClient

client = KkhayClient(api_key="kkhay_live_your_api_key_here")
```

### 2. Create a Payment Invoice

```python
response = client.create_invoice(
    price_amount=49.99,
    price_currency="USD",
    pay_network="bsc",
    pay_token="USDT",
    order_id="ORDER-9012",
    title="Annual Premium Membership",
    customer_email="merchant-customer@example.com",
    redirect_url="https://myshop.com/orders/success",
    cancel_url="https://myshop.com/cart",
)

invoice = response["invoice"]
print("Invoice ID:", invoice.id)
print("Deposit Address:", invoice.deposit_address)
print("Customer Checkout URL:", invoice.hosted_url)
```

### 3. Retrieve Invoice Status & Blockchain Proofs

```python
data = client.get_invoice("inv_9f81a7b2")
invoice = data.invoice

print(f"Status: {invoice.status}")
for payment in data.payments:
    print(f"Received: {payment.amount_received} {invoice.pay_token}")
    print(f"Tx Hash: {payment.tx_hash} ({payment.confirmations} confirmations)")
```

### 4. List & Paginate Invoices

```python
res = client.list_invoices(page=1, limit=10, status="FINISHED")
print(f"Total Completed Invoices: {res.total_count}")
for inv in res.items:
    print(f"- {inv.id}: ${inv.price_amount} ({inv.status})")
```

---

## 🔐 Webhook / IPN Verification

K Khay cryptographically signs every webhook notification using HMAC-SHA256 with your secret IPN key.

### FastAPI Example

```python
from fastapi import FastAPI, Header, HTTPException, Request
from kkhay import SignatureVerificationError, parse_webhook_event

app = FastAPI()
IPN_SECRET = "whsec_your_secret_key"


@app.post("/api/webhooks/kkhay")
async def handle_kkhay_webhook(
    request: Request,
    x_kkhay_signature: str = Header(None),
):
    body = await request.body()

    try:
        event = parse_webhook_event(
            raw_body=body,
            signature=x_kkhay_signature,
            ipn_secret=IPN_SECRET,
        )
    except SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event.event == "payment.finished":
        print(f"Order {event.order_id} was paid!")
        print(f"Transaction Hash: {event.tx_hash}")

    return {"status": "ok"}
```

### Flask / Django Example

```python
from flask import Flask, abort, request
from kkhay import SignatureVerificationError, parse_webhook_event

app = Flask(__name__)


@app.route("/webhooks/kkhay", methods=["POST"])
def webhook():
    raw_body = request.get_data()
    sig = request.headers.get("x-kkhay-signature")

    try:
        event = parse_webhook_event(raw_body, sig, "whsec_your_secret")
    except SignatureVerificationError:
        abort(400)

    # Process order
    return "OK", 200
```

---

## 🛠️ Error Handling

```python
from kkhay import KkhayApiError, KkhayClient

client = KkhayClient(api_key="invalid_key")

try:
    client.get_invoice("inv_not_exist")
except KkhayApiError as e:
    print(f"HTTP Status: {e.status}")
    print(f"Error Code: {e.code}")
    print(f"Message: {e.message}")
```

---

## 📄 License

MIT © [K Khay](https://kkhay.com)


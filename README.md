<div align="center">

# `kkhay-python`

**Official Python SDK for K Khay — The Non-Custodial Crypto Payment Gateway**

[![PyPI Version](https://img.shields.io/pypi/v/kkhay.svg?style=flat-square)](https://pypi.org/project/kkhay/)
[![CI](https://github.com/boboaungdev/kkhay-python/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/boboaungdev/kkhay-python/actions/workflows/ci.yml)
[![Python Version](https://img.shields.io/badge/python-%3E%3D3.9-3776AB.svg?style=flat-square&logo=python&logoColor=white)](https://pypi.org/project/kkhay/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)

Accept cryptocurrency payments across **190+ blockchain networks** and **500+ tokens** (EVM, Bitcoin, Solana, TON, Tron, and XRPL) with **zero custody** and automatic direct-to-wallet settlement. Works natively with **FastAPI, Django, Flask, Celery, or background automation bots** with **zero external dependencies**.

[Gateway Dashboard](https://gateway.kkhay.com) • [API Keys](https://gateway.kkhay.com/dashboard/keys) • [Website](https://kkhay.com)

</div>

---

## ⚡ Key Highlights

- 🛡️ **100% Non-Custodial**: Payments settle directly to your destination blockchain address in seconds. K Khay never holds your private keys or customer funds.
- 🌐 **190+ Networks Supported**: 
  - **EVM Networks**: BNB Smart Chain (`bsc`), Polygon (`polygon`), Arbitrum (`arbitrum`), Base (`base`), Ethereum (`eth`), Optimism (`optimism`), Avalanche (`avalanche`), and 180+ more.
  - **UTXO Networks**: Bitcoin (`btc`), Dogecoin (`doge`), Litecoin (`ltc`), Bitcoin Cash (`bch`).
  - **High-Throughput Chains**: Solana (`sol`), TON (`ton`), Tron (`trx`), XRP Ledger (`xrp`).
- 🪙 **500+ Cryptocurrencies**: Native coins and tokens (USDT, USDC, BTC, ETH, SOL, TON, BNB, DOGE, XRP, TRX, LTC, and more).
- 🔗 **Branded Hosted Checkouts**: Instant hosted checkout URLs with dynamic QR codes, live blockchain polling, and wallet deep links.
- 🔔 **Cryptographic Webhooks**: Timing-safe HMAC-SHA256 signature verification (`x-kkhay-signature` via `hmac.compare_digest`).
- 🪶 **Zero External Dependencies**: Pure Python standard library implementation (`urllib.request`, `hmac`, `hashlib`, `json`, `dataclasses`).

---

## 📦 Installation

```bash
pip install kkhay
```

*(Requires Python 3.9 or newer)*

---

## 🚀 Quickstart

### 1. Initialize the Client

Obtain your API Key from the [K Khay Gateway Dashboard](https://gateway.kkhay.com/dashboard/keys).

```python
from kkhay import KkhayClient

client = KkhayClient(api_key="kkhay_live_your_api_key_here")
```

Custom base URL and timeout can be configured:

```python
client = KkhayClient(
    api_key="kkhay_live_your_api_key_here",
    base_url="https://api.kkhay.com",
    timeout=30.0,
)
```

---

### 2. Create a Crypto Payment Invoice

```python
from kkhay import KkhayClient, InvoiceTypeEnum

client = KkhayClient(api_key="kkhay_live_your_api_key_here")

response = client.create_invoice(
    amount=49.99,
    currency="USD",
    pay_network="bsc",       # or "polygon", "solana", "bitcoin", "tron", etc.
    pay_token="USDT",        # or "USDC", "BTC", "ETH", "SOL", "TON", etc.
    order_id="ORD-9012",
    title="Pro Tier Membership",
    customer_email="buyer@example.com",
    redirect_url="https://myshop.com/success",
    cancel_url="https://myshop.com/cart",
    type=InvoiceTypeEnum.PAYMENT,
)

invoice = response["invoice"]
print("Invoice ID:", invoice.id)
print("Deposit Address:", invoice.deposit_address)
print("Checkout URL:", invoice.hosted_url)
```

---

### 3. Retrieve Invoice Status & Blockchain Confirmations

```python
data = client.get_invoice("0192e2b3-5776-791b-8524-77a834164b12")
invoice = data.invoice

print(f"Status: {invoice.status}") # WAITING, PAID, EXPIRED, CANCELED

for payment in data.payments:
    print(f"Received: {payment.amount_received} on tx {payment.tx_hash}")
    print(f"Confirmations: {payment.confirmations}")
```

---

### 4. List & Paginate Invoices

```python
from kkhay import InvoiceStatusEnum

res = client.list_invoices(
    page=1,
    limit=10,
    status=InvoiceStatusEnum.PAID,
)

print(f"Total Settled: {res.total_count}")
for inv in res.items:
    print(f"- {inv.id}: ${inv.amount} {inv.currency} ({inv.status})")
```

---

### 5. Check API Health

```python
health = client.check_health()
print("Gateway API Status:", health.get("status"))
```

---

## 🔐 Webhook / IPN Verification

K Khay cryptographically signs every webhook notification using HMAC-SHA256 with your secret IPN key.

### FastAPI Example

```python
import os
from fastapi import FastAPI, Header, HTTPException, Request
from kkhay import (
    SignatureVerificationError,
    WebhookEventTypeEnum,
    parse_webhook_event,
)

app = FastAPI()
IPN_SECRET = os.getenv("KKHAY_IPN_SECRET", "whsec_your_secret_key")


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
        raise HTTPException(status_code=401, detail="Invalid signature")

    if event.event == WebhookEventTypeEnum.PAYMENT_PAID or event.event == WebhookEventTypeEnum.PAYMENT_FINISHED:
        print(f"Order {event.order_id} fulfilled!")
        print(f"Blockchain Tx: {event.tx_hash}")

    return {"status": "ok"}
```

---

### Django / Flask Example

```python
import os
from flask import Flask, abort, request
from kkhay import (
    SignatureVerificationError,
    WebhookEventTypeEnum,
    parse_webhook_event,
)

app = Flask(__name__)
IPN_SECRET = os.getenv("KKHAY_IPN_SECRET", "whsec_your_secret")


@app.route("/webhooks/kkhay", methods=["POST"])
def webhook():
    raw_body = request.get_data()
    sig = request.headers.get("x-kkhay-signature")

    try:
        event = parse_webhook_event(raw_body, sig, IPN_SECRET)
    except SignatureVerificationError:
        abort(401)

    if event.event in (WebhookEventTypeEnum.PAYMENT_PAID, WebhookEventTypeEnum.PAYMENT_FINISHED):
        # Fulfill order in database
        pass

    return {"ok": True}, 200
```

---

## 📚 Constants & Enums

### Invoice Status (`InvoiceStatusEnum`)

Matches PostgreSQL schema enum values:

| Constant | Value | Description |
| :--- | :--- | :--- |
| `InvoiceStatusEnum.WAITING` | `'WAITING'` | Awaiting customer payment on blockchain |
| `InvoiceStatusEnum.PAID` | `'PAID'` | Transaction confirmed and settled |
| `InvoiceStatusEnum.EXPIRED` | `'EXPIRED'` | Payment window closed without full payment |
| `InvoiceStatusEnum.CANCELED` | `'CANCELED'` | Invoice explicitly voided or canceled |

### Invoice Type (`InvoiceTypeEnum`)

| Constant | Value | Description |
| :--- | :--- | :--- |
| `InvoiceTypeEnum.PAYMENT` | `'PAYMENT'` | Standard e-commerce payment |
| `InvoiceTypeEnum.DONATION` | `'DONATION'` | Open-amount contribution |
| `InvoiceTypeEnum.SUBSCRIPTION` | `'SUBSCRIPTION'` | Recurring subscription billing |

### Webhook Event Types (`WebhookEventTypeEnum`)

| Constant | Value | Description |
| :--- | :--- | :--- |
| `WebhookEventTypeEnum.PAYMENT_PAID` | `'payment.paid'` | Payment confirmed on blockchain |
| `WebhookEventTypeEnum.PAYMENT_FINISHED` | `'payment.finished'` | Invoice completed and finalized |
| `WebhookEventTypeEnum.PAYMENT_CONFIRMING` | `'payment.confirming'` | Transaction detected, awaiting confirmations |
| `WebhookEventTypeEnum.PAYMENT_FAILED` | `'payment.failed'` | Transaction failed on-chain |
| `WebhookEventTypeEnum.INVOICE_CANCELED` | `'invoice.canceled'` | Invoice was canceled |

---

## 🌐 Supported Blockchains (190+ Networks)

| Network | Code | Type | Popular Tokens |
| :--- | :--- | :--- | :--- |
| **BNB Smart Chain** | `bsc` | EVM | USDT, USDC, BNB, DAI |
| **Polygon** | `polygon` | EVM | USDT, USDC, POL, WETH |
| **Arbitrum One** | `arbitrum` | EVM (L2) | USDT, USDC, ARB, ETH |
| **Base** | `base` | EVM (L2) | USDC, ETH, DAI |
| **Ethereum** | `eth` | EVM (L1) | USDT, USDC, ETH, DAI |
| **Solana** | `solana` / `sol` | High-Throughput | SOL, USDT, USDC |
| **TON Network** | `ton` | High-Throughput | TON, USDT |
| **Tron** | `tron` / `trx` | TRC-20 | TRX, USDT, USDC |
| **Bitcoin** | `bitcoin` / `btc`| UTXO | BTC |
| **XRP Ledger** | `xrpl` / `xrp` | Ledger | XRP |
| **Dogecoin** | `dogecoin` / `doge`| UTXO | DOGE |
| **Litecoin** | `litecoin` / `ltc` | UTXO | LTC |

*And 180+ additional networks dynamically routed through K Khay.*

---

## 📄 License

MIT © [K Khay](https://kkhay.com)

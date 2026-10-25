import hashlib
import hmac
import json
import unittest
from typing import Any, Dict, Optional

from kkhay import (
    CreateInvoiceRequest,
    GetInvoiceResponse,
    InvoiceStatusEnum,
    InvoiceTypeEnum,
    KkhayApiError,
    KkhayClient,
    KkhayInvoice,
    KkhayPaymentRecord,
    KkhayWebhookEvent,
    ListInvoicesResponse,
    SignatureVerificationError,
    WebhookEventTypeEnum,
    parse_webhook_event,
    verify_webhook_signature,
)


class MockKkhayClient(KkhayClient):
    """Subclass that records requests without network I/O for unit testing."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_path: Optional[str] = None
        self.last_method: Optional[str] = None
        self.last_data: Optional[Dict[str, Any]] = None
        self.mock_response: Dict[str, Any] = {}

    def _request(
        self,
        path: str,
        method: str = "GET",
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        self.last_path = path
        self.last_method = method
        self.last_data = data
        return self.mock_response


class TestKkhaySDK(unittest.TestCase):
    def test_client_initialization(self):
        client = KkhayClient(api_key="kkhay_live_test_12345")
        self.assertEqual(client.base_url, "https://api.kkhay.com")
        self.assertEqual(client.timeout, 30.0)
        self.assertEqual(client.VERSION, "1.0.4")

        custom = KkhayClient(
            api_key="kkhay_custom",
            base_url="https://gateway.internal/",
            timeout=15.0,
        )
        self.assertEqual(custom.base_url, "https://gateway.internal")
        self.assertEqual(custom.timeout, 15.0)

    def test_client_invalid_api_key(self):
        with self.assertRaises(ValueError):
            KkhayClient(api_key="")
        with self.assertRaises(ValueError):
            KkhayClient(api_key="   ")

    def test_get_url(self):
        api_client = KkhayClient(api_key="key", base_url="https://api.kkhay.com")
        self.assertEqual(
            api_client._get_url("/v1/gateway/invoices"),
            "https://api.kkhay.com/v1/gateway/invoices",
        )
        self.assertEqual(
            api_client._get_url("v1/gateway/invoices"),
            "https://api.kkhay.com/v1/gateway/invoices",
        )

        custom_client = KkhayClient(api_key="key", base_url="https://gateway.internal")
        self.assertEqual(
            custom_client._get_url("/v1/gateway/invoices"),
            "https://gateway.internal/api/v1/gateway/invoices",
        )

    def test_constants_and_enums(self):
        self.assertEqual(InvoiceStatusEnum.WAITING, "WAITING")
        self.assertEqual(InvoiceStatusEnum.PAID, "PAID")
        self.assertEqual(InvoiceStatusEnum.EXPIRED, "EXPIRED")
        self.assertEqual(InvoiceStatusEnum.CANCELED, "CANCELED")

        self.assertEqual(InvoiceTypeEnum.PAYMENT, "PAYMENT")
        self.assertEqual(InvoiceTypeEnum.DONATION, "DONATION")
        self.assertEqual(InvoiceTypeEnum.SUBSCRIPTION, "SUBSCRIPTION")

        self.assertEqual(WebhookEventTypeEnum.PAYMENT_PAID, "payment.paid")
        self.assertEqual(WebhookEventTypeEnum.PAYMENT_FINISHED, "payment.finished")
        self.assertEqual(WebhookEventTypeEnum.PAYMENT_CONFIRMING, "payment.confirming")
        self.assertEqual(WebhookEventTypeEnum.PAYMENT_FAILED, "payment.failed")
        self.assertEqual(WebhookEventTypeEnum.INVOICE_CANCELED, "invoice.canceled")

    def test_create_invoice_validation(self):
        client = KkhayClient(api_key="key")

        # Missing or negative amount
        with self.assertRaises(ValueError):
            client.create_invoice(pay_network="bsc", pay_token="USDT", amount=0)
        with self.assertRaises(ValueError):
            client.create_invoice(pay_network="bsc", pay_token="USDT", amount=-5.0)

        # Missing network
        with self.assertRaises(ValueError):
            client.create_invoice(pay_network="", pay_token="USDT", amount=50.0)

        # Missing token
        with self.assertRaises(ValueError):
            client.create_invoice(pay_network="polygon", pay_token="", amount=50.0)

    def test_create_invoice_request_normalization(self):
        req = CreateInvoiceRequest(
            amount=49.99,
            pay_network=" BSC ",
            pay_token=" usdt ",
            currency=" usd ",
            order_id="ORD-100",
        )
        d = req.to_dict()
        self.assertEqual(d["amount"], 49.99)
        self.assertEqual(d["priceAmount"], 49.99)
        self.assertEqual(d["currency"], "USD")
        self.assertEqual(d["priceCurrency"], "USD")
        self.assertEqual(d["payNetwork"], "bsc")
        self.assertEqual(d["payToken"], "USDT")
        self.assertEqual(d["type"], InvoiceTypeEnum.PAYMENT)
        self.assertEqual(d["orderId"], "ORD-100")

    def test_create_invoice_execution(self):
        client = MockKkhayClient(api_key="kkhay_live_test")
        client.mock_response = {
            "ok": True,
            "invoice": {
                "id": "0192e2b3-5776-791b-8524-77a834164b12",
                "gatewayId": "gw_prod_001",
                "amount": 100.0,
                "currency": "USD",
                "payNetwork": "solana",
                "payToken": "USDC",
                "depositAddress": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
                "status": "WAITING",
                "hostedUrl": "https://kkhay.com/gateway/invoice/0192e2b3-5776-791b-8524-77a834164b12",
            },
        }

        res = client.create_invoice(
            amount=100.0,
            pay_network="solana",
            pay_token="usdc",
            title="VIP Membership",
        )

        self.assertEqual(client.last_path, "/v1/gateway/invoices")
        self.assertEqual(client.last_method, "POST")
        self.assertEqual(client.last_data["amount"], 100.0)
        self.assertEqual(client.last_data["payNetwork"], "solana")
        self.assertEqual(client.last_data["payToken"], "USDC")

        inv = res["invoice"]
        self.assertIsInstance(inv, KkhayInvoice)
        self.assertEqual(inv.id, "0192e2b3-5776-791b-8524-77a834164b12")
        self.assertEqual(inv.gateway_id, "gw_prod_001")
        self.assertEqual(inv.amount, 100.0)
        self.assertEqual(inv.price_amount, 100.0)
        self.assertEqual(inv.status, "WAITING")

    def test_get_invoice(self):
        client = MockKkhayClient(api_key="kkhay_live_test")
        client.mock_response = {
            "ok": True,
            "invoice": {
                "id": "inv_9988",
                "gatewayId": "gw_007",
                "amount": 25.0,
                "currency": "USD",
                "status": "PAID",
            },
            "payments": [
                {
                    "id": "pay_1",
                    "txHash": "0xabc123",
                    "amountReceived": "25.00",
                    "confirmations": 12,
                    "status": "SETTLED",
                }
            ],
        }

        with self.assertRaises(ValueError):
            client.get_invoice("")

        resp = client.get_invoice("inv_9988")
        self.assertEqual(client.last_path, "/v1/gateway/invoices/inv_9988")
        self.assertEqual(client.last_method, "GET")
        self.assertTrue(resp.ok)
        self.assertEqual(resp.invoice.id, "inv_9988")
        self.assertEqual(resp.invoice.status, "PAID")
        self.assertEqual(len(resp.payments), 1)
        self.assertEqual(resp.payments[0].tx_hash, "0xabc123")
        self.assertEqual(resp.payments[0].confirmations, 12)

    def test_list_invoices(self):
        client = MockKkhayClient(api_key="kkhay_live_test")
        client.mock_response = {
            "ok": True,
            "items": [
                {
                    "id": "inv_1",
                    "gatewayId": "gw_1",
                    "amount": 50.0,
                    "currency": "USD",
                    "status": "PAID",
                }
            ],
            "totalCount": 1,
            "totalPages": 1,
            "currentPage": 1,
            "limit": 10,
        }

        resp = client.list_invoices(page=1, limit=10, status=InvoiceStatusEnum.PAID)
        self.assertIn("/v1/gateway/invoices?page=1&limit=10&status=PAID", client.last_path)
        self.assertEqual(client.last_method, "GET")
        self.assertEqual(resp.total_count, 1)
        self.assertEqual(len(resp.items), 1)
        self.assertEqual(resp.items[0].id, "inv_1")

    def test_check_health(self):
        client = MockKkhayClient(api_key="kkhay_live_test")
        client.mock_response = {"status": "ok"}

        res = client.check_health()
        self.assertEqual(client.last_path, "/health")
        self.assertEqual(res["status"], "ok")

    def test_webhook_signature_verification(self):
        secret = "whsec_supersecret_test_key_123"
        payload = json.dumps({
            "event": "payment.paid",
            "gateway_id": "gw_12345",
            "invoice_id": "inv_12345",
            "order_id": "ORD-999",
            "amount": 50.00,
            "currency": "USD",
            "pay_token": "USDT",
            "pay_network": "bsc",
            "status": "PAID",
        })

        signature = hmac.new(
            secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        # Valid string payload
        self.assertTrue(verify_webhook_signature(payload, signature, secret))
        # Valid with padded whitespace signature
        self.assertTrue(verify_webhook_signature(payload, f"  {signature}  \n", secret))
        # Valid bytes payload
        self.assertTrue(verify_webhook_signature(payload.encode("utf-8"), signature, secret))
        # Valid dict payload (computed against canonical compact JSON)
        dict_payload = json.loads(payload)
        compact_payload = json.dumps(dict_payload, separators=(",", ":"))
        compact_sig = hmac.new(
            secret.encode("utf-8"),
            compact_payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        self.assertTrue(verify_webhook_signature(dict_payload, compact_sig, secret))

        # Tampered payload
        self.assertFalse(verify_webhook_signature(payload + "tampered", signature, secret))
        # Wrong secret
        self.assertFalse(verify_webhook_signature(payload, signature, "wrong_secret"))
        # None signature
        self.assertFalse(verify_webhook_signature(payload, None, secret))
        # Empty signature
        self.assertFalse(verify_webhook_signature(payload, "", secret))
        # Empty secret
        self.assertFalse(verify_webhook_signature(payload, signature, ""))

    def test_parse_webhook_event(self):
        secret = "whsec_test_secret"
        payload = json.dumps({
            "event": WebhookEventTypeEnum.PAYMENT_PAID,
            "invoice_id": "inv_abc123",
            "gateway_id": "gw_prod_777",
            "order_id": "ORD-5544",
            "amount": 75.50,
            "currency": "USD",
            "pay_amount": "75.50",
            "pay_token": "USDT",
            "pay_network": "polygon",
            "deposit_address": "0x123",
            "status": "PAID",
            "tx_hash": "0x987654321",
            "timestamp": "2026-10-25T19:00:00Z",
        })
        signature = hmac.new(
            secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        event = parse_webhook_event(payload, signature, secret)
        self.assertIsInstance(event, KkhayWebhookEvent)
        self.assertEqual(event.event, "payment.paid")
        self.assertEqual(event.invoice_id, "inv_abc123")
        self.assertEqual(event.gateway_id, "gw_prod_777")
        self.assertEqual(event.amount, 75.50)
        self.assertEqual(event.price_amount, 75.50)
        self.assertEqual(event.currency, "USD")
        self.assertEqual(event.pay_token, "USDT")
        self.assertEqual(event.pay_network, "polygon")
        self.assertEqual(event.tx_hash, "0x987654321")

        # Throws on invalid signature
        with self.assertRaises(SignatureVerificationError):
            parse_webhook_event(payload, "bad_sig", secret)

        # Throws on invalid JSON
        bad_json = "this is not json"
        bad_sig = hmac.new(secret.encode("utf-8"), bad_json.encode("utf-8"), hashlib.sha256).hexdigest()
        with self.assertRaises(ValueError):
            parse_webhook_event(bad_json, bad_sig, secret)

    def test_kkhay_api_error_formatting(self):
        err = KkhayApiError(
            status=404,
            message="Invoice not found",
            code="INVOICE_NOT_FOUND",
            details={"invoice_id": "inv_000"},
        )
        self.assertEqual(err.status, 404)
        self.assertEqual(err.code, "INVOICE_NOT_FOUND")
        self.assertEqual(err.details, {"invoice_id": "inv_000"})
        self.assertIn("Invoice not found", str(err))


if __name__ == "__main__":
    unittest.main()

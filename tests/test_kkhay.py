import hashlib
import hmac
import json
import unittest

from kkhay import (
    KkhayApiError,
    KkhayClient,
    SignatureVerificationError,
    parse_webhook_event,
    verify_webhook_signature,
)


class TestKkhaySDK(unittest.TestCase):
    def test_client_initialization(self):
        client = KkhayClient(api_key="kkhay_live_test_12345")
        self.assertEqual(client.base_url, "https://api.kkhay.com")
        self.assertEqual(client.timeout, 30.0)

        custom = KkhayClient(
            api_key="kkhay_custom",
            base_url="http://localhost:3000",
            timeout=10.0,
        )
        self.assertEqual(custom.base_url, "http://localhost:3000")
        self.assertEqual(custom.timeout, 10.0)

    def test_client_invalid_api_key(self):
        with self.assertRaises(ValueError):
            KkhayClient(api_key="")

    def test_webhook_signature_verification(self):
        secret = "whsec_supersecret_test_key_123"
        payload = json.dumps({
            "event": "payment.finished",
            "invoice_id": "inv_12345",
            "order_id": "ORD-999",
            "pay_amount": "50.00",
            "pay_token": "USDT",
            "pay_network": "bsc",
            "status": "paid",
        })

        signature = hmac.new(
            secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        # Valid
        self.assertTrue(verify_webhook_signature(payload, signature, secret))
        # Tampered
        self.assertFalse(verify_webhook_signature(payload + "tampered", signature, secret))
        # Wrong secret
        self.assertFalse(verify_webhook_signature(payload, signature, "wrong_secret"))
        # None signature
        self.assertFalse(verify_webhook_signature(payload, None, secret))

    def test_parse_webhook_event(self):
        secret = "whsec_test_secret"
        payload = json.dumps({
            "event": "payment.finished",
            "invoice_id": "inv_abc123",
            "price_amount": 50.0,
            "price_currency": "USD",
            "pay_amount": "50.00",
            "pay_token": "USDT",
            "pay_network": "bsc",
            "deposit_address": "0x123",
            "status": "paid",
            "timestamp": "2026-10-07T00:00:00Z",
        })
        signature = hmac.new(
            secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        event = parse_webhook_event(payload, signature, secret)
        self.assertEqual(event.event, "payment.finished")
        self.assertEqual(event.invoice_id, "inv_abc123")
        self.assertEqual(event.pay_token, "USDT")

        # Throws on invalid signature
        with self.assertRaises(SignatureVerificationError):
            parse_webhook_event(payload, "bad_sig", secret)

    def test_kkhay_api_error_formatting(self):
        err = KkhayApiError(400, "Invoice expired", code="INVOICE_EXPIRED")
        self.assertEqual(err.status, 400)
        self.assertEqual(err.code, "INVOICE_EXPIRED")
        self.assertIn("Invoice expired", str(err))


if __name__ == "__main__":
    unittest.main()


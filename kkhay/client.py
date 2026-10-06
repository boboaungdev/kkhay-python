import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional, Union

from .errors import KkhayApiError
from .types import (
    CreateInvoiceRequest,
    GetInvoiceResponse,
    KkhayInvoice,
    KkhayPaymentRecord,
    ListInvoicesResponse,
)


class KkhayClient:
    """
    Official Python SDK client for the K Khay Sovereign Crypto Payment Gateway.

    Example:
    >>> from kkhay import KkhayClient
    >>> client = KkhayClient(api_key="kkhay_live_...")
    >>> res = client.create_invoice(
    ...     price_amount=49.99,
    ...     pay_network="bsc",
    ...     pay_token="USDT",
    ...     title="Pro Subscription",
    ... )
    >>> print("Pay URL:", res["invoice"].hosted_url)
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.kkhay.com",
        timeout: float = 30.0,
    ):
        if not api_key or not isinstance(api_key, str) or not api_key.strip():
            raise ValueError("KkhayClient: A valid 'api_key' string is required.")

        self.api_key: str = api_key.strip()
        self.base_url: str = base_url.rstrip("/")
        self.timeout: float = float(timeout)

    def _get_url(self, path: str) -> str:
        clean_path = path if path.startswith("/") else f"/{path}"
        if self.base_url.endswith("/api") or "api." in self.base_url:
            return f"{self.base_url}{clean_path}"
        return f"{self.base_url}/api{clean_path}"

    def _request(
        self,
        path: str,
        method: str = "GET",
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        url = self._get_url(path)
        headers = {
            "Accept": "application/json",
            "x-api-key": self.api_key,
            "User-Agent": "kkhay-python/1.0.0",
        }

        body_bytes: Optional[bytes] = None
        if data is not None:
            headers["Content-Type"] = "application/json"
            body_bytes = json.dumps(data).encode("utf-8")

        req = urllib.request.Request(url, data=body_bytes, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                status = response.status
                raw = response.read().decode("utf-8")
                if not raw:
                    return {}
                try:
                    return json.loads(raw)
                except json.JSONDecodeError:
                    return {"data": raw}
        except urllib.error.HTTPError as e:
            raw_err = e.read().decode("utf-8") if e.fp else ""
            error_message = f"Request failed with HTTP {e.code}"
            error_code = None
            error_details = None

            if raw_err:
                try:
                    err_json = json.loads(raw_err)
                    error_message = err_json.get("message") or err_json.get("error") or error_message
                    error_code = err_json.get("code")
                    error_details = err_json.get("details")
                except json.JSONDecodeError:
                    error_message = raw_err

            raise KkhayApiError(
                status=e.code,
                message=error_message,
                code=error_code,
                details=error_details,
            ) from e
        except urllib.error.URLError as e:
            if "timed out" in str(e).lower():
                raise KkhayApiError(408, f"Request timed out after {self.timeout}s") from e
            raise KkhayApiError(500, f"Network connection error: {e.reason}") from e
        except Exception as e:
            raise KkhayApiError(500, f"Unexpected error: {e}") from e

    def create_invoice(
        self,
        price_amount: float,
        pay_network: str,
        pay_token: str,
        price_currency: str = "USD",
        order_id: Optional[str] = None,
        title: Optional[str] = None,
        customer_name: Optional[str] = None,
        customer_email: Optional[str] = None,
        redirect_url: Optional[str] = None,
        cancel_url: Optional[str] = None,
        ipn_callback_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Creates a new sovereign crypto payment invoice.

        :return: Dict with keys 'ok' (bool) and 'invoice' (KkhayInvoice)
        """
        if price_amount <= 0:
            raise ValueError("create_invoice: 'price_amount' must be a positive number.")
        if not pay_network:
            raise ValueError("create_invoice: 'pay_network' is required (e.g. 'bsc', 'polygon').")
        if not pay_token:
            raise ValueError("create_invoice: 'pay_token' is required (e.g. 'USDT', 'USDC').")

        payload = CreateInvoiceRequest(
            price_amount=price_amount,
            pay_network=pay_network,
            pay_token=pay_token,
            price_currency=price_currency,
            order_id=order_id,
            title=title,
            customer_name=customer_name,
            customer_email=customer_email,
            redirect_url=redirect_url,
            cancel_url=cancel_url,
            ipn_callback_url=ipn_callback_url,
            metadata=metadata,
        ).to_dict()

        res = self._request("/v1/merchant/invoices", method="POST", data=payload)
        return {
            "ok": bool(res.get("ok", True)),
            "invoice": KkhayInvoice.from_dict(res.get("invoice", {})),
        }

    def get_invoice(self, invoice_id: str) -> GetInvoiceResponse:
        """
        Retrieve details and blockchain confirmations for an invoice by ID.
        """
        if not invoice_id or not str(invoice_id).strip():
            raise ValueError("get_invoice: 'invoice_id' is required.")

        res = self._request(f"/v1/merchant/invoices/{urllib.parse.quote(str(invoice_id).strip())}")
        invoice_raw = res.get("invoice", {})
        payments_raw = res.get("payments", [])

        return GetInvoiceResponse(
            ok=bool(res.get("ok", True)),
            invoice=KkhayInvoice.from_dict(invoice_raw),
            payments=[KkhayPaymentRecord.from_dict(p) for p in payments_raw],
        )

    def list_invoices(
        self,
        page: int = 1,
        limit: int = 20,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> ListInvoicesResponse:
        """
        List and paginate merchant invoices.
        """
        params: Dict[str, str] = {
            "page": str(page),
            "limit": str(limit),
        }
        if status:
            params["status"] = status
        if search:
            params["search"] = search

        query_str = urllib.parse.urlencode(params)
        res = self._request(f"/v1/merchant/invoices?{query_str}")

        items_raw = res.get("items", [])
        return ListInvoicesResponse(
            ok=bool(res.get("ok", True)),
            items=[KkhayInvoice.from_dict(item) for item in items_raw],
            total_count=int(res.get("totalCount", 0)),
            total_pages=int(res.get("totalPages", 1)),
            current_page=int(res.get("currentPage", page)),
            limit=int(res.get("limit", limit)),
        )

    def check_health(self) -> Dict[str, Any]:
        """
        Check connectivity and health of the K Khay API gateway.
        """
        return self._request("/health")


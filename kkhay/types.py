from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, Union

InvoiceStatus = Literal[
    "WAITING",
    "DETECTING",
    "CONFIRMING",
    "SENDING",
    "FINISHED",
    "EXPIRED",
    "CANCELED",
    "FAILED",
]

PaymentNetwork = Literal["bsc", "polygon", "base", "arbitrum", "ethereum", str]


@dataclass
class CreateInvoiceRequest:
    """Parameters required to generate a new crypto invoice."""
    price_amount: float
    pay_network: Union[str, PaymentNetwork]
    pay_token: str
    price_currency: str = "USD"
    order_id: Optional[str] = None
    title: Optional[str] = None
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    redirect_url: Optional[str] = None
    cancel_url: Optional[str] = None
    ipn_callback_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "priceAmount": self.price_amount,
            "payNetwork": self.pay_network,
            "payToken": self.pay_token,
            "priceCurrency": self.price_currency,
        }
        if self.order_id is not None:
            data["orderId"] = self.order_id
        if self.title is not None:
            data["title"] = self.title
        if self.customer_name is not None:
            data["customerName"] = self.customer_name
        if self.customer_email is not None:
            data["customerEmail"] = self.customer_email
        if self.redirect_url is not None:
            data["redirectUrl"] = self.redirect_url
        if self.cancel_url is not None:
            data["cancelUrl"] = self.cancel_url
        if self.ipn_callback_url is not None:
            data["ipnCallbackUrl"] = self.ipn_callback_url
        if self.metadata is not None:
            data["metadata"] = self.metadata
        return data


@dataclass
class KkhayPaymentRecord:
    id: str
    tx_hash: str
    amount_received: str
    confirmations: int
    status: str
    forwarded_tx_hash: Optional[str] = None
    created_at: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KkhayPaymentRecord":
        return cls(
            id=data.get("id", ""),
            tx_hash=data.get("txHash", ""),
            amount_received=str(data.get("amountReceived", "0")),
            confirmations=int(data.get("confirmations", 0)),
            status=data.get("status", ""),
            forwarded_tx_hash=data.get("forwardedTxHash"),
            created_at=data.get("createdAt", ""),
        )


@dataclass
class KkhayInvoice:
    id: str
    merchant_id: str
    price_amount: float
    price_currency: str
    pay_amount: str
    pay_token: str
    pay_network: str
    deposit_address: str
    status: str
    fee_amount: str
    net_amount: str
    hosted_url: str
    expires_at: str
    created_at: str
    order_id: Optional[str] = None
    title: Optional[str] = None
    settlement_mode: Optional[str] = None
    payment_method: Optional[str] = None
    redirect_url: Optional[str] = None
    cancel_url: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KkhayInvoice":
        return cls(
            id=data.get("id", ""),
            merchant_id=data.get("merchantId", ""),
            price_amount=float(data.get("priceAmount", 0)),
            price_currency=data.get("priceCurrency", "USD"),
            pay_amount=str(data.get("payAmount", "0")),
            pay_token=data.get("payToken", ""),
            pay_network=data.get("payNetwork", ""),
            deposit_address=data.get("depositAddress", ""),
            status=data.get("status", "WAITING"),
            fee_amount=str(data.get("feeAmount", "0")),
            net_amount=str(data.get("netAmount", "0")),
            hosted_url=data.get("hostedUrl", ""),
            expires_at=data.get("expiresAt", ""),
            created_at=data.get("createdAt", ""),
            order_id=data.get("orderId"),
            title=data.get("title"),
            settlement_mode=data.get("settlementMode"),
            payment_method=data.get("paymentMethod"),
            redirect_url=data.get("redirectUrl"),
            cancel_url=data.get("cancelUrl"),
        )


@dataclass
class GetInvoiceResponse:
    ok: bool
    invoice: KkhayInvoice
    payments: List[KkhayPaymentRecord] = field(default_factory=list)


@dataclass
class ListInvoicesResponse:
    ok: bool
    items: List[KkhayInvoice]
    total_count: int
    total_pages: int
    current_page: int
    limit: int


@dataclass
class KkhayWebhookEvent:
    event: str
    invoice_id: str
    order_id: Optional[str]
    price_amount: float
    price_currency: str
    pay_amount: str
    pay_token: str
    pay_network: str
    deposit_address: str
    status: str
    timestamp: str
    tx_hash: Optional[str] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KkhayWebhookEvent":
        return cls(
            event=data.get("event", ""),
            invoice_id=data.get("invoice_id", ""),
            order_id=data.get("order_id"),
            price_amount=float(data.get("price_amount", 0)),
            price_currency=data.get("price_currency", "USD"),
            pay_amount=str(data.get("pay_amount", "0")),
            pay_token=data.get("pay_token", ""),
            pay_network=data.get("pay_network", ""),
            deposit_address=data.get("deposit_address", ""),
            status=data.get("status", ""),
            timestamp=data.get("timestamp", ""),
            tx_hash=data.get("tx_hash"),
            raw_data=data,
        )


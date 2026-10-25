from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, Union

# Strict 1:1 alignment with PostgreSQL gatewayInvoiceStatusEnum
InvoiceStatus = Literal[
    "WAITING",
    "PAID",
    "EXPIRED",
    "CANCELED",
]


class InvoiceStatusEnum:
    WAITING = "WAITING"
    PAID = "PAID"
    EXPIRED = "EXPIRED"
    CANCELED = "CANCELED"


InvoiceType = Literal["PAYMENT", "DONATION", "SUBSCRIPTION"]


class InvoiceTypeEnum:
    PAYMENT = "PAYMENT"
    DONATION = "DONATION"
    SUBSCRIPTION = "SUBSCRIPTION"


WebhookEventType = Literal[
    "payment.paid",
    "payment.finished",
    "payment.confirming",
    "payment.failed",
    "invoice.canceled",
]


class WebhookEventTypeEnum:
    PAYMENT_PAID = "payment.paid"
    PAYMENT_FINISHED = "payment.finished"
    PAYMENT_CONFIRMING = "payment.confirming"
    PAYMENT_FAILED = "payment.failed"
    INVOICE_CANCELED = "invoice.canceled"


PaymentNetwork = Union[
    Literal[
        "bsc",
        "polygon",
        "arbitrum",
        "base",
        "ethereum",
        "solana",
        "ton",
        "tron",
        "bitcoin",
        "xrpl",
        "dogecoin",
        "litecoin",
    ],
    str,
]


@dataclass
class CreateInvoiceRequest:
    """Parameters required to generate a new crypto payment invoice."""
    pay_network: PaymentNetwork
    pay_token: str
    amount: Optional[float] = None
    price_amount: Optional[float] = None
    currency: Optional[str] = None
    price_currency: Optional[str] = "USD"
    type: str = InvoiceTypeEnum.PAYMENT
    order_id: Optional[str] = None
    title: Optional[str] = None
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    redirect_url: Optional[str] = None
    cancel_url: Optional[str] = None
    ipn_callback_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        raw_amt = self.amount if self.amount is not None else self.price_amount
        if raw_amt is None or float(raw_amt) <= 0:
            raise ValueError("CreateInvoiceRequest: 'amount' (or 'price_amount') must be a positive number.")

        normalized_amount = float(raw_amt)
        raw_cur = self.currency or self.price_currency or "USD"
        normalized_currency = str(raw_cur).strip().upper()

        data: Dict[str, Any] = {
            "amount": normalized_amount,
            "priceAmount": normalized_amount,
            "currency": normalized_currency,
            "priceCurrency": normalized_currency,
            "payNetwork": str(self.pay_network).strip().lower(),
            "payToken": str(self.pay_token).strip().upper(),
            "type": self.type or InvoiceTypeEnum.PAYMENT,
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
            tx_hash=data.get("txHash") or data.get("tx_hash") or "",
            amount_received=str(data.get("amountReceived") or data.get("amount_received") or "0"),
            confirmations=int(data.get("confirmations", 0)),
            status=data.get("status", ""),
            forwarded_tx_hash=data.get("forwardedTxHash") or data.get("forwarded_tx_hash"),
            created_at=data.get("createdAt") or data.get("created_at") or "",
        )


@dataclass
class KkhayInvoice:
    id: str
    gateway_id: str
    amount: float
    currency: str
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
    type: str = InvoiceTypeEnum.PAYMENT
    order_id: Optional[str] = None
    title: Optional[str] = None
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    settlement_mode: Optional[str] = None
    payment_method: Optional[str] = None
    payout_address: Optional[str] = None
    redirect_url: Optional[str] = None
    cancel_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KkhayInvoice":
        raw_amt = data.get("amount") if data.get("amount") is not None else data.get("priceAmount", 0)
        amt = float(raw_amt or 0)
        cur = str(data.get("currency") or data.get("priceCurrency") or "USD").upper()

        return cls(
            id=data.get("id", ""),
            gateway_id=data.get("gatewayId") or data.get("gateway_id") or "",
            amount=amt,
            currency=cur,
            price_amount=amt,
            price_currency=cur,
            pay_amount=str(data.get("payAmount") or data.get("pay_amount") or "0"),
            pay_token=data.get("payToken") or data.get("pay_token") or "",
            pay_network=data.get("payNetwork") or data.get("pay_network") or "",
            deposit_address=data.get("depositAddress") or data.get("deposit_address") or "",
            status=data.get("status", InvoiceStatusEnum.WAITING),
            fee_amount=str(data.get("feeAmount") or data.get("fee_amount") or "0"),
            net_amount=str(data.get("netAmount") or data.get("net_amount") or "0"),
            hosted_url=data.get("hostedUrl") or data.get("hosted_url") or "",
            expires_at=data.get("expiresAt") or data.get("expires_at") or "",
            created_at=data.get("createdAt") or data.get("created_at") or "",
            type=data.get("type", InvoiceTypeEnum.PAYMENT),
            order_id=data.get("orderId") or data.get("order_id"),
            title=data.get("title"),
            customer_name=data.get("customerName") or data.get("customer_name"),
            customer_email=data.get("customerEmail") or data.get("customer_email"),
            settlement_mode=data.get("settlementMode") or data.get("settlement_mode"),
            payment_method=data.get("paymentMethod") or data.get("payment_method"),
            payout_address=data.get("payoutAddress") or data.get("payout_address"),
            redirect_url=data.get("redirectUrl") or data.get("redirect_url"),
            cancel_url=data.get("cancelUrl") or data.get("cancel_url"),
            metadata=data.get("metadata"),
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
    gateway_id: Optional[str] = None
    amount: float = 0.0
    currency: str = "USD"
    price_amount: float = 0.0
    price_currency: str = "USD"
    order_id: Optional[str] = None
    pay_amount: str = "0"
    pay_token: str = ""
    pay_network: str = ""
    deposit_address: str = ""
    status: str = InvoiceStatusEnum.WAITING
    timestamp: str = ""
    tx_hash: Optional[str] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KkhayWebhookEvent":
        raw_amt = data.get("amount") if data.get("amount") is not None else data.get("price_amount", 0)
        amt = float(raw_amt or 0)
        cur = str(data.get("currency") or data.get("price_currency") or "USD").upper()

        return cls(
            event=data.get("event", ""),
            invoice_id=data.get("invoice_id") or data.get("invoiceId") or "",
            gateway_id=data.get("gateway_id") or data.get("gatewayId"),
            amount=amt,
            currency=cur,
            price_amount=amt,
            price_currency=cur,
            order_id=data.get("order_id") or data.get("orderId"),
            pay_amount=str(data.get("pay_amount") or data.get("payAmount") or "0"),
            pay_token=data.get("pay_token") or data.get("payToken") or "",
            pay_network=data.get("pay_network") or data.get("payNetwork") or "",
            deposit_address=data.get("deposit_address") or data.get("depositAddress") or "",
            status=data.get("status", InvoiceStatusEnum.WAITING),
            timestamp=data.get("timestamp", ""),
            tx_hash=data.get("tx_hash") or data.get("txHash"),
            raw_data=data,
        )

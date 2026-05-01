from __future__ import annotations

from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from .schema import NormalizedModel, RawModel


def _parse_price(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        price = Decimal(value) * Decimal("1000000")
    except (InvalidOperation, TypeError):
        return None
    return float(price.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP).normalize())


def _vendor_name(name: str | None, author: str) -> str:
    if name and ":" in name:
        vendor = name.split(":", 1)[0].strip()
        if vendor:
            return vendor
    return author


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _vendor_name(name: str | None, author: str) -> str:
    if name and ":" in name:
        vendor = name.split(":", 1)[0].strip()
        if vendor:
            return vendor
    return author


def normalize_model(raw: dict, fetched_at: str | None = None) -> NormalizedModel:
    m = RawModel.model_validate(raw)

    if "/" in m.id:
        author, slug = m.id.split("/", 1)
    else:
        author, slug = "", m.id

    params = m.supported_parameters or []
    supports_reasoning = "reasoning" in params or "include_reasoning" in params
    supports_tools = "tools" in params or "tool_choice" in params
    supports_vision = bool(
        m.architecture and m.architecture.modality and "image" in m.architecture.modality
    )

    pricing = m.pricing
    input_price = _parse_price(pricing.prompt if pricing else None)
    output_price = _parse_price(pricing.completion if pricing else None)

    max_completion = m.top_provider.max_completion_tokens if m.top_provider else None

    return NormalizedModel(
        model_id=m.id,
        author=author,
        slug=slug,
        vendor_name=_vendor_name(m.name, author),
        name=m.name or m.id,
        context_length=m.context_length,
        max_completion_tokens=max_completion,
        input_price_usd_per_1m=input_price,
        output_price_usd_per_1m=output_price,
        supports_reasoning=supports_reasoning,
        supports_tools=supports_tools,
        supports_vision=supports_vision,
        fetched_at=fetched_at or _now_utc(),
    )

from __future__ import annotations

from pydantic import BaseModel, Field


class RawModelPricing(BaseModel):
    prompt: str | None = None
    completion: str | None = None
    image: str | None = None
    request: str | None = None


class RawModelTopProvider(BaseModel):
    max_completion_tokens: int | None = None
    is_moderated: bool | None = None


class RawModelArchitecture(BaseModel):
    modality: str | None = None
    tokenizer: str | None = None
    instruct_type: str | None = None


class RawModel(BaseModel):
    id: str
    name: str | None = None
    context_length: int | None = None
    pricing: RawModelPricing | None = None
    top_provider: RawModelTopProvider | None = None
    architecture: RawModelArchitecture | None = None
    supported_parameters: list[str] | None = None
    description: str | None = None
    # Allow extra fields to avoid breaking on new API additions
    model_config = {"extra": "allow"}


class NormalizedModel(BaseModel):
    model_id: str
    author: str
    slug: str
    vendor_name: str
    name: str
    context_length: int | None = None
    max_completion_tokens: int | None = None
    input_price_usd_per_1m: float | None = None
    output_price_usd_per_1m: float | None = None
    supports_reasoning: bool = False
    supports_tools: bool = False
    supports_vision: bool = False
    fetched_at: str = Field(description="ISO8601 UTC timestamp")

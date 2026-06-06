"""Pydantic argument schemas exposed to the LLM for MCP tools."""

from typing import Literal

from pydantic import BaseModel, Field


class SearchKnowledgeBaseArgs(BaseModel):
    """Arguments for RAG search."""

    query: str = Field(description="Поисковый запрос пользователя")
    segment: Literal["b2b", "b2c"] = Field(
        description='Сегмент базы знаний: "b2c" для курсов, "b2b" для корп. клиентов',
    )


class ListB2cProductsArgs(BaseModel):
    """No arguments — returns full B2C catalog."""


class CreatePaymentLinkArgs(BaseModel):
    """Arguments for mock payment link creation."""

    product_id: str = Field(
        description='Код продукта из каталога, например "agents" или "deep-agents"',
    )


class ConfirmPaymentArgs(BaseModel):
    """Arguments for mock payment confirmation."""

    product_id: str = Field(
        description="Код продукта из каталога для подтверждения оплаты",
    )


class SaveLeadArgs(BaseModel):
    """Arguments for lead capture."""

    email: str = Field(description="Email лида")
    phone: str = Field(description="Телефон лида")
    name: str = Field(description="Имя лида")
    product_id: str = Field(description="Код продукта или услуги")
    segment: Literal["b2b", "b2c"] = Field(description="Сегмент лида")


TOOL_ARGS_SCHEMAS: dict[str, type[BaseModel]] = {
    "search_knowledge_base": SearchKnowledgeBaseArgs,
    "list_b2c_products": ListB2cProductsArgs,
    "create_payment_link": CreatePaymentLinkArgs,
    "confirm_payment": ConfirmPaymentArgs,
    "save_lead": SaveLeadArgs,
}

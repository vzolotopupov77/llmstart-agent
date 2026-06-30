"""Pydantic argument schemas exposed to the LLM for MCP tools."""

from typing import Literal

from pydantic import BaseModel, Field


class BranchSearchArgs(BaseModel):
    """Arguments for branch-specific RAG search tools."""

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
    "vector_search": BranchSearchArgs,
    "graph_search": BranchSearchArgs,
    "global_catalog": BranchSearchArgs,
    "text2cypher_tool": BranchSearchArgs,
    "list_b2c_products": ListB2cProductsArgs,
    "create_payment_link": CreatePaymentLinkArgs,
    "confirm_payment": ConfirmPaymentArgs,
    "save_lead": SaveLeadArgs,
}

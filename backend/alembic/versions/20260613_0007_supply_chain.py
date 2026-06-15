"""supply chain module

Revision ID: 20260613_0007
Revises: 20260613_0006
Create Date: 2026-06-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260613_0007"
down_revision: str | None = "20260613_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def audit_columns() -> list[sa.Column]:
    return [
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    ]


def upgrade() -> None:
    location_type = postgresql.ENUM("PURCHASE_WAREHOUSE", "ACCESSORIES_STORAGE", "SUPPORT_STORAGE", "SQUADRON_STORAGE", "TECHNICAL_SECTION_STORAGE", name="supply_chain_inventory_location_type", create_type=False)
    stock_condition = postgresql.ENUM("SERVICEABLE", "UNSERVICEABLE", "UNDER_REPAIR", "PRESERVED", "INSPECTION_REQUIRED", name="supply_chain_stock_condition", create_type=False)
    provision_priority = postgresql.ENUM("CRITICAL", "HIGH", "NORMAL", "LOW", name="supply_chain_provision_priority", create_type=False)
    provision_status = postgresql.ENUM("CREATED", "UNDER_REVIEW", "FULFILLED", "PARTIAL", "REJECTED", "WAITING_PURCHASE", name="supply_chain_provision_request_status", create_type=False)
    reservation_status = postgresql.ENUM("ACTIVE", "CONSUMED", "CANCELED", name="supply_chain_stock_reservation_status", create_type=False)
    purchase_priority = postgresql.ENUM("CRITICAL", "HIGH", "NORMAL", "LOW", name="supply_chain_purchase_priority", create_type=False)
    purchase_request_status = postgresql.ENUM("CREATED", "APPROVED", "ORDERED", "WAITING_DELIVERY", "RECEIVED", "CLOSED", name="supply_chain_purchase_request_status", create_type=False)
    purchase_order_status = postgresql.ENUM("CREATED", "SENT", "PARTIAL_DELIVERY", "COMPLETED", "CANCELED", name="supply_chain_purchase_order_status", create_type=False)
    reception_status = postgresql.ENUM("RECEIVED", "PENDING_QUALITY", "REJECTED", "APPROVED", name="supply_chain_goods_reception_status", create_type=False)
    event_type = postgresql.ENUM("PURCHASE_REQUEST_CREATED", "STOCK_RESERVED", "PURCHASE_ORDER_CREATED", "GOODS_RECEIVED", "QUALITY_APPROVED", "STOCK_TRANSFERRED", "PROVISION_DELIVERED", name="supply_chain_event_type", create_type=False)

    bind = op.get_bind()
    for enum in (location_type, stock_condition, provision_priority, provision_status, reservation_status, purchase_priority, purchase_request_status, purchase_order_status, reception_status, event_type):
        enum.create(bind, checkfirst=True)

    op.create_table(
        "supply_chain_inventory_locations",
        *audit_columns(),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("location_type", location_type, nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sc_locations_org_id", "supply_chain_inventory_locations", ["organization_id"])
    op.create_index("ix_sc_locations_is_deleted", "supply_chain_inventory_locations", ["is_deleted"])

    op.create_table(
        "supply_chain_stock_items",
        *audit_columns(),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("reserved_quantity", sa.Integer(), nullable=False),
        sa.Column("available_quantity", sa.Integer(), nullable=False),
        sa.Column("condition", stock_condition, nullable=False),
        sa.Column("last_updated", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.ForeignKeyConstraint(["location_id"], ["supply_chain_inventory_locations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sc_stock_items_asset_id", "supply_chain_stock_items", ["asset_id"])
    op.create_index("ix_sc_stock_items_location_id", "supply_chain_stock_items", ["location_id"])
    op.create_index("ix_sc_stock_items_is_deleted", "supply_chain_stock_items", ["is_deleted"])

    op.create_table(
        "supply_chain_provision_requests",
        *audit_columns(),
        sa.Column("requesting_department_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_type_requested", sa.String(length=160), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("priority", provision_priority, nullable=False),
        sa.Column("requested_by", sa.String(length=180), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", provision_status, nullable=False),
        sa.ForeignKeyConstraint(["requesting_department_id"], ["departments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sc_prov_req_department_id", "supply_chain_provision_requests", ["requesting_department_id"])
    op.create_index("ix_sc_prov_req_asset_type", "supply_chain_provision_requests", ["asset_type_requested"])
    op.create_index("ix_sc_prov_req_is_deleted", "supply_chain_provision_requests", ["is_deleted"])

    op.create_table(
        "supply_chain_stock_reservations",
        *audit_columns(),
        sa.Column("stock_item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provision_request_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reserved_quantity", sa.Integer(), nullable=False),
        sa.Column("reserved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", reservation_status, nullable=False),
        sa.ForeignKeyConstraint(["provision_request_id"], ["supply_chain_provision_requests.id"]),
        sa.ForeignKeyConstraint(["stock_item_id"], ["supply_chain_stock_items.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sc_res_stock_item_id", "supply_chain_stock_reservations", ["stock_item_id"])
    op.create_index("ix_sc_res_provision_request_id", "supply_chain_stock_reservations", ["provision_request_id"])
    op.create_index("ix_sc_res_is_deleted", "supply_chain_stock_reservations", ["is_deleted"])

    op.create_table(
        "supply_chain_purchase_requests",
        *audit_columns(),
        sa.Column("requested_by_department", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_type", sa.String(length=160), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("justification", sa.Text(), nullable=False),
        sa.Column("priority", purchase_priority, nullable=False),
        sa.Column("status", purchase_request_status, nullable=False),
        sa.ForeignKeyConstraint(["requested_by_department"], ["departments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sc_purchase_req_department", "supply_chain_purchase_requests", ["requested_by_department"])
    op.create_index("ix_sc_purchase_req_asset_type", "supply_chain_purchase_requests", ["asset_type"])
    op.create_index("ix_sc_purchase_req_is_deleted", "supply_chain_purchase_requests", ["is_deleted"])

    op.create_table(
        "supply_chain_suppliers",
        *audit_columns(),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("supplier_code", sa.String(length=80), nullable=False),
        sa.Column("contact_name", sa.String(length=180), nullable=True),
        sa.Column("email", sa.String(length=180), nullable=True),
        sa.Column("phone", sa.String(length=80), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("supplier_code"),
    )
    op.create_index("ix_sc_suppliers_is_deleted", "supply_chain_suppliers", ["is_deleted"])

    op.create_table(
        "supply_chain_purchase_orders",
        *audit_columns(),
        sa.Column("purchase_request_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("supplier_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_number", sa.String(length=120), nullable=False),
        sa.Column("ordered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expected_delivery", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", purchase_order_status, nullable=False),
        sa.ForeignKeyConstraint(["purchase_request_id"], ["supply_chain_purchase_requests.id"]),
        sa.ForeignKeyConstraint(["supplier_id"], ["supply_chain_suppliers.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_number"),
    )
    op.create_index("ix_sc_po_purchase_request_id", "supply_chain_purchase_orders", ["purchase_request_id"])
    op.create_index("ix_sc_po_supplier_id", "supply_chain_purchase_orders", ["supplier_id"])
    op.create_index("ix_sc_po_is_deleted", "supply_chain_purchase_orders", ["is_deleted"])

    op.create_table(
        "supply_chain_goods_receptions",
        *audit_columns(),
        sa.Column("purchase_order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("received_by", sa.String(length=180), nullable=False),
        sa.Column("documentation_complete", sa.Boolean(), nullable=False),
        sa.Column("quality_pending", sa.Boolean(), nullable=False),
        sa.Column("status", reception_status, nullable=False),
        sa.ForeignKeyConstraint(["purchase_order_id"], ["supply_chain_purchase_orders.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sc_receptions_purchase_order_id", "supply_chain_goods_receptions", ["purchase_order_id"])
    op.create_index("ix_sc_receptions_is_deleted", "supply_chain_goods_receptions", ["is_deleted"])

    op.create_table(
        "supply_chain_procurement_quality_checks",
        *audit_columns(),
        sa.Column("goods_reception_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("inspector_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("documentation_valid", sa.Boolean(), nullable=False),
        sa.Column("physical_condition_valid", sa.Boolean(), nullable=False),
        sa.Column("approved", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["goods_reception_id"], ["supply_chain_goods_receptions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sc_quality_goods_reception_id", "supply_chain_procurement_quality_checks", ["goods_reception_id"])
    op.create_index("ix_sc_quality_inspector_id", "supply_chain_procurement_quality_checks", ["inspector_id"])
    op.create_index("ix_sc_quality_is_deleted", "supply_chain_procurement_quality_checks", ["is_deleted"])

    op.create_table(
        "supply_chain_events",
        *audit_columns(),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", event_type, nullable=False),
        sa.Column("performed_by", sa.String(length=180), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("origin_location_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("destination_location_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.ForeignKeyConstraint(["destination_location_id"], ["supply_chain_inventory_locations.id"]),
        sa.ForeignKeyConstraint(["origin_location_id"], ["supply_chain_inventory_locations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sc_events_asset_id", "supply_chain_events", ["asset_id"])
    op.create_index("ix_sc_events_origin_location_id", "supply_chain_events", ["origin_location_id"])
    op.create_index("ix_sc_events_destination_location_id", "supply_chain_events", ["destination_location_id"])
    op.create_index("ix_sc_events_is_deleted", "supply_chain_events", ["is_deleted"])


def downgrade() -> None:
    op.drop_index("ix_sc_events_is_deleted", table_name="supply_chain_events")
    op.drop_index("ix_sc_events_destination_location_id", table_name="supply_chain_events")
    op.drop_index("ix_sc_events_origin_location_id", table_name="supply_chain_events")
    op.drop_index("ix_sc_events_asset_id", table_name="supply_chain_events")
    op.drop_table("supply_chain_events")
    op.drop_index("ix_sc_quality_is_deleted", table_name="supply_chain_procurement_quality_checks")
    op.drop_index("ix_sc_quality_inspector_id", table_name="supply_chain_procurement_quality_checks")
    op.drop_index("ix_sc_quality_goods_reception_id", table_name="supply_chain_procurement_quality_checks")
    op.drop_table("supply_chain_procurement_quality_checks")
    op.drop_index("ix_sc_receptions_is_deleted", table_name="supply_chain_goods_receptions")
    op.drop_index("ix_sc_receptions_purchase_order_id", table_name="supply_chain_goods_receptions")
    op.drop_table("supply_chain_goods_receptions")
    op.drop_index("ix_sc_po_is_deleted", table_name="supply_chain_purchase_orders")
    op.drop_index("ix_sc_po_supplier_id", table_name="supply_chain_purchase_orders")
    op.drop_index("ix_sc_po_purchase_request_id", table_name="supply_chain_purchase_orders")
    op.drop_table("supply_chain_purchase_orders")
    op.drop_index("ix_sc_suppliers_is_deleted", table_name="supply_chain_suppliers")
    op.drop_table("supply_chain_suppliers")
    op.drop_index("ix_sc_purchase_req_is_deleted", table_name="supply_chain_purchase_requests")
    op.drop_index("ix_sc_purchase_req_asset_type", table_name="supply_chain_purchase_requests")
    op.drop_index("ix_sc_purchase_req_department", table_name="supply_chain_purchase_requests")
    op.drop_table("supply_chain_purchase_requests")
    op.drop_index("ix_sc_res_is_deleted", table_name="supply_chain_stock_reservations")
    op.drop_index("ix_sc_res_provision_request_id", table_name="supply_chain_stock_reservations")
    op.drop_index("ix_sc_res_stock_item_id", table_name="supply_chain_stock_reservations")
    op.drop_table("supply_chain_stock_reservations")
    op.drop_index("ix_sc_prov_req_is_deleted", table_name="supply_chain_provision_requests")
    op.drop_index("ix_sc_prov_req_asset_type", table_name="supply_chain_provision_requests")
    op.drop_index("ix_sc_prov_req_department_id", table_name="supply_chain_provision_requests")
    op.drop_table("supply_chain_provision_requests")
    op.drop_index("ix_sc_stock_items_is_deleted", table_name="supply_chain_stock_items")
    op.drop_index("ix_sc_stock_items_location_id", table_name="supply_chain_stock_items")
    op.drop_index("ix_sc_stock_items_asset_id", table_name="supply_chain_stock_items")
    op.drop_table("supply_chain_stock_items")
    op.drop_index("ix_sc_locations_is_deleted", table_name="supply_chain_inventory_locations")
    op.drop_index("ix_sc_locations_org_id", table_name="supply_chain_inventory_locations")
    op.drop_table("supply_chain_inventory_locations")

    bind = op.get_bind()
    for enum_name in (
        "supply_chain_event_type",
        "supply_chain_goods_reception_status",
        "supply_chain_purchase_order_status",
        "supply_chain_purchase_request_status",
        "supply_chain_purchase_priority",
        "supply_chain_stock_reservation_status",
        "supply_chain_provision_request_status",
        "supply_chain_provision_priority",
        "supply_chain_stock_condition",
        "supply_chain_inventory_location_type",
    ):
        postgresql.ENUM(name=enum_name).drop(bind, checkfirst=True)

from datetime import timedelta

from odoo import fields, models


class RevivaIQDeadStockService(models.AbstractModel):
    _name = "revivaiq.dead.stock.service"
    _description = "RevivaIQ Dead Stock Analytics Service"

    SAFE_REGENERATION_STATES = ["draft", "active"]
    PROTECTED_OPERATIONAL_STATES = ["reviewed", "resolved"]

    def _cleanup_stale_generated_dead_stock(self, company, limit):
        stale_records = self.env["revivaiq.dead.stock"].search(
            [
                ("company_id", "=", company.id),
                ("analysis_source", "=", "generated"),
                ("state", "in", self.SAFE_REGENERATION_STATES),
            ],
            limit=limit,
            order="id asc",
        )

        cleanup_count = len(stale_records)
        stale_records.unlink()
        return cleanup_count

    def generate_dead_stock_analysis(self):
        company = self.env.company

        dashboard = self.env["revivaiq.dashboard"].search(
            [("company_id", "=", company.id)],
            limit=1,
        )

        threshold_days = dashboard.dead_stock_days_threshold or 60
        minimum_quantity = dashboard.dead_stock_min_quantity or 1.0
        batch_limit = dashboard.dead_stock_max_batch_limit or 500
        safe_limit = min(max(batch_limit, 50), 5000)

        now = fields.Datetime.now()
        today = fields.Date.today()
        cutoff_date = today - timedelta(days=threshold_days)

        cleanup_count = self._cleanup_stale_generated_dead_stock(company, safe_limit)

        products = self.env["product.product"].search(
            [
                ("sale_ok", "=", True),
                ("company_id", "in", [False, company.id]),
            ],
            limit=safe_limit,
            order="id desc",
        )

        valid_products = products.filtered(
            lambda product: product.qty_available > minimum_quantity
        )

        DeadStock = self.env["revivaiq.dead.stock"]
        created_records = 0
        skipped_protected_records = 0

        for product in valid_products:
            protected_existing = DeadStock.search(
                [
                    ("product_id", "=", product.id),
                    ("company_id", "=", company.id),
                    ("state", "in", self.PROTECTED_OPERATIONAL_STATES),
                ],
                limit=1,
            )

            if protected_existing:
                skipped_protected_records += 1
                continue

            sale_line = self.env["sale.order.line"].search(
                [
                    ("product_id", "=", product.id),
                    ("order_id.company_id", "=", company.id),
                    ("order_id.state", "in", ["sale", "done"]),
                ],
                order="order_id.date_order desc",
                limit=1,
            )

            if sale_line:
                last_sale_date = sale_line.order_id.date_order.date()

                if last_sale_date > cutoff_date:
                    continue

                days_without_sale = (today - last_sale_date).days
            else:
                last_sale_date = False
                days_without_sale = threshold_days

            inventory_value = product.qty_available * product.standard_price

            if days_without_sale >= threshold_days * 2:
                risk_level = "critical"
                risk_score = 95
            elif days_without_sale >= threshold_days:
                risk_level = "high"
                risk_score = 80
            else:
                risk_level = "medium"
                risk_score = 55

            DeadStock.create({
                "product_id": product.id,
                "company_id": company.id,
                "quantity_on_hand": product.qty_available,
                "quantity_sold": 0.0,
                "last_sale_date": last_sale_date,
                "days_without_sale": days_without_sale,
                "inventory_value": inventory_value,
                "risk_level": risk_level,
                "risk_score": risk_score,
                "state": "active",
                "analysis_source": "generated",
                "analysis_run_date": now,
                "note": "Dead stock candidate detected by RevivaIQ analytics.",
            })

            created_records += 1

        return {
            "success": True,
            "created_records": created_records,
            "updated_records": 0,
            "cleanup_count": cleanup_count,
            "skipped_protected_records": skipped_protected_records,
        }
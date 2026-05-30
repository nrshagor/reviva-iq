from datetime import timedelta

from odoo import fields, models


class RevivaIQDeadStockService(models.AbstractModel):
    _name = "revivaiq.dead.stock.service"
    _description = "RevivaIQ Dead Stock Analytics Service"

    def generate_dead_stock_analysis(self):
        dashboard = self.env["revivaiq.dashboard"].search(
            [("company_id", "=", self.env.company.id)],
            limit=1,
        )

        threshold_days = dashboard.dead_stock_days_threshold or 60
        minimum_quantity = dashboard.dead_stock_min_quantity or 1.0
        batch_limit = dashboard.dead_stock_max_batch_limit or 500

        today = fields.Date.today()
        cutoff_date = today - timedelta(days=threshold_days)

        products = self.env["product.product"].search(
            [
                ("sale_ok", "=", True),
                ("company_id", "in", [False, self.env.company.id]),
            ],
            limit=batch_limit,
            order="id desc",
        )

        valid_products = products.filtered(
            lambda product: product.qty_available > minimum_quantity
        )

        DeadStock = self.env["revivaiq.dead.stock"]
        created_records = 0

        for product in valid_products:
            sale_line = self.env["sale.order.line"].search(
                [
                    ("product_id", "=", product.id),
                    ("order_id.company_id", "=", self.env.company.id),
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
            elif days_without_sale >= threshold_days:
                risk_level = "high"
            else:
                risk_level = "medium"

            existing = DeadStock.search(
                [
                    ("product_id", "=", product.id),
                    ("company_id", "=", self.env.company.id),
                ],
                limit=1,
            )

            vals = {
                "product_id": product.id,
                "company_id": self.env.company.id,
                "quantity_on_hand": product.qty_available,
                "quantity_sold": 0.0,
                "last_sale_date": last_sale_date,
                "days_without_sale": days_without_sale,
                "inventory_value": inventory_value,
                "risk_level": risk_level,
                "note": "Dead stock candidate detected by RevivaIQ analytics.",
            }

            if existing:
                existing.write(vals)
            else:
                DeadStock.create(vals)
                created_records += 1

        return {
            "success": True,
            "created_records": created_records,
        }
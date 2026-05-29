from datetime import timedelta

from odoo import fields, models


class RevivaIQDeadStockService(models.AbstractModel):
    _name = "revivaiq.dead.stock.service"
    _inherit = "revivaiq.analytics.service"
    _description = "RevivaIQ Dead Stock Analytics Service"


    def generate_dead_stock_analysis(self):
        dashboard = self.env["revivaiq.dashboard"].search([], limit=1)

        threshold_days = dashboard.dead_stock_days_threshold or 60
        minimum_quantity = dashboard.dead_stock_min_quantity or 1.0

        today = fields.Date.today()
        cutoff_date = today - timedelta(days=threshold_days)

        batch_limit = dashboard.dead_stock_max_batch_limit or 500

        products = self._search_limited(
            "product.product",
            domain=[("sale_ok", "=", True)],
            limit=batch_limit,
            order="id desc",
        )

        valid_products = products.filtered(
            lambda product: product.qty_available > minimum_quantity
        )

        if not valid_products:
            return {
                "success": True,
                "created_records": 0,
                "threshold_days": threshold_days,
            }

        product_ids = valid_products.ids

        existing_records = self.env["revivaiq.dead.stock"].search(
            [
                ("product_id", "in", product_ids),
                ("state", "!=", "resolved"),
                ("company_id", "=", self.env.company.id),
            ]
        )

        existing_product_ids = set(existing_records.mapped("product_id").ids)

        sale_lines = self.env["sale.order.line"].search(
            [
                ("product_id", "in", product_ids),
                ("order_id.state", "in", ["sale", "done"]),
                ("company_id", "=", self.env.company.id),
            ],
            order="create_date desc",
        )

        last_sale_by_product = {}

        for line in sale_lines:
            if line.product_id.id not in last_sale_by_product:
                last_sale_by_product[line.product_id.id] = line.create_date.date()

        create_values = []

        for product in valid_products:
            if product.id in existing_product_ids:
                continue

            last_sale_date = last_sale_by_product.get(product.id)
            days_without_sale = threshold_days

            if last_sale_date:
                days_without_sale = (today - last_sale_date).days

            if last_sale_date and last_sale_date > cutoff_date:
                continue

            risk_level, risk_score = self._calculate_dead_stock_risk(
                days_without_sale
            )

            create_values.append(
                {
                    "product_id": product.id,
                    "company_id": self.env.company.id,
                    "quantity_on_hand": product.qty_available,
                    "quantity_sold": 0,
                    "last_sale_date": last_sale_date,
                    "days_without_sale": days_without_sale,
                    "inventory_value": product.qty_available * product.standard_price,
                    "risk_level": risk_level,
                    "risk_score": risk_score,
                    "state": "active",
                    "note": "Generated from RevivaIQ dead stock analytics engine.",
                }
            )

        if create_values:
            self.env["revivaiq.dead.stock"].create(create_values)

        return {
            "success": True,
            "created_records": len(create_values),
            "threshold_days": threshold_days,
        }

    def _calculate_dead_stock_risk(self, days_without_sale):
        if days_without_sale >= 120:
            return "critical", 95

        if days_without_sale >= 90:
            return "high", 80

        if days_without_sale >= 60:
            return "medium", 60

        return "low", 30
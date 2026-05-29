from odoo import fields


class CustomerRecoveryService:
    def __init__(self, env):
        self.env = env

    def run_customer_recovery_analysis(self, dashboard):
        company = self.env.company
        inactivity_days = dashboard.customer_inactivity_days_threshold or 90
        batch_limit = dashboard.customer_batch_limit or 500

        cutoff_date = fields.Date.subtract(fields.Date.today(), days=inactivity_days)

        partners = self.env["res.partner"].search(
            [
                ("company_id", "in", [False, company.id]),
                ("customer_rank", ">", 0),
                ("active", "=", True),
            ],
            limit=batch_limit,
            order="id desc",
        )

        Insight = self.env["revivaiq.customer.insight"]
        created_count = 0

        for partner in partners:
            orders = self.env["sale.order"].search(
                [
                    ("partner_id", "=", partner.id),
                    ("company_id", "=", company.id),
                    ("state", "in", ["sale", "done"]),
                ],
                order="date_order desc",
                limit=100,
            )

            if not orders:
                continue

            last_order = orders[0]
            last_order_date = last_order.date_order.date()

            if last_order_date > cutoff_date:
                continue

            days_inactive = (fields.Date.today() - last_order_date).days
            total_revenue = sum(orders.mapped("amount_total"))
            total_order_count = len(orders)

            recovery_score = min(100, int((days_inactive / inactivity_days) * 50))

            if total_revenue >= 5000:
                recovery_score = min(100, recovery_score + 30)
            elif total_revenue >= 1000:
                recovery_score = min(100, recovery_score + 15)

            customer_status = self._get_customer_status(days_inactive, inactivity_days)
            recovery_stage = "review" if recovery_score >= 70 else "new"

            existing = Insight.search(
                [
                    ("partner_id", "=", partner.id),
                    ("company_id", "=", company.id),
                ],
                limit=1,
            )

            vals = {
                "partner_id": partner.id,
                "company_id": company.id,
                "total_order_count": total_order_count,
                "total_revenue": total_revenue,
                "last_order_date": last_order_date,
                "days_inactive": days_inactive,
                "recovery_score": recovery_score,
                "customer_status": customer_status,
                "recovery_stage": recovery_stage,
                "note": "Inactive customer detected by RevivaIQ recovery analytics.",
            }

            if existing:
                existing.write(vals)
            else:
                Insight.create(vals)
                created_count += 1

        return created_count

    def _get_customer_status(self, days_inactive, inactivity_days):
        if days_inactive >= inactivity_days * 2:
            return "lost"

        if days_inactive >= inactivity_days:
            return "inactive"

        return "at_risk"
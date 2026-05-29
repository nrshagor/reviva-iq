from odoo import fields


class CustomerRecoveryService:
    def __init__(self, env):
        self.env = env

    def run_customer_recovery_analysis(self, dashboard):
        company = self.env.company
        inactivity_days = dashboard.customer_inactivity_days_threshold
        batch_limit = dashboard.customer_batch_limit

        cutoff_date = fields.Date.subtract(fields.Date.today(), days=inactivity_days)

        partners = self.env["res.partner"].search(
            [
                ("company_id", "in", [False, company.id]),
                ("customer_rank", ">", 0),
                ("active", "=", True),
            ],
            limit=batch_limit,
        )

        Insight = self.env["revivaiq.customer.insight"]

        created_count = 0

        for partner in partners:
            last_order = self.env["sale.order"].search(
                [
                    ("partner_id", "=", partner.id),
                    ("company_id", "=", company.id),
                    ("state", "in", ["sale", "done"]),
                ],
                order="date_order desc",
                limit=1,
            )

            if not last_order:
                continue

            last_order_date = last_order.date_order.date()

            if last_order_date > cutoff_date:
                continue

            existing = Insight.search(
                [
                    ("partner_id", "=", partner.id),
                    ("company_id", "=", company.id),
                ],
                limit=1,
            )

            days_inactive = (fields.Date.today() - last_order_date).days
            recovery_score = min(100, int(days_inactive / inactivity_days * 50))

            vals = {
                "partner_id": partner.id,
                "company_id": company.id,
                "total_order_count": 1,
                "total_revenue": last_order.amount_total,
                "last_order_date": last_order_date,
                "days_inactive": days_inactive,
                "recovery_score": recovery_score,
                "customer_status": "inactive",
                "recovery_stage": "review",
                "note": "Inactive customer detected by manual recovery analysis.",
            }
            
            if existing:
                existing.write(vals)
            else:
                Insight.create(vals)
                created_count += 1

        return created_count
from odoo import fields


class CustomerRecoveryService:
    SAFE_REGENERATION_STAGES = ["new", "review"]
    PROTECTED_OPERATIONAL_STAGES = ["contacted", "recovered", "ignored"]

    def __init__(self, env):
        self.env = env

    def _cleanup_stale_generated_insights(self, company, limit):
        stale_records = self.env["revivaiq.customer.insight"].search(
            [
                ("company_id", "=", company.id),
                ("analysis_source", "=", "generated"),
                ("recovery_stage", "in", self.SAFE_REGENERATION_STAGES),
            ],
            limit=limit,
            order="id asc",
        )

        cleanup_count = len(stale_records)
        stale_records.unlink()
        return cleanup_count

    def run_customer_recovery_analysis(self, dashboard):
        company = self.env.company
        inactivity_days = dashboard.customer_inactivity_days_threshold or 90
        batch_limit = dashboard.customer_batch_limit or 500
        safe_limit = min(max(batch_limit, 50), 5000)

        now = fields.Datetime.now()
        today = fields.Date.today()
        cutoff_date = fields.Date.subtract(today, days=inactivity_days)

        cleanup_count = self._cleanup_stale_generated_insights(company, safe_limit)

        partners = self.env["res.partner"].search(
            [
                ("company_id", "in", [False, company.id]),
                ("customer_rank", ">", 0),
                ("active", "=", True),
            ],
            limit=safe_limit,
            order="id desc",
        )

        Insight = self.env["revivaiq.customer.insight"]
        created_count = 0
        skipped_protected_count = 0

        for partner in partners:
            protected_existing = Insight.search(
                [
                    ("partner_id", "=", partner.id),
                    ("company_id", "=", company.id),
                    ("recovery_stage", "in", self.PROTECTED_OPERATIONAL_STAGES),
                ],
                limit=1,
            )

            if protected_existing:
                skipped_protected_count += 1
                continue

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

            days_inactive = (today - last_order_date).days
            total_revenue = sum(orders.mapped("amount_total"))
            total_order_count = len(orders)

            recovery_score = min(100, int((days_inactive / inactivity_days) * 50))

            if total_revenue >= 5000:
                recovery_score = min(100, recovery_score + 30)
            elif total_revenue >= 1000:
                recovery_score = min(100, recovery_score + 15)

            customer_status = self._get_customer_status(days_inactive, inactivity_days)
            recovery_stage = "review" if recovery_score >= 70 else "new"

            Insight.create({
                "partner_id": partner.id,
                "company_id": company.id,
                "total_order_count": total_order_count,
                "total_revenue": total_revenue,
                "last_order_date": last_order_date,
                "days_inactive": days_inactive,
                "recovery_score": recovery_score,
                "customer_status": customer_status,
                "recovery_stage": recovery_stage,
                "analysis_source": "generated",
                "analysis_run_date": now,
                "note": "Inactive customer detected by RevivaIQ recovery analytics.",
            })

            created_count += 1

        return {
            "created_records": created_count,
            "updated_records": 0,
            "cleanup_count": cleanup_count,
            "skipped_protected_records": skipped_protected_count,
        }

    def _get_customer_status(self, days_inactive, inactivity_days):
        if days_inactive >= inactivity_days * 2:
            return "lost"

        if days_inactive >= inactivity_days:
            return "inactive"

        return "at_risk"
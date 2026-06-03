from odoo import fields, models


class RevivaIQAnalyticsSnapshotService(models.AbstractModel):
    _name = "revivaiq.analytics.snapshot.service"
    _description = "RevivaIQ Analytics Snapshot Service"

    def _cleanup_draft_snapshots(self, company, limit):
        draft_snapshots = self.env["revivaiq.analytics.snapshot"].search(
            [
                ("company_id", "=", company.id),
                ("state", "=", "draft"),
            ],
            limit=limit,
            order="id asc",
        )

        cleanup_count = len(draft_snapshots)
        draft_snapshots.unlink()
        return cleanup_count

    def generate_snapshot(self, snapshot_name="RevivaIQ Snapshot", record_limit=5000):
        company = self.env.company
        safe_limit = min(max(record_limit or 5000, 50), 10000)
        now = fields.Datetime.now()

        cleanup_count = self._cleanup_draft_snapshots(company, safe_limit)

        DeadStock = self.env["revivaiq.dead.stock"]
        CustomerInsight = self.env["revivaiq.customer.insight"]
        Snapshot = self.env["revivaiq.analytics.snapshot"]

        dead_stocks = DeadStock.search(
            [
                ("company_id", "=", company.id),
                ("state", "in", ["draft", "active", "reviewed"]),
            ],
            limit=safe_limit,
            order="risk_score desc, id desc",
        )

        customer_insights = CustomerInsight.search(
            [
                ("company_id", "=", company.id),
                ("recovery_stage", "in", ["new", "review", "contacted"]),
            ],
            limit=safe_limit,
            order="recovery_score desc, id desc",
        )

        dead_stock_count = len(dead_stocks)
        customer_recovery_count = len(customer_insights)

        high_risk_dead_stock_count = len(
            dead_stocks.filtered(lambda item: item.risk_level in ["high", "critical"])
        )

        high_score_customer_count = len(
            customer_insights.filtered(lambda customer: customer.recovery_score >= 80)
        )

        dead_stock_value = sum(dead_stocks.mapped("inventory_value"))
        recovery_opportunity_value = sum(customer_insights.mapped("total_revenue"))
        total_revenue_risk = dead_stock_value + recovery_opportunity_value

        snapshot = Snapshot.create({
            "name": snapshot_name or "RevivaIQ Snapshot",
            "company_id": company.id,
            "snapshot_date": now,
            "snapshot_type": "manual",
            "analysis_source": "generated",
            "analysis_run_date": now,
            "dead_stock_count": dead_stock_count,
            "dead_stock_value": dead_stock_value,
            "inactive_customer_count": customer_recovery_count,
            "customer_recovery_count": customer_recovery_count,
            "high_risk_dead_stock_count": high_risk_dead_stock_count,
            "high_score_customer_count": high_score_customer_count,
            "recovery_opportunity_value": recovery_opportunity_value,
            "total_revenue_risk": total_revenue_risk,
            "state": "confirmed",
            "confirmed_by": self.env.user.id,
            "confirmed_date": now,
            "note": "Manual analytics snapshot generated from current active recovery data.",
        })

        return {
            "snapshot_id": snapshot.id,
            "dead_stock_count": dead_stock_count,
            "dead_stock_value": dead_stock_value,
            "customer_recovery_count": customer_recovery_count,
            "high_risk_dead_stock_count": high_risk_dead_stock_count,
            "high_score_customer_count": high_score_customer_count,
            "recovery_opportunity_value": recovery_opportunity_value,
            "total_revenue_risk": total_revenue_risk,
            "cleanup_count": cleanup_count,
        }
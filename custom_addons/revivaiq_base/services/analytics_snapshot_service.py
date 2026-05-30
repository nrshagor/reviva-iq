from odoo import fields, models


class RevivaIQAnalyticsSnapshotService(models.AbstractModel):
    _name = "revivaiq.analytics.snapshot.service"
    _description = "RevivaIQ Analytics Snapshot Service"

    def generate_snapshot(self, snapshot_name="RevivaIQ Snapshot", record_limit=5000):
        company = self.env.company

        safe_limit = min(max(record_limit or 5000, 50), 10000)

        DeadStock = self.env["revivaiq.dead.stock"]
        CustomerInsight = self.env["revivaiq.customer.insight"]
        Snapshot = self.env["revivaiq.analytics.snapshot"]

        dead_stocks = DeadStock.search(
            [("company_id", "=", company.id)],
            limit=safe_limit,
        )

        customer_insights = CustomerInsight.search(
            [("company_id", "=", company.id)],
            limit=safe_limit,
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
            "snapshot_date": fields.Datetime.now(),
            "snapshot_type": "manual",
            "dead_stock_count": dead_stock_count,
            "dead_stock_value": dead_stock_value,
            "inactive_customer_count": customer_recovery_count,
            "customer_recovery_count": customer_recovery_count,
            "high_risk_dead_stock_count": high_risk_dead_stock_count,
            "high_score_customer_count": high_score_customer_count,
            "recovery_opportunity_value": recovery_opportunity_value,
            "total_revenue_risk": total_revenue_risk,
            "state": "confirmed",
            "note": "Manual analytics snapshot generated from current recovery data.",
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
        }
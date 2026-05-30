from odoo import api, fields, models
from odoo.exceptions import ValidationError


class RevivaIQDashboard(models.Model):
    _name = "revivaiq.dashboard"
    _description = "RevivaIQ Dashboard"

    name = fields.Char(default="RevivaIQ Overview", required=True)

    dead_stock_days_threshold = fields.Integer(
        string="Dead Stock Threshold (Days)",
        default=60,
        required=True,
    )
    dead_stock_max_batch_limit = fields.Integer(
        string="Maximum Product Batch Limit",
        default=500,
        required=True,
    )
    dead_stock_min_quantity = fields.Float(
        string="Minimum Stock Quantity",
        default=1.0,
    )

    customer_inactivity_days_threshold = fields.Integer(
        string="Customer Inactivity Threshold (Days)",
        default=90,
        required=True,
    )
    customer_batch_limit = fields.Integer(
        string="Maximum Customer Batch Limit",
        default=500,
        required=True,
    )

    last_dead_stock_run = fields.Datetime(readonly=True)
    last_dead_stock_created_count = fields.Integer(readonly=True)

    last_customer_recovery_run = fields.Datetime(readonly=True)
    last_customer_recovery_created_count = fields.Integer(readonly=True)

    last_snapshot_run = fields.Datetime(readonly=True)
    last_snapshot_dead_stock_count = fields.Integer(readonly=True)
    last_snapshot_customer_recovery_count = fields.Integer(readonly=True)

    dead_stock_count = fields.Integer(compute="_compute_dashboard_summary")
    dead_stock_total_quantity = fields.Float(compute="_compute_dashboard_summary")
    dead_stock_total_sold_quantity = fields.Float(compute="_compute_dashboard_summary")
    dead_stock_total_risk_value = fields.Monetary(compute="_compute_dashboard_summary")

    inactive_customer_count = fields.Integer(compute="_compute_dashboard_summary")
    high_score_customer_count = fields.Integer(compute="_compute_dashboard_summary")
    customer_recovery_value = fields.Monetary(compute="_compute_dashboard_summary")

    latest_snapshot_count = fields.Integer(compute="_compute_dashboard_summary")
    latest_total_revenue_risk = fields.Monetary(compute="_compute_dashboard_summary")

    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
        required=True,
        readonly=True,
    )

    currency_id = fields.Many2one(
        "res.currency",
        related="company_id.currency_id",
        readonly=True,
    )

    @api.depends()
    def _compute_dashboard_summary(self):
        for record in self:
            company = self.env.company

            dead_stocks = self.env["revivaiq.dead.stock"].search(
                [("company_id", "=", company.id)],
                limit=5000,
            )

            customers = self.env["revivaiq.customer.insight"].search(
                [("company_id", "=", company.id)],
                limit=5000,
            )

            latest_snapshots = self.env["revivaiq.analytics.snapshot"].search(
                [("company_id", "=", company.id)],
                order="snapshot_date desc",
                limit=1,
            )

            record.dead_stock_count = len(dead_stocks)
            record.dead_stock_total_quantity = sum(dead_stocks.mapped("quantity_on_hand"))
            record.dead_stock_total_sold_quantity = sum(dead_stocks.mapped("quantity_sold"))
            record.dead_stock_total_risk_value = sum(dead_stocks.mapped("inventory_value"))

            record.inactive_customer_count = len(customers)
            record.high_score_customer_count = len(
                customers.filtered(lambda c: c.recovery_score >= 80)
            )
            record.customer_recovery_value = sum(customers.mapped("total_revenue"))

            record.latest_snapshot_count = len(latest_snapshots)
            record.latest_total_revenue_risk = sum(
                latest_snapshots.mapped("total_revenue_risk")
            )

    @api.constrains("dead_stock_days_threshold")
    def _validate_dead_stock_threshold(self):
        for record in self:
            if not 7 <= record.dead_stock_days_threshold <= 365:
                raise ValidationError("Dead Stock Threshold must be between 7 and 365 days.")

    @api.constrains("dead_stock_max_batch_limit")
    def _validate_dead_stock_batch_limit(self):
        for record in self:
            if not 50 <= record.dead_stock_max_batch_limit <= 5000:
                raise ValidationError(
                    "Maximum Product Batch Limit must be between 50 and 5000."
                )

    @api.constrains("dead_stock_min_quantity")
    def _validate_minimum_quantity(self):
        for record in self:
            if not 0 <= record.dead_stock_min_quantity <= 100000:
                raise ValidationError("Minimum Stock Quantity must be between 0 and 100000.")

    @api.constrains("customer_inactivity_days_threshold")
    def _validate_customer_inactivity_threshold(self):
        for record in self:
            if not 30 <= record.customer_inactivity_days_threshold <= 730:
                raise ValidationError(
                    "Customer Inactivity Threshold must be between 30 and 730 days."
                )

    @api.constrains("customer_batch_limit")
    def _validate_customer_batch_limit(self):
        for record in self:
            if not 50 <= record.customer_batch_limit <= 5000:
                raise ValidationError(
                    "Maximum Customer Batch Limit must be between 50 and 5000."
                )

    def action_run_dead_stock_analysis(self):
        self.ensure_one()

        result = self.env["revivaiq.dead.stock.service"].generate_dead_stock_analysis()
        created_records = result.get("created_records", 0)

        self.write({
            "last_dead_stock_run": fields.Datetime.now(),
            "last_dead_stock_created_count": created_records,
        })

        return self._show_notification(
            "Dead Stock Analysis Complete",
            f"Created {created_records} dead stock record(s).",
        )

    def action_run_customer_recovery_analysis(self):
        self.ensure_one()

        from ..services.customer_recovery_service import CustomerRecoveryService

        created_records = CustomerRecoveryService(self.env).run_customer_recovery_analysis(self)

        self.write({
            "last_customer_recovery_run": fields.Datetime.now(),
            "last_customer_recovery_created_count": created_records,
        })

        return self.action_open_customer_insights()

    def action_generate_analytics_snapshot(self):
        self.ensure_one()

        result = self.env["revivaiq.analytics.snapshot.service"].generate_snapshot()

        self.write({
            "last_snapshot_run": fields.Datetime.now(),
            "last_snapshot_dead_stock_count": result.get("dead_stock_count", 0),
            "last_snapshot_customer_recovery_count": result.get(
                "customer_recovery_count",
                0,
            ),
        })

        return self._show_notification(
            "Analytics Snapshot Created",
            (
                f"Snapshot created with {result.get('dead_stock_count', 0)} dead stock item(s) "
                f"and {result.get('customer_recovery_count', 0)} customer recovery opportunity record(s)."
            ),
        )

    def action_open_dead_stock(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Dead Stock",
            "res_model": "revivaiq.dead.stock",
            "view_mode": "list,form",
            "target": "current",
        }

    def action_open_customer_insights(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Customer Insights",
            "res_model": "revivaiq.customer.insight",
            "view_mode": "list,form",
            "target": "current",
        }

    def action_open_analytics_snapshots(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Analytics Snapshots",
            "res_model": "revivaiq.analytics.snapshot",
            "view_mode": "list,form",
            "target": "current",
        }

    def action_open_dead_stock_analysis_wizard(self):
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": "Run Dead Stock Analysis",
            "res_model": "revivaiq.dead.stock.analysis.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_dead_stock_days_threshold": self.dead_stock_days_threshold,
                "default_dead_stock_min_quantity": self.dead_stock_min_quantity,
                "default_dead_stock_max_batch_limit": self.dead_stock_max_batch_limit,
            },
        }

    def action_open_customer_recovery_wizard(self):
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": "Run Customer Recovery Analysis",
            "res_model": "revivaiq.customer.recovery.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_customer_inactivity_days_threshold": self.customer_inactivity_days_threshold,
                "default_customer_batch_limit": self.customer_batch_limit,
            },
        }

    def action_open_snapshot_generation_wizard(self):
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": "Generate Analytics Snapshot",
            "res_model": "revivaiq.snapshot.generation.wizard",
            "view_mode": "form",
            "target": "new",
        }

    def _show_notification(self, title, message, notification_type="success"):
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": title,
                "message": message,
                "type": notification_type,
                "sticky": False,
            },
        }
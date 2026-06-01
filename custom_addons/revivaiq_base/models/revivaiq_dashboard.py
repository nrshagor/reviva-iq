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
    dead_stock_summary_text = fields.Text(compute="_compute_dashboard_summary")

    inactive_customer_count = fields.Integer(compute="_compute_dashboard_summary")
    high_score_customer_count = fields.Integer(compute="_compute_dashboard_summary")
    customer_recovery_value = fields.Monetary(compute="_compute_dashboard_summary")
    customer_recovery_summary_text = fields.Text(compute="_compute_dashboard_summary")

    latest_snapshot_count = fields.Integer(compute="_compute_dashboard_summary")
    latest_total_revenue_risk = fields.Monetary(compute="_compute_dashboard_summary")
    snapshot_summary_text = fields.Text(compute="_compute_dashboard_summary")

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
            company = record.company_id or self.env.company

            dead_stocks = self.env["revivaiq.dead.stock"].search(
                [
                    ("company_id", "=", company.id),
                    ("state", "in", ["draft", "active", "reviewed"]),
                ],
                limit=5000,
                order="risk_score desc, id desc",
            )

            customers = self.env["revivaiq.customer.insight"].search(
                [
                    ("company_id", "=", company.id),
                    ("recovery_stage", "in", ["new", "review", "contacted"]),
                ],
                limit=5000,
                order="recovery_score desc, id desc",
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
                customers.filtered(lambda customer: customer.recovery_score >= 80)
            )
            record.customer_recovery_value = sum(customers.mapped("total_revenue"))

            record.latest_snapshot_count = len(latest_snapshots)
            record.latest_total_revenue_risk = sum(
                latest_snapshots.mapped("total_revenue_risk")
            )

            record.dead_stock_summary_text = record._get_dead_stock_summary_text()
            record.customer_recovery_summary_text = record._get_customer_recovery_summary_text()
            record.snapshot_summary_text = record._get_snapshot_summary_text()

    def _format_currency_amount(self, amount):
        self.ensure_one()
        currency = self.currency_id or self.env.company.currency_id
        return f"{amount:,.2f} {currency.symbol or currency.name or ''}".strip()

    def _get_dead_stock_summary_text(self):
        self.ensure_one()

        if not self.dead_stock_count:
            return (
                "No active dead stock risk found for the current threshold. "
                "Your inventory recovery position looks healthy."
            )

        return (
            f"{self.dead_stock_days_threshold} days threshold found "
            f"{self.dead_stock_count} active dead stock item(s). "
            f"{self.dead_stock_total_quantity:.2f} unit(s) are currently tied up, "
            f"with an estimated inventory risk value of "
            f"{self._format_currency_amount(self.dead_stock_total_risk_value)}."
        )

    def _get_customer_recovery_summary_text(self):
        self.ensure_one()

        if not self.inactive_customer_count:
            return (
                "No active inactive-customer recovery opportunity found for the current threshold. "
                "Customer recovery risk looks stable."
            )

        return (
            f"{self.customer_inactivity_days_threshold} days inactivity threshold found "
            f"{self.inactive_customer_count} active customer recovery opportunity record(s). "
            f"{self.high_score_customer_count} customer(s) have strong recovery potential, "
            f"with an estimated opportunity value of "
            f"{self._format_currency_amount(self.customer_recovery_value)}."
        )

    def _get_snapshot_summary_text(self):
        self.ensure_one()

        if not self.latest_snapshot_count:
            return (
                "No analytics snapshot has been generated yet. "
                "Generate a snapshot to capture the current revenue recovery position."
            )

        return (
            f"Latest snapshot shows total revenue risk of "
            f"{self._format_currency_amount(self.latest_total_revenue_risk)}. "
            f"It includes {self.last_snapshot_dead_stock_count} dead stock item(s) "
            f"and {self.last_snapshot_customer_recovery_count} customer recovery opportunity record(s)."
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
                raise ValidationError("Maximum Product Batch Limit must be between 50 and 5000.")

    @api.constrains("dead_stock_min_quantity")
    def _validate_minimum_quantity(self):
        for record in self:
            if not 0 <= record.dead_stock_min_quantity <= 100000:
                raise ValidationError("Minimum Stock Quantity must be between 0 and 100000.")

    @api.constrains("customer_inactivity_days_threshold")
    def _validate_customer_inactivity_threshold(self):
        for record in self:
            if not 30 <= record.customer_inactivity_days_threshold <= 730:
                raise ValidationError("Customer Inactivity Threshold must be between 30 and 730 days.")

    @api.constrains("customer_batch_limit")
    def _validate_customer_batch_limit(self):
        for record in self:
            if not 50 <= record.customer_batch_limit <= 5000:
                raise ValidationError("Maximum Customer Batch Limit must be between 50 and 5000.")

    def action_run_dead_stock_analysis(self):
        self.ensure_one()

        result = self.env["revivaiq.dead.stock.service"].generate_dead_stock_analysis()
        created_records = result.get("created_records", 0)
        updated_records = result.get("updated_records", 0)
        cleanup_count = result.get("cleanup_count", 0)
        skipped_protected_records = result.get("skipped_protected_records", 0)

        self.write({
            "last_dead_stock_run": fields.Datetime.now(),
            "last_dead_stock_created_count": created_records,
        })

        return self._show_notification(
            "Dead Stock Analysis Complete",
            (
                f"Created {created_records} fresh dead stock record(s). "
                f"Cleaned {cleanup_count} old generated draft/active record(s). "
                f"Preserved {skipped_protected_records} reviewed/resolved record(s). "
                f"Updated {updated_records} existing record(s)."
            ),
        )

    def action_run_customer_recovery_analysis(self):
        self.ensure_one()

        from ..services.customer_recovery_service import CustomerRecoveryService

        result = CustomerRecoveryService(self.env).run_customer_recovery_analysis(self)

        if isinstance(result, dict):
            created_records = result.get("created_records", 0)
            cleanup_count = result.get("cleanup_count", 0)
            skipped_protected_records = result.get("skipped_protected_records", 0)
        else:
            created_records = result or 0
            cleanup_count = 0
            skipped_protected_records = 0

        self.write({
            "last_customer_recovery_run": fields.Datetime.now(),
            "last_customer_recovery_created_count": created_records,
        })

        return self._show_notification(
            "Customer Recovery Analysis Complete",
            (
                f"Created {created_records} fresh recovery opportunity record(s). "
                f"Cleaned {cleanup_count} old generated new/review record(s). "
                f"Preserved {skipped_protected_records} contacted/recovered/ignored record(s)."
            ),
        )

    def action_generate_analytics_snapshot(self):
        self.ensure_one()

        result = self.env["revivaiq.analytics.snapshot.service"].generate_snapshot()
        cleanup_count = result.get("cleanup_count", 0)

        self.write({
            "last_snapshot_run": fields.Datetime.now(),
            "last_snapshot_dead_stock_count": result.get("dead_stock_count", 0),
            "last_snapshot_customer_recovery_count": result.get("customer_recovery_count", 0),
        })

        return self._show_notification(
            "Analytics Snapshot Created",
            (
                f"Snapshot created with {result.get('dead_stock_count', 0)} active dead stock item(s) "
                f"and {result.get('customer_recovery_count', 0)} active customer recovery opportunity record(s). "
                f"Cleaned {cleanup_count} old draft snapshot(s)."
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
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

    last_dead_stock_run = fields.Datetime(
        string="Last Dead Stock Analysis Run",
        readonly=True,
    )

    last_dead_stock_created_count = fields.Integer(
        string="Last Created Dead Stock Records",
        readonly=True,
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

    @api.constrains("dead_stock_days_threshold")
    def _validate_dead_stock_threshold(self):
        for record in self:
            if record.dead_stock_days_threshold < 7:
                raise ValidationError("Dead stock threshold must be at least 7 days.")
            if record.dead_stock_days_threshold > 365:
                raise ValidationError("Dead stock threshold cannot exceed 365 days.")

    @api.constrains("dead_stock_max_batch_limit")
    def _validate_batch_limit(self):
        for record in self:
            if record.dead_stock_max_batch_limit < 50:
                raise ValidationError("Batch limit must be at least 50.")
            if record.dead_stock_max_batch_limit > 5000:
                raise ValidationError("Batch limit cannot exceed 5000.")

    @api.constrains("dead_stock_min_quantity")
    def _validate_minimum_quantity(self):
        for record in self:
            if record.dead_stock_min_quantity < 0:
                raise ValidationError("Minimum stock quantity cannot be negative.")
            if record.dead_stock_min_quantity > 100000:
                raise ValidationError("Minimum stock quantity is too large.")

    @api.constrains("customer_inactivity_days_threshold", "customer_batch_limit")
    def _check_customer_recovery_settings(self):
        for record in self:
            if record.customer_inactivity_days_threshold < 30:
                raise ValidationError("Customer Inactivity Threshold must be at least 30 days.")
            if record.customer_inactivity_days_threshold > 730:
                raise ValidationError("Customer Inactivity Threshold cannot exceed 730 days.")
            if record.customer_batch_limit < 50:
                raise ValidationError("Customer Batch Limit must be at least 50.")
            if record.customer_batch_limit > 5000:
                raise ValidationError("Customer Batch Limit cannot exceed 5000.")

    def action_run_dead_stock_analysis(self):
        self.ensure_one()

        result = self.env["revivaiq.dead.stock.service"].generate_dead_stock_analysis()

        self.write(
            {
                "last_dead_stock_run": fields.Datetime.now(),
                "last_dead_stock_created_count": result.get("created_records", 0),
            }
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Dead Stock Analysis Complete",
                "message": f"Created {result.get('created_records', 0)} dead stock record(s).",
                "type": "success",
                "sticky": False,
            },
        }

    def action_run_customer_recovery_analysis(self):
        self.ensure_one()

        from ..services.customer_recovery_service import CustomerRecoveryService

        CustomerRecoveryService(self.env).run_customer_recovery_analysis(self)

        return {
            "type": "ir.actions.act_window",
            "name": "Customer Recovery Opportunities",
            "res_model": "revivaiq.customer.insight",
            "view_mode": "list,form",
            "target": "current",
        }
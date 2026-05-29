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
        help="Products with no confirmed sale after this number of days will be considered dead stock candidates.",
    )

    dead_stock_max_batch_limit = fields.Integer(
        string="Maximum Product Batch Limit",
        default=500,
        required=True,
        help="Maximum number of products processed in one analytics run.",
    )

    dead_stock_min_quantity = fields.Float(
        string="Minimum Stock Quantity",
        default=1.0,
        help="Only products with stock quantity above this value will be checked for dead stock analysis.",
    )

    last_dead_stock_run = fields.Datetime(
        string="Last Dead Stock Analysis Run",
        readonly=True,
    )

    last_dead_stock_created_count = fields.Integer(
        string="Last Created Dead Stock Records",
        readonly=True,
    )

    @api.constrains("dead_stock_days_threshold")
    def _validate_dead_stock_threshold(self):
        for record in self:
            if record.dead_stock_days_threshold < 7:
                raise ValidationError(
                    "Dead stock threshold must be at least 7 days."
                )

            if record.dead_stock_days_threshold > 365:
                raise ValidationError(
                    "Dead stock threshold cannot exceed 365 days."
                )

    @api.constrains("dead_stock_max_batch_limit")
    def _validate_batch_limit(self):
        for record in self:
            if record.dead_stock_max_batch_limit < 50:
                raise ValidationError(
                    "Batch limit must be at least 50."
                )

            if record.dead_stock_max_batch_limit > 5000:
                raise ValidationError(
                    "Batch limit cannot exceed 5000."
                )
    
    @api.constrains("dead_stock_min_quantity")
    def _validate_minimum_quantity(self):
        for record in self:
            if record.dead_stock_min_quantity < 0:
                raise ValidationError(
                    "Minimum stock quantity cannot be negative."
                )

            if record.dead_stock_min_quantity > 100000:
                raise ValidationError(
                    "Minimum stock quantity is too large."
                )

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
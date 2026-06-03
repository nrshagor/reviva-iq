from odoo import fields, models
from odoo.exceptions import ValidationError


class RevivaIQDeadStockAnalysisWizard(models.TransientModel):
    _name = "revivaiq.dead.stock.analysis.wizard"
    _description = "RevivaIQ Dead Stock Analysis Wizard"

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
        required=True,
    )

    def action_run_dead_stock_analysis(self):
        self.ensure_one()

        if not 7 <= self.dead_stock_days_threshold <= 365:
            raise ValidationError("Dead Stock Threshold must be between 7 and 365 days.")

        if not 50 <= self.dead_stock_max_batch_limit <= 5000:
            raise ValidationError("Maximum Product Batch Limit must be between 50 and 5000.")

        if not 0 <= self.dead_stock_min_quantity <= 100000:
            raise ValidationError("Minimum Stock Quantity must be between 0 and 100000.")

        dashboard = self.env["revivaiq.dashboard"].search(
            [("company_id", "=", self.env.company.id)],
            limit=1,
        )

        if not dashboard:
            dashboard = self.env["revivaiq.dashboard"].create({
                "name": "RevivaIQ Overview",
                "company_id": self.env.company.id,
            })

        old_values = {
            "dead_stock_days_threshold": dashboard.dead_stock_days_threshold,
            "dead_stock_max_batch_limit": dashboard.dead_stock_max_batch_limit,
            "dead_stock_min_quantity": dashboard.dead_stock_min_quantity,
        }

        dashboard.write({
            "dead_stock_days_threshold": self.dead_stock_days_threshold,
            "dead_stock_max_batch_limit": self.dead_stock_max_batch_limit,
            "dead_stock_min_quantity": self.dead_stock_min_quantity,
        })

        result = dashboard.action_run_dead_stock_analysis()

        dashboard.write(old_values)

        return dashboard.action_open_dead_stock()
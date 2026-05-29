from odoo import fields, models


class RevivaIQDeadStock(models.Model):
    _name = "revivaiq.dead.stock"
    _description = "RevivaIQ Dead Stock Intelligence"
    _order = "risk_score desc, id desc"

    product_id = fields.Many2one(
        "product.product",
        string="Product",
        required=True,
        index=True,
        ondelete="cascade",
    )

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )

    quantity_on_hand = fields.Float(string="Quantity On Hand", default=0.0)
    quantity_sold = fields.Float(string="Quantity Sold", default=0.0)

    last_sale_date = fields.Date(string="Last Sale Date")
    days_without_sale = fields.Integer(string="Days Without Sale", default=0)

    inventory_value = fields.Monetary(string="Inventory Value", default=0.0)
    currency_id = fields.Many2one(
        "res.currency",
        related="company_id.currency_id",
        readonly=True,
    )

    risk_level = fields.Selection(
        [
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
            ("critical", "Critical"),
        ],
        string="Risk Level",
        default="low",
        index=True,
    )

    risk_score = fields.Float(string="Risk Score", default=0.0, index=True)

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("reviewed", "Reviewed"),
            ("resolved", "Resolved"),
        ],
        string="Status",
        default="draft",
        index=True,
    )

    note = fields.Text(string="Internal Note")

    def action_open_dead_stock_settings(self):
        dashboard = self.env["revivaiq.dashboard"].search([], limit=1)

        return {
            "type": "ir.actions.act_window",
            "name": "Dead Stock Settings",
            "res_model": "revivaiq.dashboard",
            "res_id": dashboard.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_run_dead_stock_analysis(self):
        dashboard = self.env["revivaiq.dashboard"].search([], limit=1)
        return dashboard.action_run_dead_stock_analysis()
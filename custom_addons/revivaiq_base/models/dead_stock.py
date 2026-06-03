from odoo import fields, models


class RevivaIQDeadStock(models.Model):
    _name = "revivaiq.dead.stock"
    _description = "RevivaIQ Dead Stock Intelligence"
    _order = "risk_score desc, id desc"

    product_id = fields.Many2one("product.product", string="Product", required=True, index=True, ondelete="cascade")
    product_image_128 = fields.Image(
    string="Product Image",
    related="product_id.image_128",
    readonly=True,
    )
    company_id = fields.Many2one("res.company", string="Company", required=True, default=lambda self: self.env.company, index=True)

    quantity_on_hand = fields.Float(string="Quantity On Hand", default=0.0)
    quantity_sold = fields.Float(string="Quantity Sold", default=0.0)
    last_sale_date = fields.Date(string="Last Sale Date")
    days_without_sale = fields.Integer(string="Days Without Sale", default=0)
    inventory_value = fields.Monetary(string="Inventory Value", default=0.0)

    currency_id = fields.Many2one("res.currency", related="company_id.currency_id", readonly=True)

    analysis_source = fields.Selection(
        [("demo", "Demo Data"), ("manual", "Manual"), ("generated", "Generated")],
        string="Analysis Source",
        default="generated",
        required=True,
        index=True,
    )
    analysis_run_date = fields.Datetime(string="Analysis Run Date", default=fields.Datetime.now, readonly=True, index=True)

    risk_level = fields.Selection(
        [("low", "Low"), ("medium", "Medium"), ("high", "High"), ("critical", "Critical")],
        string="Risk Level",
        default="low",
        index=True,
    )
    risk_score = fields.Float(string="Risk Score", default=0.0, index=True)

    state = fields.Selection(
        [("draft", "Draft"), ("active", "Active"), ("reviewed", "Reviewed"), ("resolved", "Resolved")],
        string="Status",
        default="draft",
        index=True,
    )

    reviewed_by = fields.Many2one("res.users", string="Reviewed By", readonly=True)
    reviewed_date = fields.Datetime(string="Reviewed Date", readonly=True)
    resolved_by = fields.Many2one("res.users", string="Resolved By", readonly=True)
    resolved_date = fields.Datetime(string="Resolved Date", readonly=True)

    note = fields.Text(string="Internal Note")

    def action_mark_active(self):
        self.write({"state": "active"})

    def action_mark_reviewed(self):
        self.write({
            "state": "reviewed",
            "reviewed_by": self.env.user.id,
            "reviewed_date": fields.Datetime.now(),
        })

    def action_mark_resolved(self):
        self.write({
            "state": "resolved",
            "resolved_by": self.env.user.id,
            "resolved_date": fields.Datetime.now(),
        })

    def action_reset_to_draft(self):
        self.write({"state": "draft"})

    def action_open_dead_stock_settings(self):
        dashboard = self.env["revivaiq.dashboard"].search([("company_id", "=", self.env.company.id)], limit=1)
        return {
            "type": "ir.actions.act_window",
            "name": "Dead Stock Settings",
            "res_model": "revivaiq.dashboard",
            "res_id": dashboard.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_run_dead_stock_analysis(self):
        dashboard = self.env["revivaiq.dashboard"].search([("company_id", "=", self.env.company.id)], limit=1)
        return dashboard.action_run_dead_stock_analysis()
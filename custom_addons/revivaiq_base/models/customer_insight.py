from odoo import fields, models


class RevivaIQCustomerInsight(models.Model):
    _name = "revivaiq.customer.insight"
    _description = "RevivaIQ Customer Recovery Insight"
    _order = "recovery_score desc, id desc"

    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
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

    total_order_count = fields.Integer(string="Total Orders", default=0)
    total_revenue = fields.Monetary(string="Total Revenue", default=0.0)

    last_order_date = fields.Date(string="Last Order Date")
    days_inactive = fields.Integer(string="Days Inactive", default=0)

    recovery_score = fields.Float(string="Recovery Score", default=0.0, index=True)

    customer_status = fields.Selection(
        [
            ("active", "Active"),
            ("at_risk", "At Risk"),
            ("inactive", "Inactive"),
            ("lost", "Lost"),
        ],
        string="Customer Status",
        default="active",
        index=True,
    )

    recovery_stage = fields.Selection(
        [
            ("new", "New"),
            ("review", "Needs Review"),
            ("contacted", "Contacted"),
            ("recovered", "Recovered"),
            ("ignored", "Ignored"),
        ],
        string="Recovery Stage",
        default="new",
        index=True,
    )

    currency_id = fields.Many2one(
        "res.currency",
        related="company_id.currency_id",
        readonly=True,
    )

    note = fields.Text(string="Internal Note")
from odoo import fields, models


class RevivaIQCustomerInsight(models.Model):
    _name = "revivaiq.customer.insight"
    _description = "RevivaIQ Customer Recovery Insight"
    _order = "recovery_score desc, days_inactive desc"

    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        required=True,
        index=True,
    )

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )

    total_order_count = fields.Integer(string="Total Orders")
    total_revenue = fields.Monetary(string="Total Revenue")
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        related="company_id.currency_id",
        store=True,
        readonly=True,
    )

    last_order_date = fields.Date(string="Last Order Date")
    days_inactive = fields.Integer(string="Days Inactive")
    recovery_score = fields.Integer(string="Recovery Score")

    customer_status = fields.Selection(
        [
            ("active", "Active"),
            ("inactive", "Inactive"),
            ("at_risk", "At Risk"),
            ("lost", "Lost"),
        ],
        string="Customer Status",
        default="inactive",
        required=True,
    )

    recovery_stage = fields.Selection(
        [
            ("new", "New"),
            ("review", "Review"),
            ("contacted", "Contacted"),
            ("recovered", "Recovered"),
            ("ignored", "Ignored"),
        ],
        string="Recovery Stage",
        default="new",
        required=True,
    )

    note = fields.Text(string="Note")

    _sql_constraints = [
        (
            "unique_customer_company_insight",
            "unique(partner_id, company_id)",
            "Customer insight already exists for this company.",
        )
    ]
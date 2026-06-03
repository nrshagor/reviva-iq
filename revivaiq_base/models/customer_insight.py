from odoo import fields, models


class RevivaIQCustomerInsight(models.Model):
    _name = "revivaiq.customer.insight"
    _description = "RevivaIQ Customer Recovery Insight"
    _order = "recovery_score desc, days_inactive desc"

    partner_id = fields.Many2one("res.partner", string="Customer", required=True, index=True)
    company_id = fields.Many2one("res.company", string="Company", required=True, default=lambda self: self.env.company, index=True)

    total_order_count = fields.Integer(string="Total Orders")
    total_revenue = fields.Monetary(string="Total Revenue")

    currency_id = fields.Many2one("res.currency", string="Currency", related="company_id.currency_id", store=True, readonly=True)

    last_order_date = fields.Date(string="Last Order Date")
    days_inactive = fields.Integer(string="Days Inactive")
    recovery_score = fields.Integer(string="Recovery Score")

    analysis_source = fields.Selection(
        [("demo", "Demo Data"), ("manual", "Manual"), ("generated", "Generated")],
        string="Analysis Source",
        default="generated",
        required=True,
        index=True,
    )
    analysis_run_date = fields.Datetime(string="Analysis Run Date", default=fields.Datetime.now, readonly=True, index=True)

    customer_status = fields.Selection(
        [("active", "Active"), ("inactive", "Inactive"), ("at_risk", "At Risk"), ("lost", "Lost")],
        string="Customer Status",
        default="inactive",
        required=True,
        index=True,
    )

    recovery_stage = fields.Selection(
        [("new", "New"), ("review", "Review"), ("contacted", "Contacted"), ("recovered", "Recovered"), ("ignored", "Ignored")],
        string="Recovery Stage",
        default="new",
        required=True,
        index=True,
    )

    contacted_by = fields.Many2one("res.users", string="Contacted By", readonly=True)
    contacted_date = fields.Datetime(string="Contacted Date", readonly=True)
    recovered_by = fields.Many2one("res.users", string="Recovered By", readonly=True)
    recovered_date = fields.Datetime(string="Recovered Date", readonly=True)
    ignored_by = fields.Many2one("res.users", string="Ignored By", readonly=True)
    ignored_date = fields.Datetime(string="Ignored Date", readonly=True)

    note = fields.Text(string="Note")

    _sql_constraints = [
        ("unique_customer_company_insight", "unique(partner_id, company_id)", "Customer insight already exists for this company.")
    ]

    def action_mark_review(self):
        self.write({"recovery_stage": "review"})

    def action_mark_contacted(self):
        self.write({
            "recovery_stage": "contacted",
            "contacted_by": self.env.user.id,
            "contacted_date": fields.Datetime.now(),
        })

    def action_mark_recovered(self):
        self.write({
            "recovery_stage": "recovered",
            "recovered_by": self.env.user.id,
            "recovered_date": fields.Datetime.now(),
        })

    def action_mark_ignored(self):
        self.write({
            "recovery_stage": "ignored",
            "ignored_by": self.env.user.id,
            "ignored_date": fields.Datetime.now(),
        })

    def action_reset_to_new(self):
        self.write({"recovery_stage": "new"})
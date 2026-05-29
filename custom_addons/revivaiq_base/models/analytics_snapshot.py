from odoo import fields, models


class RevivaIQAnalyticsSnapshot(models.Model):
    _name = "revivaiq.analytics.snapshot"
    _description = "RevivaIQ Analytics Snapshot"
    _order = "snapshot_date desc, id desc"

    name = fields.Char(string="Snapshot Name", required=True)

    snapshot_date = fields.Date(
        string="Snapshot Date",
        required=True,
        default=fields.Date.context_today,
        index=True,
    )

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )

    dead_stock_count = fields.Integer(string="Dead Stock Items", default=0)
    dead_stock_value = fields.Monetary(string="Dead Stock Value", default=0.0)

    inactive_customer_count = fields.Integer(string="Inactive Customers", default=0)
    recovery_opportunity_value = fields.Monetary(
        string="Recovery Opportunity Value",
        default=0.0,
    )

    total_revenue_risk = fields.Monetary(string="Total Revenue Risk", default=0.0)

    currency_id = fields.Many2one(
        "res.currency",
        related="company_id.currency_id",
        readonly=True,
    )

    snapshot_type = fields.Selection(
        [
            ("manual", "Manual"),
            ("scheduled", "Scheduled"),
            ("system", "System"),
        ],
        string="Snapshot Type",
        default="manual",
        index=True,
    )

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("archived", "Archived"),
        ],
        string="Status",
        default="draft",
        index=True,
    )

    note = fields.Text(string="Snapshot Note")
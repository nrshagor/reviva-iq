from odoo import fields, models


class RevivaIQAnalyticsSnapshot(models.Model):
    _name = "revivaiq.analytics.snapshot"
    _description = "RevivaIQ Analytics Snapshot"
    _order = "snapshot_date desc, id desc"

    name = fields.Char(
        string="Snapshot Name",
        required=True,
        default="RevivaIQ Snapshot",
    )

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )

    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        related="company_id.currency_id",
        store=True,
        readonly=True,
    )

    snapshot_date = fields.Datetime(
        string="Snapshot Date",
        default=fields.Datetime.now,
        required=True,
        index=True,
    )

    snapshot_type = fields.Selection(
        [
            ("manual", "Manual"),
            ("system", "System"),
        ],
        string="Snapshot Type",
        default="manual",
        required=True,
    )

    dead_stock_count = fields.Integer(
        string="Dead Stock Count",
        readonly=True,
    )

    dead_stock_value = fields.Monetary(
        string="Dead Stock Value",
        readonly=True,
    )

    inactive_customer_count = fields.Integer(
        string="Inactive Customers",
        readonly=True,
    )

    recovery_opportunity_value = fields.Monetary(
        string="Recovery Opportunity Value",
        readonly=True,
    )

    total_revenue_risk = fields.Monetary(
        string="Total Revenue Risk",
        readonly=True,
    )

    customer_recovery_count = fields.Integer(
        string="Customer Recovery Count",
        readonly=True,
    )

    high_risk_dead_stock_count = fields.Integer(
        string="High Risk Dead Stock",
        readonly=True,
    )

    high_score_customer_count = fields.Integer(
        string="High Score Customers",
        readonly=True,
    )

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
        ],
        string="Status",
        default="confirmed",
        required=True,
    )

    note = fields.Text(string="Note")
from odoo import models, fields


class RevivaIQDashboard(models.Model):
    _name = "revivaiq.dashboard"
    _description = "RevivaIQ Dashboard"

    name = fields.Char(default="RevivaIQ Overview", required=True)
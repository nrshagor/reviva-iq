from odoo import fields, models
from odoo.exceptions import ValidationError


class RevivaIQSnapshotGenerationWizard(models.TransientModel):
    _name = "revivaiq.snapshot.generation.wizard"
    _description = "RevivaIQ Snapshot Generation Wizard"

    name = fields.Char(
        string="Snapshot Name",
        default="RevivaIQ Snapshot",
        required=True,
    )

    record_limit = fields.Integer(
        string="Maximum Records to Summarize",
        default=5000,
        required=True,
    )

    def action_generate_snapshot(self):
        self.ensure_one()

        if not 50 <= self.record_limit <= 10000:
            raise ValidationError("Maximum Records to Summarize must be between 50 and 10000.")

        result = self.env["revivaiq.analytics.snapshot.service"].generate_snapshot(
            snapshot_name=self.name,
            record_limit=self.record_limit,
        )

        dashboard = self.env["revivaiq.dashboard"].search(
            [("company_id", "=", self.env.company.id)],
            limit=1,
        )

        if dashboard:
            dashboard.write({
                "last_snapshot_run": fields.Datetime.now(),
                "last_snapshot_dead_stock_count": result.get("dead_stock_count", 0),
                "last_snapshot_customer_recovery_count": result.get("customer_recovery_count", 0),
            })

        return {
            "type": "ir.actions.act_window",
            "name": "Analytics Snapshots",
            "res_model": "revivaiq.analytics.snapshot",
            "view_mode": "list,form",
            "target": "current",
        }
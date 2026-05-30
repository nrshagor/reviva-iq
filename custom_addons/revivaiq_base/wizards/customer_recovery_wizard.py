from odoo import fields, models
from odoo.exceptions import ValidationError


class RevivaIQCustomerRecoveryWizard(models.TransientModel):
    _name = "revivaiq.customer.recovery.wizard"
    _description = "RevivaIQ Customer Recovery Wizard"

    customer_inactivity_days_threshold = fields.Integer(
        string="Customer Inactivity Threshold (Days)",
        default=90,
        required=True,
    )

    customer_batch_limit = fields.Integer(
        string="Maximum Customer Batch Limit",
        default=500,
        required=True,
    )

    def action_run_customer_recovery_analysis(self):
        self.ensure_one()

        if not 30 <= self.customer_inactivity_days_threshold <= 730:
            raise ValidationError("Customer Inactivity Threshold must be between 30 and 730 days.")

        if not 50 <= self.customer_batch_limit <= 5000:
            raise ValidationError("Maximum Customer Batch Limit must be between 50 and 5000.")

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
            "customer_inactivity_days_threshold": dashboard.customer_inactivity_days_threshold,
            "customer_batch_limit": dashboard.customer_batch_limit,
        }

        dashboard.write({
            "customer_inactivity_days_threshold": self.customer_inactivity_days_threshold,
            "customer_batch_limit": self.customer_batch_limit,
        })

        result = dashboard.action_run_customer_recovery_analysis()

        dashboard.write(old_values)

        return result
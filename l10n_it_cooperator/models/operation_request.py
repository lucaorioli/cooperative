# Copyright 2026 Luca Orioli <lucaorioli@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class OperationRequest(models.Model):
    _inherit = "operation.request"

    def execute_operation(self):
        result = super().execute_operation()
        if self.operation_type in ("sell_back", "transfer"):
            membership = self.partner_id.get_cooperative_membership(self.company_id)
            if membership.old_member and not membership.l10n_it_termination_date:
                membership.write(
                    {
                        "l10n_it_termination_date": self.effective_date,
                        "l10n_it_termination_reason": (
                            "withdrawal"
                            if self.operation_type == "sell_back"
                            else "transfer"
                        ),
                    }
                )
        return result

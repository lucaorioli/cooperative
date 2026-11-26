# Copyright 2026 Luca Orioli <lucaorioli@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _l10n_it_edi_ready_for_xml_export(self):
        # a capital release request is not an invoice: not sent to the sdi
        if self.release_capital_request:
            return False
        return super()._l10n_it_edi_ready_for_xml_export()

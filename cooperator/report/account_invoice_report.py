from odoo import api, fields, models
from odoo.fields import Domain
from odoo.tools import SQL


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    release_capital_request = fields.Boolean(string="Release capital request")

    def _select(self) -> SQL:
        return SQL(
            "%s, move.release_capital_request AS release_capital_request",
            super()._select(),
        )

    @api.model
    def _search(self, domain, *args, **kwargs):
        # capital release requests should be excluded from reports. this is also used by
        # res.partner._invoice_total().
        domain = Domain(domain) & Domain("release_capital_request", "=", False)
        return super()._search(domain, *args, **kwargs)

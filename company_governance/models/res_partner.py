# Copyright 2026 Luca Orioli <lucaorioli@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    governance_member_ids = fields.One2many(
        comodel_name="governance.body.member",
        inverse_name="partner_id",
        string="Corporate Offices",
    )

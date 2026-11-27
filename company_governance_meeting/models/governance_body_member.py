# Copyright 2026 Luca Orioli <lucaorioli@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class GovernanceBodyMember(models.Model):
    _inherit = "governance.body.member"
    _check_company_auto = True

    appointment_resolution_id = fields.Many2one(
        comodel_name="governance.resolution",
        string="Appointing Resolution",
        check_company=True,
    )
    end_resolution_id = fields.Many2one(
        comodel_name="governance.resolution",
        string="Ending Resolution",
        check_company=True,
    )

# Copyright 2026 Luca Orioli <lucaorioli@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class GovernanceBodyType(models.Model):
    _name = "governance.body.type"
    _description = "Corporate Body Type"
    _order = "sequence, name"

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    role_ids = fields.Many2many(
        comodel_name="governance.role",
        string="Allowed Offices",
        help="Offices that the members of this kind of body can hold. "
        "Leave empty to allow any office.",
    )
    description = fields.Text(translate=True)

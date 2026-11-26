# Copyright 2026 Luca Orioli <lucaorioli@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

from .member_category import SHARE_CATEGORIES


class ProductTemplate(models.Model):
    _inherit = "product.template"

    l10n_it_share_category = fields.Selection(
        SHARE_CATEGORIES,
        string="Share Category",
        default="cooperator",
        help="Category of the share in the members register: shares of the "
        "cooperator members, of the supporting members (soci sovventori) or "
        "instruments of the financing members (soci finanziatori).",
    )

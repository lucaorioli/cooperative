# Copyright 2026 Luca Orioli <lucaorioli@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

# categories of the albo delle società cooperative
COOP_REGISTER_CATEGORIES = [
    ("production_work", "Production and work cooperatives"),
    ("agricultural_work", "Agricultural work cooperatives"),
    ("social", "Social cooperatives"),
    ("agricultural_contribution", "Agricultural products contribution cooperatives"),
    ("housing", "Housing cooperatives"),
    ("fishing", "Fishing cooperatives"),
    ("consumer", "Consumer cooperatives"),
    ("retailer", "Retailer cooperatives"),
    ("transport", "Transport cooperatives"),
    ("consortium", "Cooperative consortia"),
    ("agricultural_consortium", "Agricultural consortia"),
    ("credit", "Cooperative credit banks"),
    ("guarantee", "Guarantee and credit cooperatives"),
    ("other", "Other cooperatives"),
]


class ResCompany(models.Model):
    _inherit = "res.company"

    l10n_it_coop_register_number = fields.Char(
        string="Cooperative Register Number",
        help="Registration number in the Italian register of cooperative "
        "societies (Albo delle società cooperative).",
    )
    l10n_it_coop_register_section = fields.Selection(
        [
            ("prevailing", "Cooperatives with prevailing mutuality"),
            ("other", "Cooperatives other than with prevailing mutuality"),
        ],
        string="Cooperative Register Section",
    )
    l10n_it_coop_register_category = fields.Selection(
        COOP_REGISTER_CATEGORIES,
        string="Cooperative Register Category",
    )
    l10n_it_social_coop_type = fields.Selection(
        [
            ("a", "Type A (social, health and educational services)"),
            ("b", "Type B (work integration of disadvantaged people)"),
            ("ab", "Types A and B"),
        ],
        string="Social Cooperative Type",
        help="Type of social cooperative (law 381/1991). Volunteer members are "
        "allowed in social cooperatives only.",
    )

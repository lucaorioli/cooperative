# Copyright 2026 Luca Orioli <lucaorioli@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Company Governance",
    "summary": "Corporate bodies, their terms of office and office holders",
    "version": "18.0.1.0.0",
    "depends": ["mail"],
    "author": "Luca Orioli, Odoo Community Association (OCA)",
    "maintainers": ["lucaorioli"],
    "category": "Cooperative management",
    "website": "https://github.com/OCA/cooperative",
    "license": "AGPL-3",
    "data": [
        "security/governance_security.xml",
        "security/ir.model.access.csv",
        "data/governance_data.xml",
        "views/governance_role_views.xml",
        "views/governance_body_type_views.xml",
        "views/governance_body_member_views.xml",
        "views/governance_body_views.xml",
        "views/res_partner_views.xml",
        "views/menus.xml",
    ],
    "installable": True,
}

# Copyright 2026 Luca Orioli <lucaorioli@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Italy - Cooperators Website",
    "summary": "Fiscal code and IBAN in the subscription form of the website",
    "version": "19.0.1.0.0",
    "depends": [
        "cooperator_website",
        "l10n_it_cooperator",
    ],
    "author": "Luca Orioli, Odoo Community Association (OCA)",
    "maintainers": ["lucaorioli"],
    "category": "Cooperative management",
    "website": "https://github.com/OCA/cooperative",
    "license": "AGPL-3",
    "data": [
        "views/subscription_template.xml",
    ],
    "auto_install": True,
    "installable": True,
}

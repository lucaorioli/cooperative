# Copyright 2026 Luca Orioli <lucaorioli@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Italy - Cooperators",
    "summary": "Italian localization of the cooperator module",
    "version": "19.0.1.0.0",
    "depends": [
        "cooperator",
        "l10n_it_edi",
    ],
    "author": "Luca Orioli, Odoo Community Association (OCA)",
    "maintainers": ["lucaorioli"],
    "category": "Cooperative management",
    "website": "https://github.com/OCA/cooperative",
    "license": "AGPL-3",
    "data": [
        "views/res_config_settings_view.xml",
        "views/subscription_request_view.xml",
        "views/member_category_views.xml",
        "report/report_cooperator_certificate.xml",
        "report/report_cooperator_register.xml",
    ],
    "auto_install": True,
    "installable": True,
}

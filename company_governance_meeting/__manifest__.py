# Copyright 2026 Luca Orioli <lucaorioli@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Company Governance Meetings",
    "summary": "Meetings of the corporate bodies, resolutions and minutes",
    "version": "19.0.1.0.0",
    "depends": ["company_governance"],
    "author": "Luca Orioli, Odoo Community Association (OCA)",
    "maintainers": ["lucaorioli"],
    "category": "Cooperative management",
    "website": "https://github.com/OCA/cooperative",
    "license": "AGPL-3",
    "data": [
        "security/governance_meeting_security.xml",
        "security/ir.model.access.csv",
        "data/ir_sequence.xml",
        "views/governance_resolution_views.xml",
        "views/governance_meeting_views.xml",
        "views/governance_body_views.xml",
        "views/governance_body_member_views.xml",
        "views/menus.xml",
        "report/governance_meeting_report.xml",
    ],
    "installable": True,
}

# Copyright 2026 Luca Orioli <lucaorioli@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

from odoo.addons.cooperator.models.res_partner import cooperative_membership_field

from .member_category import MEMBER_TYPES, TERMINATION_REASONS

# also used by the subscription request
LEGAL_FORMS = [
    ("it_di", "Sole proprietorship (ditta individuale)"),
    ("it_snc", "General partnership (S.n.c.)"),
    ("it_sas", "Limited partnership (S.a.s.)"),
    ("it_srl", "Limited liability company (S.r.l.)"),
    ("it_srls", "Simplified limited liability company (S.r.l.s.)"),
    ("it_spa", "Joint-stock company (S.p.A.)"),
    ("it_sapa", "Partnership limited by shares (S.a.p.A.)"),
    ("it_coop", "Cooperative society (Soc. coop.)"),
    ("it_coop_soc", "Social cooperative (Coop. sociale)"),
    ("it_consortium", "Consortium"),
    ("it_association", "Association"),
    ("it_foundation", "Foundation"),
    ("it_public", "Public body"),
]
LEGAL_FORMS_ONDELETE = {key: "set null" for key, _label in LEGAL_FORMS}


class ResPartner(models.Model):
    _inherit = "res.partner"

    legal_form = fields.Selection(
        selection_add=LEGAL_FORMS, ondelete=LEGAL_FORMS_ONDELETE
    )
    l10n_it_member_type = cooperative_membership_field(
        "l10n_it_member_type",
        fields.Selection,
        string="Member Type",
        selection=MEMBER_TYPES,
    )
    l10n_it_special_category = cooperative_membership_field(
        "l10n_it_special_category", fields.Boolean, string="Special Category"
    )
    l10n_it_special_category_end = cooperative_membership_field(
        "l10n_it_special_category_end", fields.Date, string="Special Category Until"
    )
    l10n_it_admission_date = cooperative_membership_field(
        "l10n_it_admission_date", fields.Date, string="Admission Date", readonly=True
    )
    l10n_it_termination_date = cooperative_membership_field(
        "l10n_it_termination_date", fields.Date, string="Termination Date"
    )
    l10n_it_termination_reason = cooperative_membership_field(
        "l10n_it_termination_reason",
        fields.Selection,
        string="Termination Reason",
        selection=TERMINATION_REASONS,
    )
    l10n_it_encumbrances = cooperative_membership_field(
        "l10n_it_encumbrances", fields.Text, string="Encumbrances"
    )

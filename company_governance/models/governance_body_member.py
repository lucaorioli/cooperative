# Copyright 2026 Luca Orioli <lucaorioli@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.osv import expression


class GovernanceBodyMember(models.Model):
    _name = "governance.body.member"
    _description = "Corporate Body Member"
    _order = "date_start desc, sequence, id"
    _rec_names_search = ["partner_id", "role_id", "body_id"]

    body_id = fields.Many2one(
        comodel_name="governance.body",
        string="Body",
        required=True,
        ondelete="cascade",
        index=True,
    )
    type_id = fields.Many2one(related="body_id.type_id", store=True)
    company_id = fields.Many2one(related="body_id.company_id", store=True)
    sequence = fields.Integer(default=10)
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Holder",
        required=True,
        index=True,
    )
    role_id = fields.Many2one(
        comodel_name="governance.role",
        string="Office",
        required=True,
    )
    date_start = fields.Date(
        string="Appointed On",
        required=True,
        default=fields.Date.context_today,
    )
    date_end = fields.Date(string="Ended On")
    end_reason = fields.Selection(
        selection=[
            ("term_expired", "Term Expired"),
            ("body_ceased", "Body Ceased"),
            ("resignation", "Resignation"),
            ("revocation", "Revocation"),
            ("forfeiture", "Forfeiture"),
            ("death", "Death"),
            ("other", "Other"),
        ],
    )
    legal_representative = fields.Boolean()
    powers = fields.Text(string="Powers and Delegations")
    is_current = fields.Boolean(
        string="Current",
        compute="_compute_is_current",
        search="_search_is_current",
    )

    @api.depends("date_start", "date_end", "body_id.state")
    def _compute_is_current(self):
        today = fields.Date.context_today(self)
        for member in self:
            member.is_current = (
                member.body_id.state != "ceased"
                and member.date_start <= today
                and (not member.date_end or member.date_end >= today)
            )

    def _search_is_current(self, operator, value):
        if operator not in ("=", "!=") or not isinstance(value, bool):
            raise NotImplementedError(_("Unsupported search on Current."))
        today = fields.Date.context_today(self)
        domain = [
            ("body_id.state", "!=", "ceased"),
            ("date_start", "<=", today),
            "|",
            ("date_end", "=", False),
            ("date_end", ">=", today),
        ]
        if (operator == "=") != value:
            domain = ["!", *expression.normalize_domain(domain)]
        return domain

    @api.depends("partner_id", "role_id", "body_id")
    def _compute_display_name(self):
        for member in self:
            member.display_name = (
                f"{member.partner_id.name} - {member.role_id.name} "
                f"({member.body_id.name})"
            )

    @api.constrains("date_start", "date_end", "body_id")
    def _check_dates(self):
        for member in self:
            if member.date_end and member.date_end < member.date_start:
                raise ValidationError(
                    _("%s cannot end before being appointed.", member.display_name)
                )
            if member.date_start < member.body_id.date_start:
                raise ValidationError(
                    _(
                        "%s cannot be appointed before the body takes office.",
                        member.display_name,
                    )
                )

    @api.constrains("role_id", "body_id")
    def _check_role(self):
        for member in self:
            allowed = member.type_id.role_ids
            if allowed and member.role_id not in allowed:
                raise ValidationError(
                    _(
                        "The office %(role)s is not allowed in a %(type)s.",
                        role=member.role_id.name,
                        type=member.type_id.name,
                    )
                )

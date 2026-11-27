# Copyright 2026 Luca Orioli <lucaorioli@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class GovernanceResolution(models.Model):
    _name = "governance.resolution"
    _description = "Corporate Body Resolution"
    _inherit = ["mail.thread"]
    _order = "meeting_date desc, sequence, id"

    meeting_id = fields.Many2one(
        comodel_name="governance.meeting",
        string="Meeting",
        required=True,
        ondelete="cascade",
        index=True,
    )
    meeting_date = fields.Datetime(related="meeting_id.date", store=True)
    body_id = fields.Many2one(related="meeting_id.body_id", store=True)
    company_id = fields.Many2one(related="meeting_id.company_id", store=True)
    sequence = fields.Integer(default=10)
    number = fields.Char(readonly=True, copy=False, tracking=True)
    name = fields.Char(string="Subject", required=True, tracking=True)
    text = fields.Html()
    outcome = fields.Selection(
        selection=[
            ("approved", "Approved"),
            ("rejected", "Rejected"),
            ("postponed", "Postponed"),
        ],
        tracking=True,
    )
    votes_for = fields.Float(digits=(16, 2))
    votes_against = fields.Float(digits=(16, 2))
    votes_abstained = fields.Float(string="Abstentions", digits=(16, 2))
    appointment_ids = fields.One2many(
        comodel_name="governance.body.member",
        inverse_name="appointment_resolution_id",
        string="Appointments",
    )
    termination_ids = fields.One2many(
        comodel_name="governance.body.member",
        inverse_name="end_resolution_id",
        string="Terminations",
    )
    appointed_body_ids = fields.One2many(
        comodel_name="governance.body",
        inverse_name="appointment_resolution_id",
        string="Appointed Bodies",
    )

    @api.depends("number", "name")
    def _compute_display_name(self):
        for resolution in self:
            resolution.display_name = (
                f"{resolution.number} - {resolution.name}"
                if resolution.number
                else resolution.name
            )

    @api.constrains("votes_for", "votes_against", "votes_abstained")
    def _check_votes(self):
        for resolution in self:
            votes = (
                resolution.votes_for,
                resolution.votes_against,
                resolution.votes_abstained,
            )
            if min(votes) < 0:
                raise ValidationError(_("The votes cannot be negative."))
            present = resolution.meeting_id.present_votes
            if present and sum(votes) > present:
                raise ValidationError(
                    _(
                        "The votes of %(name)s exceed the votes present "
                        "or represented (%(present)s).",
                        name=resolution.name,
                        present=present,
                    )
                )

    def _get_number_sequence(self):
        """Numbering sequence of the company, created from the generic one."""
        self.ensure_one()
        sequence_model = self.env["ir.sequence"].sudo()
        sequence = sequence_model.search(
            [
                ("code", "=", "governance.resolution"),
                ("company_id", "=", self.company_id.id),
            ],
            limit=1,
        )
        if not sequence:
            sequence = (
                self.env.ref("company_governance_meeting.seq_governance_resolution")
                .sudo()
                .copy({"company_id": self.company_id.id})
            )
        return sequence

    def _assign_number(self):
        for resolution in self.sorted(lambda r: (r.meeting_date, r.sequence, r.id)):
            resolution.number = resolution._get_number_sequence().next_by_id(
                sequence_date=resolution.meeting_date.date()
            )

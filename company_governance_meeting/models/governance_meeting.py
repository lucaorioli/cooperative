# Copyright 2026 Luca Orioli <lucaorioli@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import formatLang


class GovernanceMeeting(models.Model):
    _name = "governance.meeting"
    _description = "Corporate Body Meeting"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date desc, id desc"

    name = fields.Char(required=True, tracking=True)
    body_id = fields.Many2one(
        comodel_name="governance.body",
        string="Body",
        required=True,
        index=True,
        tracking=True,
    )
    company_id = fields.Many2one(related="body_id.company_id", store=True)
    meeting_type = fields.Selection(
        selection=[("ordinary", "Ordinary"), ("extraordinary", "Extraordinary")],
        string="Type",
        required=True,
        default="ordinary",
    )
    convocation_date = fields.Date(tracking=True)
    convocation_method = fields.Char(
        help="How the meeting was called, e.g. registered letter, email, "
        "notice in the official journal.",
    )
    date = fields.Datetime(required=True, tracking=True)
    location = fields.Char()
    agenda = fields.Html()
    chair_id = fields.Many2one(comodel_name="res.partner", string="Chair")
    secretary_id = fields.Many2one(comodel_name="res.partner", string="Secretary")
    attendee_ids = fields.One2many(
        comodel_name="governance.meeting.attendee",
        inverse_name="meeting_id",
        string="Attendees",
    )
    attendee_count = fields.Integer(compute="_compute_attendance")
    present_count = fields.Integer(
        string="Present or Represented", compute="_compute_attendance"
    )
    present_votes = fields.Float(
        string="Votes Present or Represented",
        compute="_compute_attendance",
        digits=(16, 2),
    )
    total_votes = fields.Float(compute="_compute_attendance", digits=(16, 2))
    resolution_ids = fields.One2many(
        comodel_name="governance.resolution",
        inverse_name="meeting_id",
        string="Resolutions",
    )
    minutes = fields.Html()
    signed_minutes = fields.Binary(attachment=True, copy=False)
    signed_minutes_filename = fields.Char()
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("convened", "Convened"),
            ("held", "Held"),
            ("minuted", "Minuted"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
        required=True,
        tracking=True,
    )

    @api.depends("attendee_ids.attendance", "attendee_ids.votes")
    def _compute_attendance(self):
        for meeting in self:
            attendees = meeting.attendee_ids
            present = attendees.filtered(lambda a: a.attendance != "absent")
            meeting.attendee_count = len(attendees)
            meeting.present_count = len(present)
            meeting.present_votes = sum(present.mapped("votes"))
            meeting.total_votes = sum(attendees.mapped("votes"))

    @api.constrains("convocation_date", "date")
    def _check_convocation_date(self):
        for meeting in self:
            if (
                meeting.convocation_date
                and meeting.convocation_date > meeting.date.date()
            ):
                raise ValidationError(
                    self.env._("%s cannot be convened after its date.", meeting.name)
                )

    def _format_votes(self, votes):
        """Votes without decimals when they are whole numbers."""
        digits = 0 if float(votes).is_integer() else 2
        return formatLang(self.env, votes, digits=digits)

    def action_load_members(self):
        """Add the current members of the body to the attendees."""
        for meeting in self:
            known = meeting.attendee_ids.partner_id
            members = meeting.body_id.current_member_ids.filtered(
                lambda m, known=known: m.partner_id not in known
            )
            meeting.attendee_ids = [
                fields.Command.create({"partner_id": p.id}) for p in members.partner_id
            ]

    def action_convene(self):
        today = fields.Date.context_today(self)
        for meeting in self:
            if not meeting.convocation_date and today <= meeting.date.date():
                meeting.convocation_date = today
        self.write({"state": "convened"})

    def action_hold(self):
        self.resolution_ids.filtered(lambda r: not r.number)._assign_number()
        self.write({"state": "held"})

    def action_minute(self):
        for meeting in self:
            if not meeting.minutes and not meeting.signed_minutes:
                raise UserError(
                    self.env._("Write or attach the minutes of %s first.", meeting.name)
                )
        self.write({"state": "minuted"})

    def action_cancel(self):
        self.write({"state": "cancelled"})

    def action_draft(self):
        self.write({"state": "draft"})

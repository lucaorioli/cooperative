# Copyright 2026 Luca Orioli <lucaorioli@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class GovernanceMeetingAttendee(models.Model):
    _name = "governance.meeting.attendee"
    _description = "Corporate Body Meeting Attendee"
    _order = "meeting_id, id"

    meeting_id = fields.Many2one(
        comodel_name="governance.meeting",
        required=True,
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(related="meeting_id.company_id", store=True)
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Entitled Person",
        required=True,
    )
    attendance = fields.Selection(
        selection=[
            ("present", "Present"),
            ("proxy", "Represented by Proxy"),
            ("absent", "Absent"),
        ],
        required=True,
        default="present",
    )
    proxy_partner_id = fields.Many2one(comodel_name="res.partner", string="Proxy")
    votes = fields.Float(
        default=1.0,
        digits=(16, 2),
        help="Votes of the attendee: 1 for one head, one vote, or the share "
        "of the capital held.",
    )

    _partner_meeting_uniq = models.Constraint(
        "unique(meeting_id, partner_id)",
        "A person can attend a meeting only once.",
    )

    @api.constrains("attendance", "proxy_partner_id")
    def _check_proxy(self):
        for attendee in self:
            if attendee.attendance == "proxy" and not attendee.proxy_partner_id:
                raise ValidationError(
                    self.env._("Set the proxy of %s.", attendee.partner_id.name)
                )

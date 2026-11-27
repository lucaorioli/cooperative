# Copyright 2026 Luca Orioli <lucaorioli@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class GovernanceBody(models.Model):
    _inherit = "governance.body"
    _check_company_auto = True

    appointment_resolution_id = fields.Many2one(
        comodel_name="governance.resolution",
        string="Appointing Resolution",
        tracking=True,
        check_company=True,
    )
    meeting_ids = fields.One2many(
        comodel_name="governance.meeting",
        inverse_name="body_id",
        string="Meetings",
    )
    meeting_count = fields.Integer(compute="_compute_meeting_count")

    def _compute_meeting_count(self):
        data = self.env["governance.meeting"]._read_group(
            [("body_id", "in", self.ids)], ["body_id"], ["__count"]
        )
        counts = {body.id: count for body, count in data}
        for body in self:
            body.meeting_count = counts.get(body.id, 0)

    def action_view_meetings(self):
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "company_governance_meeting.governance_meeting_action"
        )
        action["domain"] = [("body_id", "in", self.ids)]
        action["context"] = {"default_body_id": self[:1].id}
        return action

# Copyright 2026 Luca Orioli <lucaorioli@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class GovernanceBody(models.Model):
    _name = "governance.body"
    _description = "Corporate Body"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_start desc, id desc"

    name = fields.Char(required=True, tracking=True)
    type_id = fields.Many2one(
        comodel_name="governance.body.type",
        string="Type",
        required=True,
        tracking=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        default=lambda self: self.env.company,
    )
    date_start = fields.Date(
        string="Start Date",
        required=True,
        tracking=True,
        help="Date on which the body took office.",
    )
    date_end = fields.Date(
        string="End of Term",
        tracking=True,
        help="Expected end of the term of office.",
    )
    term_note = fields.Char(
        string="Term",
        help="Term of office as stated in the appointment, "
        "e.g. until the approval of the financial statements of a given year.",
    )
    date_ceased = fields.Date(
        string="Ceased On",
        tracking=True,
        help="Date on which the body actually left office.",
    )
    state = fields.Selection(
        selection=[
            ("active", "In Office"),
            ("extended", "Extended"),
            ("ceased", "Ceased"),
        ],
        default="active",
        required=True,
        tracking=True,
        help="Extended: the term has expired, but the body stays in office "
        "until the new one is appointed.",
    )
    member_ids = fields.One2many(
        comodel_name="governance.body.member",
        inverse_name="body_id",
        string="Members",
    )
    current_member_ids = fields.One2many(
        comodel_name="governance.body.member",
        compute="_compute_current_member_ids",
        string="Current Members",
    )
    note = fields.Html()

    @api.depends("member_ids.is_current")
    def _compute_current_member_ids(self):
        for body in self:
            body.current_member_ids = body.member_ids.filtered("is_current")

    @api.constrains("date_start", "date_end", "date_ceased")
    def _check_dates(self):
        for body in self:
            for date in (body.date_end, body.date_ceased):
                if date and date < body.date_start:
                    raise ValidationError(
                        self.env._(
                            "The dates of %s cannot precede its start date.", body.name
                        )
                    )

    def action_extend(self):
        self.write({"state": "extended"})

    def action_cease(self):
        for body in self:
            date = body.date_ceased or fields.Date.context_today(body)
            body.write({"state": "ceased", "date_ceased": date})
            body.member_ids.filtered(
                lambda m, date=date: not m.date_end or m.date_end > date
            ).write({"date_end": date, "end_reason": "body_ceased"})

    def action_reset_active(self):
        self.write({"state": "active", "date_ceased": False})

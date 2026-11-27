# Copyright 2026 Luca Orioli <lucaorioli@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime

from odoo.exceptions import UserError, ValidationError
from odoo.fields import Command, Date
from odoo.tests import TransactionCase


class TestGovernanceMeeting(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        partner = cls.env["res.partner"]
        cls.alice = partner.create({"name": "Alice"})
        cls.bob = partner.create({"name": "Bob"})
        cls.carol = partner.create({"name": "Carol"})
        cls.body = cls.env["governance.body"].create(
            {
                "name": "Board",
                "type_id": cls.env.ref("company_governance.body_type_board").id,
                "date_start": "2026-01-01",
                "member_ids": [
                    Command.create(
                        {
                            "partner_id": p.id,
                            "role_id": cls.env.ref("company_governance.role_member").id,
                            "date_start": "2026-01-01",
                        }
                    )
                    for p in (cls.alice, cls.bob, cls.carol)
                ],
            }
        )
        cls.meeting = cls.env["governance.meeting"].create(
            {
                "name": "Board meeting",
                "body_id": cls.body.id,
                "date": datetime(2026, 3, 10, 10, 0),
            }
        )

    def test_attendance_and_quorum(self):
        self.meeting.action_load_members()
        self.assertEqual(
            self.meeting.attendee_ids.partner_id, self.body.member_ids.partner_id
        )
        # loading again does not duplicate the attendees
        self.meeting.action_load_members()
        self.assertEqual(self.meeting.attendee_count, 3)
        attendees = {a.partner_id: a for a in self.meeting.attendee_ids}
        attendees[self.bob].write(
            {"attendance": "proxy", "proxy_partner_id": self.alice.id}
        )
        attendees[self.carol].attendance = "absent"
        self.assertEqual(self.meeting.present_count, 2)
        self.assertEqual(self.meeting.present_votes, 2)
        self.assertEqual(self.meeting.total_votes, 3)
        with self.assertRaises(ValidationError):
            attendees[self.carol].attendance = "proxy"

    def test_workflow_and_numbering(self):
        self.meeting.action_convene()
        self.assertEqual(self.meeting.state, "convened")
        first, second = self.env["governance.resolution"].create(
            [
                {"meeting_id": self.meeting.id, "name": "Budget", "sequence": 1},
                {"meeting_id": self.meeting.id, "name": "Appointment", "sequence": 2},
            ]
        )
        self.assertFalse(first.number)
        self.meeting.action_hold()
        self.assertTrue(first.number.startswith("2026/"))
        self.assertLess(first.number, second.number)
        self.assertIn(first.number, first.display_name)
        with self.assertRaises(UserError):
            self.meeting.action_minute()
        self.meeting.minutes = "<p>Minutes</p>"
        self.meeting.action_minute()
        self.assertEqual(self.meeting.state, "minuted")
        report = self.env.ref(
            "company_governance_meeting.action_report_governance_meeting"
        )
        html = report._render_qweb_html(report.report_name, self.meeting.ids)[0]
        self.assertIn(b"Budget", html)
        self.assertEqual(self.meeting._format_votes(4.0), "4")
        self.assertEqual(self.meeting._format_votes(2.5), "2.50")

    def test_multi_company(self):
        other = self.env["res.company"].create({"name": "Other company"})
        board = self.body.copy({"company_id": other.id, "member_ids": False})
        meeting = self.meeting.copy({"body_id": board.id})
        resolutions = self.env["governance.resolution"].create(
            [
                {"meeting_id": m.id, "name": "Budget", "outcome": "approved"}
                for m in (self.meeting, meeting)
            ]
        )
        (self.meeting + meeting).action_hold()
        # each company has its own numbering
        self.assertEqual(resolutions[0].number, resolutions[1].number)
        with self.assertRaises(UserError):
            board.appointment_resolution_id = resolutions[0]

    def test_convocation_date(self):
        with self.assertRaises(ValidationError):
            self.meeting.convocation_date = "2026-03-11"
        self.meeting.convocation_date = "2026-03-01"
        past = self.meeting.copy({"convocation_date": False})
        past.date = datetime(2000, 1, 1, 10, 0)
        # a past meeting registered later gets no convocation date of today
        past.action_convene()
        self.assertFalse(past.convocation_date)
        future = self.meeting.copy({"convocation_date": False})
        future.date = datetime(2999, 1, 1, 10, 0)
        future.action_convene()
        self.assertEqual(future.convocation_date, Date.context_today(future))

    def test_votes(self):
        self.meeting.action_load_members()
        resolution = self.env["governance.resolution"].create(
            {"meeting_id": self.meeting.id, "name": "Budget", "votes_for": 2}
        )
        resolution.votes_against = 1
        with self.assertRaises(ValidationError):
            resolution.votes_abstained = 1
        with self.assertRaises(ValidationError):
            resolution.votes_against = -1

    def test_appointment_links(self):
        resolution = self.env["governance.resolution"].create(
            {"meeting_id": self.meeting.id, "name": "Appointment"}
        )
        self.body.appointment_resolution_id = resolution
        member = self.body.member_ids[0]
        member.end_resolution_id = resolution
        self.assertEqual(resolution.appointed_body_ids, self.body)
        self.assertEqual(resolution.termination_ids, member)
        self.assertEqual(self.body.meeting_count, 1)
        action = self.body.action_view_meetings()
        self.assertEqual(
            self.env["governance.meeting"].search(action["domain"]), self.meeting
        )

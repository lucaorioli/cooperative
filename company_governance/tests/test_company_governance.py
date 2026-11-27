# Copyright 2026 Luca Orioli <lucaorioli@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date, timedelta

from odoo.exceptions import ValidationError
from odoo.fields import Date
from odoo.tests import TransactionCase


class TestCompanyGovernance(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.board_type = cls.env.ref("company_governance.body_type_board")
        cls.chair = cls.env.ref("company_governance.role_chair")
        cls.member_role = cls.env.ref("company_governance.role_member")
        cls.auditor = cls.env.ref("company_governance.role_auditor")
        cls.alice = cls.env["res.partner"].create({"name": "Alice"})
        cls.bob = cls.env["res.partner"].create({"name": "Bob"})
        cls.today = Date.context_today(cls.env.user)
        cls.start = cls.today - timedelta(days=365)
        cls.body = cls.env["governance.body"].create(
            {
                "name": "Board",
                "type_id": cls.board_type.id,
                "date_start": cls.start,
                "date_end": cls.today + timedelta(days=365),
                "member_ids": [
                    (
                        0,
                        0,
                        {
                            "partner_id": cls.alice.id,
                            "role_id": cls.chair.id,
                            "date_start": cls.start,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "partner_id": cls.bob.id,
                            "role_id": cls.member_role.id,
                            "date_start": cls.start,
                        },
                    ),
                ],
            }
        )
        cls.alice_office, cls.bob_office = cls.body.member_ids.sorted("role_id")

    def test_current_members(self):
        self.assertEqual(self.body.current_member_ids, self.body.member_ids)
        self.bob_office.write(
            {"date_end": self.today - timedelta(days=1), "end_reason": "resignation"}
        )
        self.assertFalse(self.bob_office.is_current)
        self.assertEqual(self.body.current_member_ids, self.alice_office)
        Member = self.env["governance.body.member"]
        current = Member.search(
            [("body_id", "=", self.body.id), ("is_current", "=", True)]
        )
        self.assertEqual(current, self.alice_office)
        past = Member.search(
            [("body_id", "=", self.body.id), ("is_current", "!=", True)]
        )
        self.assertEqual(past, self.bob_office)

    def test_partner_offices(self):
        self.assertEqual(self.alice.governance_member_ids, self.alice_office)
        self.assertIn("Alice", self.alice_office.display_name)
        self.assertIn(self.chair.name, self.alice_office.display_name)

    def test_extend_and_cease(self):
        self.body.action_extend()
        self.assertEqual(self.body.state, "extended")
        self.assertTrue(self.alice_office.is_current)
        self.bob_office.date_end = self.today - timedelta(days=10)
        self.body.action_cease()
        self.assertEqual(self.body.state, "ceased")
        self.assertEqual(self.body.date_ceased, self.today)
        self.assertEqual(self.alice_office.date_end, self.today)
        self.assertEqual(self.alice_office.end_reason, "body_ceased")
        # a member who had already left keeps their end date
        self.assertEqual(self.bob_office.date_end, self.today - timedelta(days=10))
        self.assertFalse(self.body.current_member_ids)
        self.body.action_reset_active()
        self.assertEqual(self.body.state, "active")
        self.assertFalse(self.body.date_ceased)

    def test_role_not_allowed(self):
        with self.assertRaises(ValidationError):
            self.alice_office.role_id = self.auditor
        committee = self.env.ref("company_governance.body_type_committee")
        self.body.type_id = committee
        # no allowed offices on the type: any office can be held
        self.alice_office.role_id = self.auditor

    def test_dates(self):
        with self.assertRaises(ValidationError):
            self.alice_office.date_end = self.start - timedelta(days=1)
        with self.assertRaises(ValidationError):
            self.alice_office.date_start = self.start - timedelta(days=1)
        with self.assertRaises(ValidationError):
            self.body.date_end = date(2000, 1, 1)

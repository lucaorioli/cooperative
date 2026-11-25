# Copyright 2026 Luca Orioli <lucaorioli@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import HttpCase, tagged

from odoo.addons.cooperator.tests.cooperator_test_mixin import CooperatorTestMixin


@tagged("-at_install", "post_install")
class CooperatorPortalCase(HttpCase, CooperatorTestMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.set_up_cooperator_test_data()
        cls.subscription_request_1.validate_subscription_request()
        cls.capital_release_request = cls.subscription_request_1.capital_release_request
        cls.partner = cls.subscription_request_1.partner_id
        cls.user = cls.env["res.users"].create(
            {
                "name": "Portal Cooperator",
                "login": "portal_cooperator",
                "password": "portal_cooperator",
                "partner_id": cls.partner.id,
                "groups_id": [(6, 0, [cls.env.ref("base.group_portal").id])],
            }
        )

    def setUp(self):
        super().setUp()
        self.authenticate("portal_cooperator", "portal_cooperator")

    def test_capital_release_requests_list(self):
        response = self.url_open("/my/capital_release_requests")
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.capital_release_request.name, response.text)
        self.assertIn("Request #", response.text)

    def test_capital_release_requests_excluded_from_invoices(self):
        response = self.url_open("/my/invoices")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(self.capital_release_request.name, response.text)

    def test_capital_release_request_detail(self):
        self.assertEqual(
            self.capital_release_request.access_url,
            f"/my/capital_release_requests/{self.capital_release_request.id}",
        )
        response = self.url_open(self.capital_release_request.access_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.capital_release_request.name, response.text)

    def test_home_counter(self):
        response = self.url_open("/my/home")
        self.assertEqual(response.status_code, 200)
        self.assertIn("/my/capital_release_requests", response.text)
        values = self.make_jsonrpc_request(
            "/my/counters", {"counters": ["capital_release_request_count"]}
        )
        self.assertEqual(values["capital_release_request_count"], 1)

    def test_account_details_form(self):
        response = self.url_open("/my/account")
        self.assertEqual(response.status_code, 200)
        for field in ("gender", "lang", "birthdate_date", "iban"):
            self.assertIn(f'name="{field}"', response.text)

    def test_cooperator_certificate(self):
        self.pay_invoice(self.capital_release_request)
        response = self.url_open("/my/cooperator_certificate/pdf")
        self.assertEqual(response.status_code, 200)

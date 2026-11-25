# SPDX-FileCopyrightText: 2026 Luca Orioli <lucaorioli@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from odoo import http
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
                "group_ids": [(6, 0, [cls.env.ref("base.group_portal").id])],
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

    def _submit_account_details(self, **values):
        data = {
            "name": self.partner.name,
            "email": self.partner.email,
            "phone": "+39 000 000 0000",
            "street": "Via di Prova 1",
            "city": "Roma",
            "zip": "00100",
            "country_id": str(self.partner.country_id.id),
            "partner_id": str(self.partner.id),
            "address_type": "billing",
            "use_delivery_as_billing": "true",
            "required_fields": "name,email",
            "cooperator_details": "1",
            "gender": "female",
            "lang": "en_US",
            "birthdate_date": "1980-01-01",
            "csrf_token": http.Request.csrf_token(self),
        }
        data.update(values)
        response = self.url_open("/my/address/submit", data=data)
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_account_details_submit(self):
        feedback = self._submit_account_details(iban="BE60096123456870")
        self.assertFalse(feedback.get("invalid_fields"), feedback)
        self.assertEqual(
            self.partner.bank_ids[:1].sanitized_acc_number, "BE60096123456870"
        )
        self.assertEqual(self.partner.gender, "female")
        self.assertEqual(str(self.partner.birthdate_date), "1980-01-01")

    def test_account_details_invalid_iban(self):
        feedback = self._submit_account_details(iban="not an iban")
        self.assertIn("iban", feedback["invalid_fields"])

    def test_account_details_missing_fields(self):
        feedback = self._submit_account_details(gender="", iban="BE60096123456870")
        self.assertIn("gender", feedback["invalid_fields"])

    def test_cooperator_certificate(self):
        self.pay_invoice(self.capital_release_request)
        response = self.url_open("/my/cooperator_certificate/pdf")
        self.assertEqual(response.status_code, 200)

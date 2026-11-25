# SPDX-FileCopyrightText: 2026 Luca Orioli <lucaorioli@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from odoo import http
from odoo.tests.common import HttpCase, tagged

from odoo.addons.cooperator.tests.cooperator_test_mixin import CooperatorTestMixin


@tagged("-at_install", "post_install")
class SubscriptionFormCase(HttpCase, CooperatorTestMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.set_up_cooperator_test_data()
        (cls.share_x + cls.share_y).product_tmpl_id.display_on_website = True
        cls.company.write(
            {
                "data_policy_approval_required": False,
                "internal_rules_approval_required": False,
                "financial_risk_approval_required": False,
                "generic_rules_approval_required": False,
            }
        )

    def setUp(self):
        super().setUp()
        # open a public session, needed for the csrf token of the form
        self.authenticate(None, None)

    def _get_form_data(self, **values):
        data = {
            "firstname": "Web",
            "lastname": "Cooperator",
            "email": "web.cooperator@example.org",
            "confirm_email": "web.cooperator@example.org",
            "birthdate": "1980-01-01",
            "gender": "female",
            "iban": "BE60096123456870",
            "address": "Cooperation Street 1",
            "zip_code": "1000",
            "city": "Brussels",
            "country_id": str(self.env.ref("base.be").id),
            "phone": "+32 000 00 00 00",
            "lang": "en_US",
            "share_product_id": str(self.share_y.product_tmpl_id.id),
            "ordered_parts": "2",
            "csrf_token": http.Request.csrf_token(self),
        }
        data.update(values)
        return data

    def test_become_cooperator_page(self):
        response = self.url_open("/become_cooperator")
        self.assertEqual(response.status_code, 200)
        self.assertIn("oe_cooperator", response.text)
        self.assertIn(self.share_y.short_name, response.text)

    def test_become_company_cooperator_page(self):
        response = self.url_open("/become_company_cooperator")
        self.assertEqual(response.status_code, 200)
        self.assertIn('name="company_name"', response.text)

    def test_get_share_product(self):
        product_tmpl = self.share_y.product_tmpl_id
        result = self.make_jsonrpc_request(
            "/subscription/get_share_product",
            {"share_product_id": product_tmpl.id},
        )
        self.assertEqual(
            result[str(product_tmpl.id)],
            {"list_price": 25.0, "min_qty": 2, "force_min_qty": True},
        )

    def test_subscribe(self):
        response = self.url_open(
            "/subscription/subscribe_share", data=self._get_form_data()
        )
        self.assertEqual(response.status_code, 200)
        subscription_request = self.env["subscription.request"].search(
            [("email", "=", "web.cooperator@example.org")]
        )
        self.assertEqual(len(subscription_request), 1)
        self.assertEqual(subscription_request.source, "website")
        self.assertEqual(subscription_request.share_product_id, self.share_y)
        self.assertEqual(subscription_request.ordered_parts, 2)
        self.assertEqual(subscription_request.state, "draft")

    def test_subscribe_company(self):
        data = self._get_form_data(
            is_company="on",
            company_name="Web Company",
            company_email="web.company@example.org",
            confirm_email="web.company@example.org",
            company_register_number="BE 0123.456.789",
        )
        response = self.url_open("/subscription/subscribe_share", data=data)
        self.assertEqual(response.status_code, 200)
        subscription_request = self.env["subscription.request"].search(
            [("company_email", "=", "web.company@example.org")]
        )
        self.assertEqual(len(subscription_request), 1)
        self.assertTrue(subscription_request.is_company)
        self.assertEqual(subscription_request.company_register_number, "BE0123456789")

    def test_subscribe_below_minimum_quantity(self):
        response = self.url_open(
            "/subscription/subscribe_share",
            data=self._get_form_data(ordered_parts="1"),
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Number of shares must be at least 2.", response.text)
        self.assertFalse(
            self.env["subscription.request"].search(
                [("email", "=", "web.cooperator@example.org")]
            )
        )

    def test_subscribe_with_id_card(self):
        self.company.allow_id_card_upload = True
        response = self.url_open(
            "/subscription/subscribe_share",
            data=self._get_form_data(),
            files={"identity_card_scan": ("id_card.txt", b"id card", "text/plain")},
        )
        self.assertEqual(response.status_code, 200)
        subscription_request = self.env["subscription.request"].search(
            [("email", "=", "web.cooperator@example.org")]
        )
        attachment = self.env["ir.attachment"].search(
            [
                ("res_model", "=", "subscription.request"),
                ("res_id", "=", subscription_request.id),
            ]
        )
        self.assertEqual(attachment.name, "id_card.txt")

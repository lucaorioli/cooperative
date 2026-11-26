# SPDX-FileCopyrightText: 2026 Luca Orioli <lucaorioli@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from unittest import mock

from odoo import http
from odoo.tests.common import HttpCase, tagged

from odoo.addons.cooperator.tests.cooperator_test_mixin import CooperatorTestMixin

REQUESTS = "odoo.addons.website_recaptcha_v2.models.website.requests"


@tagged("-at_install", "post_install")
class TestRecaptchaSubscription(HttpCase, CooperatorTestMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.set_up_cooperator_test_data()
        cls.share_y.product_tmpl_id.display_on_website = True
        cls.company.write(
            {
                "data_policy_approval_required": False,
                "internal_rules_approval_required": False,
                "financial_risk_approval_required": False,
                "generic_rules_approval_required": False,
            }
        )
        cls.env.ref("website.default_website").write(
            {
                "recaptcha_v2_enabled": True,
                "recaptcha_v2_site_key": "test-site",
                "recaptcha_v2_secret_key": "test-secret",
            }
        )

    def setUp(self):
        super().setUp()
        self.authenticate(None, None)

    def _subscribe(self):
        data = {
            "firstname": "Web",
            "lastname": "Cooperator",
            "email": "captcha.cooperator@example.org",
            "confirm_email": "captcha.cooperator@example.org",
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
            "g-recaptcha-response": "dummy_response",
            "csrf_token": http.Request.csrf_token(self),
        }
        response = self.url_open("/subscription/subscribe_share", data=data)
        requests = self.env["subscription.request"].search(
            [("email", "=", "captcha.cooperator@example.org")]
        )
        return response, requests

    def test_form_shows_widget(self):
        response = self.url_open("/become_cooperator")
        self.assertIn('class="g-recaptcha"', response.text)

    @mock.patch(REQUESTS)
    def test_captcha_failed(self, requests_mock):
        requests_mock.post().json.return_value = {"success": False}
        response, requests = self._subscribe()
        self.assertEqual(response.status_code, 200)
        self.assertIn("Error validating the CAPTCHA", response.text)
        self.assertFalse(requests)

    @mock.patch(REQUESTS)
    def test_captcha_solved(self, requests_mock):
        requests_mock.post().json.return_value = {"success": True}
        response, requests = self._subscribe()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(requests), 1)

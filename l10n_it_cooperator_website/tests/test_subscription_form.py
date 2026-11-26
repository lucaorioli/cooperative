# Copyright 2026 Luca Orioli <lucaorioli@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import http
from odoo.tests.common import HttpCase, tagged

from odoo.addons.cooperator.tests.cooperator_test_mixin import CooperatorTestMixin

PERSON_CF = "RSSMRA85T10A562S"
COMPANY_CF = "07149930583"


@tagged("-at_install", "post_install")
class TestItSubscriptionForm(HttpCase, CooperatorTestMixin):
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
        # website_recaptcha_v2 enables the reCAPTCHA in its demo data
        website = cls.env.ref("website.default_website")
        if "recaptcha_v2_enabled" in website._fields:
            website.recaptcha_v2_enabled = False
        cls.SubscriptionRequest = cls.env["subscription.request"]

    def setUp(self):
        super().setUp()
        self.authenticate(None, None)

    def _get_form_data(self, **values):
        data = {
            "firstname": "Mario",
            "lastname": "Rossi",
            "email": "mario.rossi@example.org",
            "confirm_email": "mario.rossi@example.org",
            "birthdate": "1985-12-10",
            "gender": "male",
            "iban": "IT60X0542811101000000123456",
            "address": "Via di Prova 1",
            "zip_code": "00100",
            "city": "Roma",
            "country_id": str(self.env.ref("base.it").id),
            "phone": "+39 000 000 0000",
            "lang": "en_US",
            "share_product_id": str(self.share_y.product_tmpl_id.id),
            "ordered_parts": "2",
            "l10n_it_codice_fiscale": "rssmra85t10a562s",
            "csrf_token": http.Request.csrf_token(self),
        }
        data.update(values)
        return data

    def _subscribe(self, **values):
        response = self.url_open(
            "/subscription/subscribe_share", data=self._get_form_data(**values)
        )
        self.assertEqual(response.status_code, 200)
        return response

    def test_form_fields(self):
        response = self.url_open("/become_cooperator")
        self.assertIn('name="l10n_it_codice_fiscale"', response.text)
        self.assertIn('name="iban"', response.text)
        response = self.url_open("/become_company_cooperator")
        self.assertIn("Company Fiscal Code", response.text)

    def test_subscribe(self):
        self._subscribe()
        request = self.SubscriptionRequest.search(
            [("email", "=", "mario.rossi@example.org")]
        )
        self.assertEqual(len(request), 1)
        self.assertEqual(request.l10n_it_codice_fiscale, PERSON_CF)
        self.assertEqual(request.iban, "IT60X0542811101000000123456")

    def test_subscribe_without_codice_fiscale(self):
        response = self._subscribe(l10n_it_codice_fiscale="")
        self.assertIn("The fiscal code is required", response.text)
        self.assertFalse(
            self.SubscriptionRequest.search([("email", "=", "mario.rossi@example.org")])
        )
        # not required for a subscriber living abroad
        self._subscribe(
            l10n_it_codice_fiscale="", country_id=str(self.env.ref("base.fr").id)
        )
        self.assertTrue(
            self.SubscriptionRequest.search([("email", "=", "mario.rossi@example.org")])
        )

    def test_subscribe_invalid_codice_fiscale(self):
        response = self._subscribe(l10n_it_codice_fiscale="RSSMRA85T10A562X")
        self.assertIn("is not a valid Italian fiscal code", response.text)
        self.assertIn('value="RSSMRA85T10A562X"', response.text)
        self.assertFalse(
            self.SubscriptionRequest.search([("email", "=", "mario.rossi@example.org")])
        )

    def test_subscribe_company(self):
        self._subscribe(
            is_company="on",
            company_name="Impresa di Prova S.r.l.",
            company_email="impresa@example.org",
            confirm_email="impresa@example.org",
            company_register_number="RM-123456",
            company_type="it_srl",
            l10n_it_codice_fiscale=COMPANY_CF,
        )
        request = self.SubscriptionRequest.search(
            [("company_email", "=", "impresa@example.org")]
        )
        self.assertEqual(len(request), 1)
        self.assertEqual(request.company_type, "it_srl")
        self.assertEqual(request.l10n_it_codice_fiscale, COMPANY_CF)

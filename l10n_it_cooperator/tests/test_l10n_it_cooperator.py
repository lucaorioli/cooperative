# Copyright 2026 Luca Orioli <lucaorioli@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, tagged

from odoo.addons.cooperator.tests.cooperator_test_mixin import CooperatorTestMixin

PERSON_CF = "RSSMRA85T10A562S"
COMPANY_CF = "07149930583"
OTHER_CF = "VRDNNA80A41H501H"


@tagged("post_install", "-at_install")
class TestL10nItCooperator(TransactionCase, CooperatorTestMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.set_up_cooperator_test_data()
        cls.it_company = cls.env["res.company"].create(
            {"name": "Cooperativa di prova", "country_id": cls.env.ref("base.it").id}
        )
        cls.env["account.chart.template"].try_loading(
            "it", cls.it_company, install_demo=False
        )
        cls.env.user.company_ids |= cls.it_company
        cls.env = cls.env(
            context=dict(cls.env.context, allowed_company_ids=cls.it_company.ids)
        )
        cls.SubscriptionRequest = cls.env["subscription.request"].with_company(
            cls.it_company
        )
        Account = cls.env["account.account"].with_company(cls.it_company)
        cls.receivable_account = Account.create(
            {
                "code": "150150",
                "name": "Crediti verso soci",
                "account_type": "asset_receivable",
                "reconcile": True,
            }
        )
        cls.capital_account = Account.create(
            {"code": "210150", "name": "Capitale sociale", "account_type": "equity"}
        )
        cls.it_company.property_cooperator_account = cls.receivable_account
        cls._set_share_capital_account(cls.capital_account)

    @classmethod
    def _set_share_capital_account(cls, account):
        settings = (
            cls.env["res.config.settings"]
            .with_company(cls.it_company)
            .create({"l10n_it_share_capital_account_id": account.id})
        )
        settings.execute()

    def _request_vals(self, **vals):
        values = {
            "firstname": "Mario",
            "lastname": "Rossi",
            "email": "mario.rossi@example.org",
            "address": "Via di Prova 1",
            "zip_code": "00100",
            "city": "Roma",
            "lang": "en_US",
            "country_id": self.env.ref("base.it").id,
            "source": "manual",
            "ordered_parts": 2,
            "share_product_id": self.share_y.id,
            "company_id": self.it_company.id,
            "data_policy_approved": True,
            "internal_rules_approved": True,
            "financial_risk_approved": True,
            "generic_rules_approved": True,
            "skip_iban_control": True,
        }
        values.update(vals)
        return values

    def test_no_account_created(self):
        # the module creates no account: the user chooses them in the settings
        accounts = self.env["account.account"].search(
            [("company_ids", "in", self.it_company.ids)]
        )
        self.assertFalse(
            accounts.filtered(
                lambda a: a.with_company(self.it_company).code in ("1001", "2110")
            )
        )

    def test_share_capital_account_setting(self):
        settings = (
            self.env["res.config.settings"].with_company(self.it_company).create({})
        )
        self.assertEqual(
            settings.l10n_it_share_capital_account_id, self.capital_account
        )
        category = self.env.ref("cooperator.product_category_company_share")
        # emptied: the category gets back the default income account, shown as
        # not set (with the warning)
        self._set_share_capital_account(self.env["account.account"])
        default_income = category.with_company(
            self.it_company
        ).property_account_income_categ_id
        self.assertNotEqual(default_income, self.capital_account)
        settings = (
            self.env["res.config.settings"].with_company(self.it_company).create({})
        )
        self.assertFalse(settings.l10n_it_share_capital_account_id)

    def test_capital_release_request(self):
        request = self.SubscriptionRequest.create(
            self._request_vals(l10n_it_codice_fiscale=PERSON_CF)
        )
        request.validate_subscription_request()
        invoice = request.capital_release_request
        self.assertEqual(invoice.state, "posted")
        self.assertEqual(
            invoice.invoice_line_ids.account_id,
            self.capital_account,
            "the shares go to the share capital, not to the revenue",
        )
        self.assertEqual(
            invoice.line_ids.filtered(
                lambda line: line.display_type == "payment_term"
            ).account_id,
            self.receivable_account,
        )
        self.assertFalse(invoice._l10n_it_edi_ready_for_xml_export())
        partner = request.partner_id
        self.assertEqual(partner.l10n_it_codice_fiscale, PERSON_CF)

    def test_codice_fiscale_validation(self):
        with self.assertRaises(ValidationError):
            self.SubscriptionRequest.create(
                self._request_vals(l10n_it_codice_fiscale="RSSMRA85T10A562X")
            )
        request = self.SubscriptionRequest.create(
            self._request_vals(l10n_it_codice_fiscale="rssmra 85t10 a562s")
        )
        self.assertEqual(request.l10n_it_codice_fiscale, PERSON_CF)
        # a VAT number with the country prefix, as on the partner
        request.write({"is_company": True, "l10n_it_codice_fiscale": "IT07149930583"})
        self.assertEqual(request.l10n_it_codice_fiscale, COMPANY_CF)

    def test_codice_fiscale_required_in_italy(self):
        request = self.SubscriptionRequest.create(self._request_vals())
        with self.assertRaises(UserError):
            request.validate_subscription_request()
        # not required for a subscriber living abroad
        request = self.SubscriptionRequest.create(
            self._request_vals(
                email="abroad@example.org", country_id=self.env.ref("base.fr").id
            )
        )
        request.validate_subscription_request()
        self.assertEqual(request.state, "done")

    def test_partner_found_by_codice_fiscale(self):
        partner = self.env["res.partner"].create(
            {
                "firstname": "Mario",
                "lastname": "Rossi",
                "email": "other.address@example.org",
                "l10n_it_codice_fiscale": PERSON_CF,
            }
        )
        request = self.SubscriptionRequest.create(
            self._request_vals(l10n_it_codice_fiscale=PERSON_CF)
        )
        self.assertEqual(request.partner_id, partner)
        request.validate_subscription_request()
        self.assertEqual(request.partner_id, partner)

    def test_company_request(self):
        request = self.SubscriptionRequest.create(
            self._request_vals(
                is_company=True,
                company_name="Impresa di Prova S.r.l.",
                company_email="impresa@example.org",
                company_register_number="RM-123456",
                company_type="it_srl",
                contact_person_function="Legale rappresentante",
                l10n_it_codice_fiscale=COMPANY_CF,
                share_product_id=self.share_y.id,
            )
        )
        request.validate_subscription_request()
        partner = request.partner_id
        self.assertTrue(partner.is_company)
        self.assertEqual(partner.legal_form, "it_srl")
        self.assertEqual(partner.l10n_it_codice_fiscale, COMPANY_CF)
        # a new request with the same fiscal code finds the company
        partner.company_register_number = False
        request_2 = self.SubscriptionRequest.create(
            self._request_vals(
                is_company=True,
                company_name="Impresa di Prova S.r.l.",
                company_email="impresa@example.org",
                company_register_number="RM-999999",
                l10n_it_codice_fiscale=COMPANY_CF,
            )
        )
        request_2._find_or_create_partner()
        self.assertEqual(request_2.partner_id, partner)

    def test_reports(self):
        self.it_company.write(
            {
                "l10n_it_coop_register_number": "A123456",
                "l10n_it_coop_register_section": "prevailing",
                "l10n_it_coop_register_category": "social",
            }
        )
        request = self.SubscriptionRequest.create(
            self._request_vals(l10n_it_codice_fiscale=PERSON_CF)
        )
        request.validate_subscription_request()
        self.pay_invoice(request.capital_release_request)
        partner = request.partner_id.with_company(self.it_company)
        self.assertTrue(partner.member)
        report = self.env["ir.actions.report"].with_company(self.it_company)
        html = report._render_qweb_html(
            "cooperator.action_cooperator_report_certificate", partner.ids
        )[0].decode()
        self.assertIn(PERSON_CF, html)
        self.assertIn("A123456", html)
        html = report._render_qweb_html(
            "cooperator.action_report_cooperator_register",
            partner.cooperative_membership_id.ids,
        )[0].decode()
        self.assertIn(PERSON_CF, html)
        self.assertIn("Via di Prova 1", html)

    def _new_member(self, **vals):
        request = self.SubscriptionRequest.create(self._request_vals(**vals))
        request.validate_subscription_request()
        self.pay_invoice(request.capital_release_request)
        return request.partner_id.get_cooperative_membership(self.it_company)

    def test_member_type(self):
        membership = self._new_member(
            l10n_it_codice_fiscale=PERSON_CF, l10n_it_member_type="worker"
        )
        self.assertTrue(membership.member)
        self.assertEqual(membership.l10n_it_member_type, "worker")
        self.assertEqual(
            membership.l10n_it_admission_date,
            membership.share_ids[:1].effective_date,
        )
        with self.assertRaises(ValidationError):
            membership.l10n_it_special_category = True
        membership.write(
            {
                "l10n_it_special_category": True,
                "l10n_it_special_category_end": "2030-12-31",
            }
        )

    def test_member_of_two_companies(self):
        other = self.env["res.company"].create(
            {"name": "Seconda cooperativa", "country_id": self.env.ref("base.it").id}
        )
        self.env["account.chart.template"].try_loading("it", other, install_demo=False)
        self.env.user.company_ids |= other
        other.property_cooperator_account = (
            self.env["account.account"]
            .with_company(other)
            .create(
                {
                    "code": "150150",
                    "name": "Crediti verso soci",
                    "account_type": "asset_receivable",
                    "reconcile": True,
                }
            )
        )
        first = self._new_member(
            l10n_it_codice_fiscale=PERSON_CF, l10n_it_member_type="worker"
        )
        partner = first.partner_id
        request = (
            self.env["subscription.request"]
            .with_company(other)
            .with_context(allowed_company_ids=[other.id, self.it_company.id])
            .create(
                self._request_vals(
                    company_id=other.id,
                    l10n_it_codice_fiscale=PERSON_CF,
                    l10n_it_member_type="user",
                    ordered_parts=3,
                )
            )
        )
        request.validate_subscription_request()
        self.pay_invoice(request.capital_release_request)
        # the fiscal code finds the same partner, with a membership per company
        self.assertEqual(request.partner_id, partner)
        second = partner.get_cooperative_membership(other)
        self.assertNotEqual(first, second)
        self.assertTrue(first.member and second.member)
        self.assertEqual(first.number_of_share, 2)
        self.assertEqual(second.number_of_share, 3)
        self.assertEqual(
            partner.with_company(self.it_company).l10n_it_member_type, "worker"
        )
        self.assertEqual(partner.with_company(other).l10n_it_member_type, "user")
        self.assertEqual(partner.with_company(other).number_of_share, 3)
        # one register for each company
        html = (
            self.env["ir.actions.report"]
            .with_context(allowed_company_ids=[self.it_company.id, other.id])
            ._render_qweb_html(
                "cooperator.action_report_cooperator_register", (first + second).ids
            )[0]
            .decode()
        )
        self.assertEqual(html.count("Members Register"), 2)
        self.assertIn("Seconda cooperativa", html)

    def test_volunteers(self):
        membership = self._new_member(l10n_it_codice_fiscale=PERSON_CF)
        # not a social cooperative: no volunteer
        with self.assertRaises(ValidationError):
            membership.l10n_it_member_type = "volunteer"
        self.it_company.l10n_it_social_coop_type = "a"
        # one volunteer out of one member: more than half
        with self.assertRaises(ValidationError):
            membership.l10n_it_member_type = "volunteer"
        self._new_member(
            email="worker@example.org",
            firstname="Anna",
            l10n_it_codice_fiscale=OTHER_CF,
            l10n_it_member_type="worker",
        )
        membership.l10n_it_member_type = "volunteer"
        self.assertEqual(membership.l10n_it_member_type, "volunteer")

    def _operation(self, **vals):
        operation = (
            self.env["operation.request"]
            .with_company(self.it_company)
            .create(
                dict(
                    {
                        "share_product_id": self.share_y.id,
                        "company_id": self.it_company.id,
                    },
                    **vals,
                )
            )
        )
        operation.submit_operation()
        operation.approve_operation()
        operation.execute_operation()
        return operation

    def test_register_operations_and_termination(self):
        supporter_share = self.share_x.product_tmpl_id
        supporter_share.l10n_it_share_category = "supporter"
        giver = self._new_member(l10n_it_codice_fiscale=PERSON_CF, ordered_parts=4)
        receiver = self._new_member(
            email="receiver@example.org",
            firstname="Anna",
            l10n_it_codice_fiscale=OTHER_CF,
            ordered_parts=2,
        )
        self._operation(
            partner_id=giver.partner_id.id,
            partner_id_to=receiver.partner_id.id,
            operation_type="transfer",
            quantity=1,
        )
        lines = giver._l10n_it_register_lines("cooperator")
        self.assertEqual([line["quantity"] for line in lines], [4, -1])
        self.assertEqual(
            [
                line["quantity"]
                for line in receiver._l10n_it_register_lines("cooperator")
            ],
            [2, 1],
        )
        self.assertFalse(giver._l10n_it_register_lines("supporter"))
        self.assertEqual(giver._l10n_it_register_holding("cooperator")["quantity"], 3)
        report = self.env["ir.actions.report"].with_company(self.it_company)
        html = report._render_qweb_html(
            "cooperator.action_report_cooperator_register", (giver + receiver).ids
        )[0].decode()
        self.assertIn("Members Register", html)
        self.assertIn("Transfer to", html)
        self.assertIn("Transfer from", html)
        self.assertIn(PERSON_CF, html)
        # selling back all the shares ends the membership
        self._operation(
            partner_id=giver.partner_id.id,
            operation_type="sell_back",
            quantity=3,
            effective_date="2026-06-30",
        )
        self.assertTrue(giver.old_member)
        self.assertEqual(str(giver.l10n_it_termination_date), "2026-06-30")
        self.assertEqual(giver.l10n_it_termination_reason, "withdrawal")
        # the former member stays in the register, with the admission date
        self.assertTrue(giver.l10n_it_admission_date)
        html = report._render_qweb_html(
            "cooperator.action_report_cooperator_register", giver.ids
        )[0].decode()
        self.assertIn("Withdrawal", html)

# Copyright 2026 Luca Orioli <lucaorioli@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from stdnum.it import codicefiscale, iva

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from .member_category import MEMBER_TYPES
from .res_partner import LEGAL_FORMS, LEGAL_FORMS_ONDELETE


class SubscriptionRequest(models.Model):
    _inherit = "subscription.request"

    company_type = fields.Selection(
        selection_add=LEGAL_FORMS, ondelete=LEGAL_FORMS_ONDELETE
    )
    l10n_it_codice_fiscale = fields.Char(
        string="Fiscal Code",
        size=16,
        help="Italian fiscal code of the person or, for a company, of the "
        "company. Required for subscribers living in Italy.",
    )
    country_code = fields.Char(related="country_id.code")
    l10n_it_member_type = fields.Selection(
        MEMBER_TYPES,
        string="Member Type",
        help="Mutual relationship of the new member with the cooperative, "
        "set on the membership when the request is validated.",
    )

    @api.model
    def _l10n_it_normalize_codice_fiscale(self, value):
        """Normalize as on the partner (l10n_it_edi), which also removes the
        country prefix of a VAT number used as fiscal code.
        """
        value = (value or "").replace(" ", "").upper()
        if not value:
            return value
        return self.env["res.partner"]._l10n_it_edi_normalized_codice_fiscale(value)

    @api.model
    def _l10n_it_check_codice_fiscale(self, value):
        """Same rule as the partner constraint of l10n_it_edi: a personal
        fiscal code or, for a company, a VAT number.
        """
        value = self._l10n_it_normalize_codice_fiscale(value)
        return codicefiscale.is_valid(value) or iva.is_valid(value)

    @api.constrains("l10n_it_codice_fiscale")
    def _check_l10n_it_codice_fiscale(self):
        for request in self:
            if request.l10n_it_codice_fiscale and not (
                self._l10n_it_check_codice_fiscale(request.l10n_it_codice_fiscale)
            ):
                raise ValidationError(
                    self.env._(
                        "%(code)s is not a valid Italian fiscal code.",
                        code=request.l10n_it_codice_fiscale,
                    )
                )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("l10n_it_codice_fiscale"):
                vals["l10n_it_codice_fiscale"] = self._l10n_it_normalize_codice_fiscale(
                    vals["l10n_it_codice_fiscale"]
                )
        return super().create(vals_list)

    def write(self, vals):
        if vals.get("l10n_it_codice_fiscale"):
            vals["l10n_it_codice_fiscale"] = self._l10n_it_normalize_codice_fiscale(
                vals["l10n_it_codice_fiscale"]
            )
        return super().write(vals)

    def _l10n_it_codice_fiscale_required(self):
        """The fiscal code is required for the subscribers living in Italy."""
        self.ensure_one()
        return self.country_code == "IT"

    def validate_subscription_request(self):
        for request in self:
            if (
                request._l10n_it_codice_fiscale_required()
                and not request.l10n_it_codice_fiscale
            ):
                raise UserError(
                    self.env._(
                        "The fiscal code is required for the subscribers "
                        "living in Italy (%(name)s).",
                        name=request.name,
                    )
                )
        return super().validate_subscription_request()

    @api.model
    def _find_partner_from_create_vals(self, vals):
        # the fiscal code identifies the partner better than the email
        if not vals.get("partner_id") and vals.get("l10n_it_codice_fiscale"):
            partner = self.env["res.partner"].search(
                self._l10n_it_partner_domain(
                    vals["l10n_it_codice_fiscale"], vals.get("is_company")
                ),
                limit=1,
            )
            if partner:
                vals["partner_id"] = partner.id
                return partner
        return super()._find_partner_from_create_vals(vals)

    @api.model
    def _l10n_it_partner_domain(self, codice_fiscale, is_company):
        return [
            (
                "l10n_it_codice_fiscale",
                "=",
                self._l10n_it_normalize_codice_fiscale(codice_fiscale),
            ),
            ("is_company", "=", bool(is_company)),
        ]

    def _get_partner_domain(self):
        # used for the person: the subscriber or the company representative
        if self.l10n_it_codice_fiscale and not self.is_company:
            return self._l10n_it_partner_domain(self.l10n_it_codice_fiscale, False)
        return super()._get_partner_domain()

    def _find_or_create_partner(self):
        if (
            not self.partner_id
            and self.is_company
            and self.l10n_it_codice_fiscale
            and not self.already_cooperator
        ):
            partner = self.env["res.partner"].search(
                self._l10n_it_partner_domain(self.l10n_it_codice_fiscale, True),
                limit=1,
            )
            if partner:
                self.partner_id = partner
        return super()._find_or_create_partner()

    def get_partner_vals(self):
        vals = super().get_partner_vals()
        vals["l10n_it_codice_fiscale"] = self.l10n_it_codice_fiscale
        return vals

    def get_partner_company_vals(self):
        vals = super().get_partner_company_vals()
        vals["l10n_it_codice_fiscale"] = self.l10n_it_codice_fiscale
        return vals

    def set_person_info(self, partner):
        result = super().set_person_info(partner)
        self.l10n_it_codice_fiscale = partner.l10n_it_codice_fiscale
        return result

    @api.onchange("partner_id")
    def onchange_partner(self):
        result = super().onchange_partner()
        if self.partner_id.l10n_it_codice_fiscale:
            self.l10n_it_codice_fiscale = self.partner_id.l10n_it_codice_fiscale
        return result

    def set_membership(self):
        result = super().set_membership()
        for request in self.filtered("l10n_it_member_type"):
            membership = request.partner_id.get_cooperative_membership(
                request.company_id
            )
            if membership and not membership.l10n_it_member_type:
                membership.l10n_it_member_type = request.l10n_it_member_type
        return result

# Copyright 2026 Luca Orioli <lucaorioli@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.http import request

from odoo.addons.cooperator_website.controllers.main import WebsiteSubscription


class WebsiteSubscriptionIt(WebsiteSubscription):
    def get_values_from_user(self, values, is_company):
        values = super().get_values_from_user(values, is_company)
        if not request.website.is_public_user():
            # the partner is the company for a company subscription
            partner = request.env.user.partner_id
            values["l10n_it_codice_fiscale"] = partner.l10n_it_codice_fiscale
        return values

    def _additional_validate(self, kwargs, logged, values, post_file):
        result = super()._additional_validate(kwargs, logged, values, post_file)
        if result is not True:
            return result
        sub_req_model = request.env["subscription.request"]
        codice_fiscale = kwargs.get("l10n_it_codice_fiscale", "").strip()
        country_id = kwargs.get("country_id")
        if not codice_fiscale:
            italy = request.env.ref("base.it")
            if country_id and country_id.isdigit() and int(country_id) == italy.id:
                values["error_msg"] = request.env._(
                    "The fiscal code is required for the subscribers living in Italy."
                )
                values["error"] = {"l10n_it_codice_fiscale"}
                return False
            return True
        if not sub_req_model._l10n_it_check_codice_fiscale(codice_fiscale):
            values["error_msg"] = request.env._(
                "%(code)s is not a valid Italian fiscal code.", code=codice_fiscale
            )
            values["error"] = {"l10n_it_codice_fiscale"}
            return False
        return True

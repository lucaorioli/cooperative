# Copyright 2026 Luca Orioli <lucaorioli@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    l10n_it_coop_register_number = fields.Char(
        related="company_id.l10n_it_coop_register_number", readonly=False
    )
    l10n_it_coop_register_section = fields.Selection(
        related="company_id.l10n_it_coop_register_section", readonly=False
    )
    l10n_it_coop_register_category = fields.Selection(
        related="company_id.l10n_it_coop_register_category", readonly=False
    )
    l10n_it_social_coop_type = fields.Selection(
        related="company_id.l10n_it_social_coop_type", readonly=False
    )
    l10n_it_share_capital_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Share Capital Account",
        compute="_compute_l10n_it_share_capital_account_id",
        store=True,
        readonly=False,
        domain=[("account_type", "=", "equity")],
        help="Account of the share capital, set as the income account of the "
        "share category. Without it the shares are recorded on the default "
        "income account of the company.",
    )

    @api.model
    def _l10n_it_get_share_category(self, company):
        category = self.env.ref(
            "cooperator.product_category_company_share", raise_if_not_found=False
        )
        return category and category.with_company(company)

    @api.depends("company_id")
    def _compute_l10n_it_share_capital_account_id(self):
        for settings in self:
            company = settings.company_id
            category = self._l10n_it_get_share_category(company)
            account = category and category.property_account_income_categ_id
            # without a specific value the category shows the default income
            # account of the company, which is not a share capital account
            default_income = self.env["ir.default"]._get(
                "product.category",
                "property_account_income_categ_id",
                company_id=company.id,
            )
            if account and account.id == default_income:
                account = False
            settings.l10n_it_share_capital_account_id = account

    def set_values(self):
        result = super().set_values()
        category = self._l10n_it_get_share_category(self.company_id)
        if (
            category
            and category.property_account_income_categ_id
            != self.l10n_it_share_capital_account_id
        ):
            # an empty value restores the default income account
            category.property_account_income_categ_id = (
                self.l10n_it_share_capital_account_id
            )
        return result

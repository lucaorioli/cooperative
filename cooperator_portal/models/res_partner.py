# SPDX-FileCopyrightText: 2022 Coop IT Easy SC
# SPDX-FileCopyrightText: 2026 Luca Orioli <lucaorioli@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from odoo import models


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _get_frontend_writable_fields(self):
        return super()._get_frontend_writable_fields() | {
            "gender",
            "lang",
            "birthdate_date",
        }

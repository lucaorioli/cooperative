# SPDX-FileCopyrightText: 2026 Luca Orioli <lucaorioli@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later


def migrate(cr, version):
    # the thanks page used to inherit from the website contact us thanks page.
    # it is now a standalone template: remove the inheritance from the existing
    # view, otherwise its new arch would be applied as an inheritance spec.
    cr.execute(
        """
        UPDATE ir_ui_view view
        SET inherit_id = NULL, mode = 'primary'
        FROM ir_model_data imd
        WHERE imd.model = 'ir.ui.view'
            AND imd.res_id = view.id
            AND imd.module = 'cooperator_website'
            AND imd.name = 'cooperator_thanks'
        """
    )

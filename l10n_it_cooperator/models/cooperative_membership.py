# Copyright 2026 Luca Orioli <lucaorioli@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from .member_category import MEMBER_TYPES, TERMINATION_REASONS


class CooperativeMembership(models.Model):
    _inherit = "cooperative.membership"

    l10n_it_member_type = fields.Selection(
        MEMBER_TYPES,
        string="Member Type",
        help="Mutual relationship of the cooperator member with the "
        "cooperative. Volunteer members are allowed in social cooperatives "
        "only.",
    )
    l10n_it_special_category = fields.Boolean(
        string="Special Category",
        help="Member admitted to the special category of art. 2527 of the "
        "civil code (training or integration), for at most five years.",
    )
    l10n_it_special_category_end = fields.Date(
        string="Special Category Until",
    )
    l10n_it_admission_date = fields.Date(
        string="Admission Date",
        compute="_compute_l10n_it_admission_date",
        help="Date of the first subscription or transfer of shares to the "
        "member in the subscription register.",
    )
    l10n_it_termination_date = fields.Date(
        string="Termination Date",
        help="Date on which the member left the cooperative. Set when the "
        "member sells back or transfers all the shares.",
    )
    l10n_it_termination_reason = fields.Selection(
        TERMINATION_REASONS,
        string="Termination Reason",
    )
    l10n_it_encumbrances = fields.Text(
        string="Encumbrances",
        help="Pledges, usufructs and other encumbrances on the shares of the "
        "member, shown in the members register.",
    )

    @api.constrains("l10n_it_special_category", "l10n_it_special_category_end")
    def _check_l10n_it_special_category(self):
        for membership in self:
            if (
                membership.l10n_it_special_category
                and not membership.l10n_it_special_category_end
            ):
                raise ValidationError(
                    self.env._(
                        "Set the end date of the special category of %s.",
                        membership.partner_id.display_name,
                    )
                )

    @api.constrains("l10n_it_member_type", "member")
    def _check_l10n_it_volunteers(self):
        """Volunteer members only in social cooperatives, and at most half of
        the members (art. 2 of law 381/1991).
        """
        for company in self.filtered(
            lambda m: m.l10n_it_member_type == "volunteer"
        ).company_id:
            if not company.l10n_it_social_coop_type:
                raise ValidationError(
                    self.env._(
                        "Volunteer members are allowed in social cooperatives "
                        "only: set the type of social cooperative of %s.",
                        company.name,
                    )
                )
            members = self.search(
                [("company_id", "=", company.id), ("member", "=", True)]
            )
            volunteers = members.filtered(
                lambda m: m.l10n_it_member_type == "volunteer"
            )
            if len(volunteers) * 2 > len(members):
                raise ValidationError(
                    self.env._(
                        "The volunteer members cannot be more than half of the "
                        "members (%(volunteers)s volunteers out of "
                        "%(members)s members).",
                        volunteers=len(volunteers),
                        members=len(members),
                    )
                )

    def _l10n_it_register_operations(self):
        """Operations of the subscription register involving the member."""
        self.ensure_one()
        return self.env["subscription.register"].search(
            [
                ("company_id", "=", self.company_id.id),
                "|",
                ("partner_id", "=", self.partner_id.id),
                ("partner_id_to", "=", self.partner_id.id),
            ],
            order="date, register_number_operation",
        )

    @api.depends("partner_id", "company_id", "effective_date")
    def _compute_l10n_it_admission_date(self):
        for membership in self:
            if not membership.partner_id or not membership.id:
                membership.l10n_it_admission_date = membership.effective_date
                continue
            entries = membership._l10n_it_register_operations().filtered(
                lambda op, m=membership: (
                    op.type == "subscription" and op.partner_id == m.partner_id
                )
                or (op.type == "transfer" and op.partner_id_to == m.partner_id)
            )
            membership.l10n_it_admission_date = (
                min(entries.mapped("date")) if entries else membership.effective_date
            )

    def set_effective(self):
        # a member admitted again starts a new membership
        self.filtered("old_member").write(
            {"l10n_it_termination_date": False, "l10n_it_termination_reason": False}
        )
        return super().set_effective()

    @api.model
    def _l10n_it_share_categories(self):
        """Share categories with their translated labels."""
        field = self.env["product.template"]._fields["l10n_it_share_category"]
        return field._description_selection(self.env)

    def _l10n_it_register_lines(self, category):
        """Lines of the members register for the shares of `category`: one
        per operation, with the change of the number of shares of the member
        (positive for the shares received, negative for those given).
        """
        self.ensure_one()
        lines = []
        for op in self._l10n_it_register_operations():
            moves = []
            if op.type == "transfer" and op.partner_id_to == self.partner_id:
                moves.append((op.share_product_id, op.quantity, op.partner_id))
            elif op.partner_id == self.partner_id:
                if op.type == "subscription":
                    moves.append((op.share_product_id, op.quantity, False))
                elif op.type in ("transfer", "sell_back"):
                    moves.append((op.share_product_id, -op.quantity, op.partner_id_to))
                elif op.type == "convert":
                    moves.append((op.share_product_id, -op.quantity, False))
                    moves.append((op.share_to_product_id, op.quantity_to, False))
            label = self._l10n_it_operation_label(op)
            for product, quantity, counterpart in moves:
                if product.l10n_it_share_category != category:
                    continue
                unit_price = (
                    op.share_to_unit_price
                    if product == op.share_to_product_id and op.type == "convert"
                    else op.share_unit_price
                )
                lines.append(
                    {
                        "operation": op,
                        "label": label,
                        "product": product,
                        "quantity": quantity,
                        "amount": quantity * unit_price,
                        "counterpart": counterpart,
                    }
                )
        return lines

    def _l10n_it_operation_label(self, operation):
        self.ensure_one()
        if operation.type == "transfer":
            if operation.partner_id_to == self.partner_id:
                return self.env._(
                    "Transfer from %(partner)s",
                    partner=operation.partner_id.display_name,
                )
            return self.env._(
                "Transfer to %(partner)s", partner=operation.partner_id_to.display_name
            )
        field = operation._fields["type"]
        return dict(field._description_selection(self.env)).get(operation.type, "")

    def _l10n_it_register_holding(self, category):
        """Shares of `category` held by the member today."""
        self.ensure_one()
        shares = self.share_ids.filtered(
            lambda s: s.share_product_id.l10n_it_share_category == category
        )
        return {
            "quantity": sum(shares.mapped("share_number")),
            "amount": sum(shares.mapped("total_amount_line")),
        }

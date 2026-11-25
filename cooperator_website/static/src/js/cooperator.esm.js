// SPDX-FileCopyrightText: 2017 Open Architects Consulting SPRL
// SPDX-FileCopyrightText: 2018 Coop IT Easy SC
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import publicWidget from "@web/legacy/js/public/public_widget";
import {rpc} from "@web/core/network/rpc";

publicWidget.registry.CooperatorSubscriptionForm = publicWidget.Widget.extend({
    selector: ".oe_cooperator",
    events: {
        "change #share_product_id": "_onChangeShareProduct",
        "change #ordered_parts": "_onChangeOrderedParts",
    },

    start() {
        this.sharePrice = 0;
        this.minQty = 0;
        // Compute initial values.
        this._onChangeShareProduct();
        return this._super(...arguments);
    },

    async _onChangeShareProduct() {
        const shareProductInput = this.el.querySelector("#share_product_id");
        if (!shareProductInput || !shareProductInput.value) {
            return;
        }
        const shareProductId = shareProductInput.value;
        const data = await rpc("/subscription/get_share_product", {
            share_product_id: shareProductId,
        });
        const shareProduct = data[shareProductId];
        this.sharePrice = shareProduct.list_price;
        const suggestedQty = shareProduct.min_qty;
        this.minQty = shareProduct.force_min_qty ? suggestedQty : 1;
        const orderedParts = this.el.querySelector("#ordered_parts");
        orderedParts.setAttribute("min", this.minQty);
        if (Number(orderedParts.value) < suggestedQty) {
            orderedParts.value = suggestedQty;
        }
        // Update the share quantity and the total price.
        this._onChangeOrderedParts();
    },

    _onChangeOrderedParts() {
        const orderedParts = this.el.querySelector("#ordered_parts");
        let quantity = Number(orderedParts.value);
        if (quantity < this.minQty) {
            quantity = this.minQty;
            orderedParts.value = quantity;
        }
        const totalParts = this.el.querySelector('input[name="total_parts"]');
        if (totalParts) {
            totalParts.value = quantity * this.sharePrice;
        }
    },
});

export default publicWidget.registry.CooperatorSubscriptionForm;

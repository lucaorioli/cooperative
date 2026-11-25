// SPDX-FileCopyrightText: 2017 Open Architects Consulting SPRL
// SPDX-FileCopyrightText: 2018 Coop IT Easy SC
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import {Interaction} from "@web/public/interaction";
import {registry} from "@web/core/registry";

export class CooperatorSubscriptionForm extends Interaction {
    static selector = ".oe_cooperator";
    dynamicContent = {
        "#share_product_id": {"t-on-change": this.onChangeShareProduct},
        "#ordered_parts": {"t-on-change": this.onChangeOrderedParts},
    };

    setup() {
        this.sharePrice = 0;
        this.minQty = 0;
    }

    start() {
        // Compute initial values.
        this.onChangeShareProduct();
    }

    onChangeShareProduct() {
        const option = this.el.querySelector("#share_product_id")?.selectedOptions[0];
        const orderedParts = this.el.querySelector("#ordered_parts");
        if (!option || !orderedParts) {
            return;
        }
        this.sharePrice = Number(option.dataset.price) || 0;
        const suggestedQty = Number(option.dataset.minQty) || 1;
        this.minQty = option.dataset.forceMinQty === "1" ? suggestedQty : 1;
        orderedParts.setAttribute("min", this.minQty);
        if (Number(orderedParts.value) < suggestedQty) {
            orderedParts.value = suggestedQty;
        }
        // Update the share quantity and the total price.
        this.onChangeOrderedParts();
    }

    onChangeOrderedParts() {
        const orderedParts = this.el.querySelector("#ordered_parts");
        if (!orderedParts) {
            return;
        }
        let quantity = Number(orderedParts.value);
        if (quantity < this.minQty) {
            quantity = this.minQty;
            orderedParts.value = quantity;
        }
        const totalParts = this.el.querySelector('input[name="total_parts"]');
        if (totalParts) {
            totalParts.value = quantity * this.sharePrice;
        }
    }
}

registry
    .category("public.interactions")
    .add("cooperator_website.subscription_form", CooperatorSubscriptionForm);

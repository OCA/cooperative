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
        this._onChangeShareProduct();
        return this._super(...arguments);
    },

    async _onChangeShareProduct() {
        const select = this.el.querySelector("#share_product_id");
        if (!select || !select.value) {
            return;
        }
        const data = await rpc("/subscription/get_share_product", {
            share_product_id: select.value,
        });
        const info = data[select.value];
        if (!info) {
            return;
        }
        const price = this.el.querySelector("#share_price");
        const quantity = this.el.querySelector("#ordered_parts");
        if (price) {
            price.textContent = info.list_price;
        }
        if (quantity) {
            quantity.value = info.min_qty;
            if (info.force_min_qty === true) {
                quantity.dataset.min = info.min_qty;
            }
        }
        this._updateTotal();
    },

    _onChangeOrderedParts() {
        this._updateTotal();
    },

    _updateTotal() {
        const price = this.el.querySelector("#share_price");
        const quantity = this.el.querySelector("#ordered_parts");
        const total = this.el.querySelector('input[name="total_parts"]');
        if (!price || !quantity || !total) {
            return;
        }
        total.value = (quantity.value || 0) * (parseFloat(price.textContent) || 0);
    },
});

export default publicWidget.registry.CooperatorSubscriptionForm;

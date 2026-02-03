// SPDX-FileCopyrightText: 2017 Open Architects Consulting SPRL
// SPDX-FileCopyrightText: 2018 Coop IT Easy SC
//
// SPDX-License-Identifier: AGPL-3.0-or-later

odoo.define("cooperator.oe_cooperator", function (require) {
    "use strict";
    $(document).ready(function () {
        var ajax = require("web.ajax");

        $(".oe_cooperator").each(function () {
            var $oe_cooperator = $(this);
            var $share_product_id = $oe_cooperator.find("#share_product_id");
            var $ordered_parts = $oe_cooperator.find("#ordered_parts");
            var share_price = 0;
            var min_qty = 0;

            $share_product_id.on("change", function () {
                var share_product_id = $share_product_id.val();
                ajax.jsonRpc("/subscription/get_share_product", "call", {
                    share_product_id: share_product_id,
                }).then(function (data) {
                    var share_product = data[share_product_id];
                    share_price = share_product.list_price;
                    min_qty = share_product.min_qty;
                    var suggested_qty = min_qty;
                    if (!share_product.force_min_qty) {
                        min_qty = 1;
                    }
                    $ordered_parts.attr("min", min_qty);
                    if ($ordered_parts.val() < suggested_qty) {
                        $ordered_parts.val(suggested_qty);
                    }
                    // Update the share quantity and the total price by
                    // triggering the event which will call the function
                    // below.
                    $ordered_parts.trigger("change");
                });
            });

            $ordered_parts.on("change", function () {
                var quantity = $ordered_parts.val();
                if (quantity < min_qty) {
                    quantity = min_qty;
                    $ordered_parts.val(quantity);
                }
                $('input[name="total_parts"]').val(quantity * share_price);
            });

            // Compute initial values.
            $share_product_id.trigger("change");
        });
    });
});

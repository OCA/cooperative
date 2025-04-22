// SPDX-FileCopyrightText: 2017 Open Architects Consulting SPRL
// SPDX-FileCopyrightText: 2018 Coop IT Easy SC
//
// SPDX-License-Identifier: AGPL-3.0-or-later

// Define sin dependencias externas
odoo.define("cooperator.oe_cooperator", [], function () {
    "use strict";

    $(document).ready(function () {
        $(".oe_cooperator").each(function () {
            var oe_cooperator = this;

            $("#share_product_id").change(function () {
                var share_product_id = $("#share_product_id").val();

                // Usar jQuery.ajax directamente en lugar de web.rpc
                $.ajax({
                    url: "/subscription/get_share_product",
                    type: "POST",
                    dataType: "json",
                    contentType: "application/json",
                    data: JSON.stringify({
                        jsonrpc: "2.0",
                        method: "call",
                        params: {share_product_id: share_product_id},
                        id: Math.floor(Math.random() * 1000000),
                    }),
                    success: function (result) {
                        if (result.result) {
                            var data = result.result;
                            $("#share_price").text(data[share_product_id].list_price);
                            $("#ordered_parts").val(data[share_product_id].min_qty);
                            $("#ordered_parts_hidden").val(
                                data[share_product_id].min_qty
                            );
                            if (data[share_product_id].force_min_qty === true) {
                                $("#ordered_parts").data(
                                    "min",
                                    data[share_product_id].min_qty
                                );
                            }
                            $("#ordered_parts").change();
                            var $share_price = $("#share_price").text();
                            $('input[name="total_parts"]').val(
                                $("#ordered_parts").val() * $share_price
                            );
                            $('input[name="total_parts"]').change();
                        }
                    },
                });
            });

            $(oe_cooperator).on("change", "#ordered_parts", function (event) {
                var $share_price = $("#share_price").text();
                var $link = $(event.currentTarget);
                var quantity = $link[0].value;
                var total_part = quantity * $share_price;
                $("#total_parts").val(total_part);
                $("#ordered_parts_hidden").val(quantity);
                return false;
            });

            $(oe_cooperator).on("focusout", "input.js_quantity", function () {
                // Note: This selector might be specific to e-commerce contexts
                // and may not be relevant here unless adapted.
                // Keeping it as is for migration.
                $("a.js_add_cart_json").trigger("click");
            });

            // Asegurarse de actualizar ordered_parts_hidden antes de enviar el formulario
            $(".oe_subscription_request_form").on("submit", function () {
                $("#ordered_parts_hidden").val($("#ordered_parts").val());
                return true;
            });

            $("#share_product_id").trigger("change");
        });
    });
});

from odoo.http import request
from odoo.tools.translate import _

from odoo.addons.cooperator_website.controllers.main import WebsiteSubscription


class WebsiteSubscription(WebsiteSubscription):
    def get_values_from_user(self, values, is_company):
        values = super().get_values_from_user(values, is_company)
        if (
            request.env.user.login != "public"
            and request.env.company.get_display_national_number(is_company)
        ):
            values[
                "national_number"
            ] = request.env.user.partner_id.get_be_national_register_number()
        return values

    def fill_values(self, values, is_company, logged, load_from_user=False):
        values = super().fill_values(values, is_company, logged, load_from_user)
        values[
            "display_national_number"
        ] = request.env.company.get_display_national_number(is_company)
        values[
            "national_number_required"
        ] = request.env.company.get_require_national_number(is_company)
        return values

    def _additional_validate(self, kwargs, logged, values, post_file):
        result = super()._additional_validate(kwargs, logged, values, post_file)
        if result is not True:
            return result
        national_number = values.get("national_number")
        if national_number:
            valid = request.env["res.partner"].validate_be_national_register_number(
                values["national_number"]
            )
            if not valid:
                values["error_msg"] = (
                    _("%s is not a valid Belgian national registration number")
                    % values["national_number"]
                )
            else:
                return True
        else:
            is_company = kwargs.get("is_company") == "on"
            if not request.env.company.get_require_national_number(is_company):
                return True
            values["error_msg"] = _("Some mandatory fields have not been filled.")
        values["error"] = {"national_number"}
        return False

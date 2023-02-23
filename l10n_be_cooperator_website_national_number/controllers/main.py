from odoo.http import request
from odoo.addons.cooperator_website.controllers.main import WebsiteSubscription


class WebsiteSubscription(WebsiteSubscription):
    def get_values_from_user(self, values, is_company):
        values = super().get_values_from_user(values, is_company)
        if request.env.user.login != "public":
            partner = request.env.user.partner_id
            company = request.env["res.company"]._company_default_get()
            if not is_company and company.require_national_number:
                national_number_id_category = request.env.ref(
                    "l10n_be_national_number.l10n_be_national_number_category"
                ).id
                national_number = partner.id_numbers.filtered(
                    lambda id_num: id_num.category_id.id == national_number_id_category
                ).name
                values["national_number"] = national_number
        return values

    def fill_values(self, values, is_company, logged, load_from_user=False):
        values = super().fill_values(values, is_company, logged, load_from_user)
        sub_req_obj = request.env["subscription.request"]
        if not is_company and sub_req_obj._check_national_number_required():
            values["national_number_required"] = True
        return values

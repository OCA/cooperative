from odoo import http
from odoo.http import request
from odoo.tools.translate import _

from odoo.addons.cooperator_website.controllers.main import WebsiteSubscription


class WebsiteSubscriptionES(WebsiteSubscription):
    def _additional_validate(self, kwargs, logged, values, post_file):
        result = super()._additional_validate(kwargs, logged, values, post_file)
        if not result:
            return False

        is_company = kwargs.get("is_company") == "on"

        if is_company and not kwargs.get("vat"):
            values["error_msg"] = _("VAT number is mandatory for companies")
            values["error"] = {"vat"}
            return False

        return True

# Copyright 2017-2018 Coop IT Easy SC <remy@gcoopiteasy.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from werkzeug.exceptions import Forbidden

from odoo import http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.osv import expression

from odoo.addons.portal.controllers.portal import CustomerPortal


class TaxShelterPortal(CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if "tax_shelter_count" in counters:
            # sudo is needed because regular users don't have access to the
            # tax.shelter.certificate model, even for their own records.
            tax_shelter_count = (
                request.env["tax.shelter.certificate"]
                .sudo()
                .search_count(self._get_tax_shelter_certificates_domain())
            )
            values["tax_shelter_count"] = tax_shelter_count
        return values

    def _taxshelter_certificate_get_page_view_values(
        self, taxshelter_certificate, access_token, **kwargs
    ):
        values = {
            "company_id": request.env.company,
            "page_name": "taxshelter",
            "taxshelter": taxshelter_certificate,
        }
        return self._get_page_view_values(
            taxshelter_certificate,
            access_token,
            values,
            "my_taxshelter_certificates_history",
            False,
            **kwargs,
        )

    def _get_tax_shelter_certificates_domain(self):
        partner = request.env.user.partner_id
        return [("partner_id", "=", partner.commercial_partner_id.id)]

    @http.route(
        [
            "/my/tax_shelter_certificates",
        ],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_tax_shelter_certificates(self, **kw):
        """Render a page that lists the tax shelter reports:
        * Tax Shelter Certificates
        * Shares Certifcates
        """
        values = self._prepare_my_tax_shelter_certificates_values()
        tax_shelters = values["tax_shelters"]
        request.session["my_taxshelter_certificates_history"] = tax_shelters.ids
        return request.render("l10n_be_cooperator_portal.portal_my_tax_shelter", values)

    # this method is a copy of PortalAccount._prepare_my_invoices_values()
    # from the account module in odoo 16, with a few changes (most notably:
    # the pager has been removed). please update accordingly when porting to
    # newer versions.
    def _prepare_my_tax_shelter_certificates_values(
        self, domain=None, url="/my/tax_shelter_certificates"
    ):
        values = self._prepare_portal_layout_values()
        # sudo is needed because regular users don't have access to the
        # tax.shelter.certificate model, even for their own records.
        TaxShelterCertificate = request.env["tax.shelter.certificate"].sudo()

        domain = expression.AND(
            [
                domain or [],
                self._get_tax_shelter_certificates_domain(),
            ]
        )

        # sorting, filtering and pager support has been removed because:
        # * the number of records is very small
        # * the ordering cannot be computed by the database because it is
        #   computed with declaration_id.fiscal_year. database ordering only
        #   works with fields on the model itself.

        values.update(
            {
                "company_id": request.env.company,
                "tax_shelters": TaxShelterCertificate.search(domain).sorted(
                    key=lambda r: r.declaration_id.fiscal_year, reverse=True
                ),
                "page_name": "taxshelter",
                "default_url": url,
            }
        )
        return values

    @http.route(
        ["/my/tax_shelter_certificates/<int:certificate_id>"],
        type="http",
        auth="public",
        website=True,
    )
    def portal_my_tax_shelter_certificate_detail(
        self,
        certificate_id,
        access_token=None,
        report_type=None,
        download=False,
        query_string=None,
        **kw
    ):
        partner = request.env.user.partner_id
        try:
            taxshelter_certificate_sudo = self._document_check_access(
                "tax.shelter.certificate", certificate_id, access_token
            )
            if taxshelter_certificate_sudo.partner_id != partner.commercial_partner_id:
                raise Forbidden()
        except (AccessError, MissingError):
            return request.redirect("/my")

        if report_type in ("html", "pdf", "text") and query_string in (
            "subscription",
            "shares",
        ):
            report_ref = "l10n_be_cooperator.action_tax_shelter_%s_report" % (
                query_string
            )
            return self._show_report(
                model=taxshelter_certificate_sudo,
                report_type=report_type,
                report_ref=report_ref,
                download=download,
            )

        values = self._taxshelter_certificate_get_page_view_values(
            taxshelter_certificate_sudo, access_token, **kw
        )
        return request.render(
            "l10n_be_cooperator_portal.portal_taxshelter_page", values
        )

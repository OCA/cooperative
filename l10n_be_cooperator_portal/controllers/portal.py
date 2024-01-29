# SPDX-FileCopyrightText: 2018 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

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

    def _tax_shelter_certificate_get_page_view_values(
        self, tax_shelter_certificate, access_token, **kwargs
    ):
        values = {
            "company_id": request.env.company,
            "page_name": "tax_shelter_certificate",
            "tax_shelter_certificate": tax_shelter_certificate,
        }
        return self._get_page_view_values(
            tax_shelter_certificate,
            access_token,
            values,
            "my_tax_shelter_certificates_history",
            False,
            **kwargs,
        )

    def _get_tax_shelter_certificates_domain(self):
        partner = request.env.user.partner_id
        return [
            ("partner_id", "=", partner.commercial_partner_id.id),
            ("state", "in", ("validated", "sent")),
        ]

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
        tax_shelter_certificates = values["tax_shelter_certificates"]
        request.session[
            "my_tax_shelter_certificates_history"
        ] = tax_shelter_certificates.ids
        return request.render(
            "l10n_be_cooperator_portal.portal_my_tax_shelter_certificate", values
        )

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
                "tax_shelter_certificates": TaxShelterCertificate.search(domain).sorted(
                    key=lambda r: r.declaration_id.fiscal_year, reverse=True
                ),
                "page_name": "tax_shelter_certificate",
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
        certificate_type=None,
        **kw
    ):
        partner = request.env.user.partner_id
        try:
            tax_shelter_certificate_sudo = self._document_check_access(
                "tax.shelter.certificate", certificate_id, access_token
            )
            if tax_shelter_certificate_sudo.partner_id != partner.commercial_partner_id:
                raise Forbidden()
        except (AccessError, MissingError):
            return request.redirect("/my")

        if report_type in ("html", "pdf", "text") and certificate_type in (
            "subscription",
            "shares",
        ):
            report_ref = "l10n_be_cooperator.action_tax_shelter_%s_report" % (
                certificate_type
            )
            return self._show_report(
                model=tax_shelter_certificate_sudo,
                report_type=report_type,
                report_ref=report_ref,
                download=download,
            )

        values = self._tax_shelter_certificate_get_page_view_values(
            tax_shelter_certificate_sudo, access_token, **kw
        )
        return request.render(
            "l10n_be_cooperator_portal.portal_tax_shelter_page", values
        )

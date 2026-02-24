# SPDX-FileCopyrightText: 2025 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later


def migrate(cr, version):
    # Copy the company_type from the deprecated legal_form field and
    # use them to give the same company types from the partner_company_type
    # module. We're using the fact that the values of the legal_form selection
    # field are the same as the xml ids of the records in l10n_be_partner_company_type.
    # Make sure all the legal_forms have a corresponding id in the records.
    cr.execute(
        """
        UPDATE res_partner AS rp
        SET partner_company_type_id = imd.res_id
        FROM ir_model_data AS imd
        WHERE
            rp.legal_form_deprecated IS NOT NULL
            AND imd.model = 'res.partner.company.type'
            AND imd.module = 'l10n_be_partner_company_type'
            AND imd.name = rp.legal_form_deprecated
        """
    )

    # Same Operation for subscription_request
    cr.execute(
        """
        UPDATE subscription_request AS sr
        SET partner_company_type_id = imd.res_id
        FROM ir_model_data AS imd
        WHERE
            sr.company_type_deprecated IS NOT NULL
            AND imd.model = 'res.partner.company.type'
            AND imd.module = 'l10n_be_partner_company_type'
            AND imd.name = sr.company_type_deprecated
        """
    )

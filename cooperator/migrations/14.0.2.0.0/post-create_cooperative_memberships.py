# Copyright 2023 Coop IT Easy SC
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    cr.execute(
        """
        select id
        from res_company
        order by id
        """
    )
    company_rows = cr.fetchall()
    company_id = company_rows[0][0]
    if len(company_rows) > 1:
        _logger.warning(
            "Multiple companies found. "
            "All cooperators will be linked to the company with id {company_id}".format(
                company_id=company_id[0]
            )
        )
    cr.execute(
        """
        insert into cooperative_membership (
            company_id,
            partner_id,
            cooperator,
            member,
            coop_candidate,
            old_member,
            cooperator_register_number,
            cooperator_type,
            effective_date,
            data_policy_approved,
            internal_rules_approved,
            financial_risk_approved,
            generic_rules_approved
        )
        select
            %(company_id)s,
            rp.id,
            rp.cooperator,
            rp.member,
            rp.coop_candidate,
            rp.old_member,
            rp.cooperator_register_number,
            rp.cooperator_type,
            rp.effective_date,
            rp.data_policy_approved,
            rp.internal_rules_approved,
            rp.financial_risk_approved,
            rp.generic_rules_approved
        from res_partner as rp
        where
            rp.cooperator or
            rp.member or
            rp.coop_candidate or
            rp.old_member or
            rp.cooperator_register_number <> 0
        order by 2
        """,
        {"company_id": company_id},
    )

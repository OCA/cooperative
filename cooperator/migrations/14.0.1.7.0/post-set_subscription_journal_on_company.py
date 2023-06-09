# Copyright 2023 Coop IT Easy SC
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    # the subscription journal is now set on the company instead of using the
    # global cooperator.subscription_journal xml id.
    cr.execute(
        """
        select id, res_id
        from ir_model_data
        where
            module = 'cooperator' and
            name = 'subscription_journal'
        """
    )
    row = cr.fetchone()
    xml_id = row[0]
    journal_id = row[1]
    cr.execute(
        """
        select id
        from res_company
        order by id
        """
    )
    company_rows = cr.fetchall()
    company_ids = [row[0] for row in company_rows]
    if len(company_ids) > 1:
        _logger.warning(
            "Multiple companies found. "
            "Please set the subscription journal manually for companies with "
            "ids: {company_ids}".format(company_ids=company_ids[1:])
        )
    cr.execute(
        """
        update res_company
        set subscription_journal_id = %s
        where id = %s
        """,
        (journal_id, company_ids[0]),
    )
    cr.execute(
        """
        delete
        from ir_model_data
        where id = %s
        """,
        (xml_id,),
    )

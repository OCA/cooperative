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
        update res_company as rc
        set subscription_journal_id = aj.id
        from account_journal as aj
        where
            rc.subscription_journal_id is null and
            aj.company_id = rc.id and
            (aj.id = %s or aj.code = 'SUBJ')
        """,
        (journal_id,),
    )
    cr.execute(
        """
        select id
        from res_company
        where subscription_journal_id is null
        order by id
        """
    )
    company_rows = cr.fetchall()
    company_ids = [row[0] for row in company_rows]
    if company_ids:
        _logger.warning(
            "Could not find the subscription journal for companies with ids: "
            "{company_ids}. Please check and set it manually if needed.".format(
                company_ids=company_ids
            )
        )
    cr.execute(
        """
        delete
        from ir_model_data
        where id = %s
        """,
        (xml_id,),
    )

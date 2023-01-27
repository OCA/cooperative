# Copyright 2019 Coop IT Easy SCRL fs
#   Houssine Bakkali <houssine@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import fields, models, _


class AccountChartTemplate(models.Model):
    _inherit = "account.chart.template"

    def _prepare_all_journals(self, acc_template_ref, company, journals_dict=None):
        if journals_dict is None:
            journals_dict = []
        subscription_journal = {'name': _('Subscription Journal'), 'code': _('SUBJ'), 'type': 'sale', 'favorite': False,
                                'sequence': 10}
        journals_dict.append(subscription_journal)
        return super()._prepare_all_journals(acc_template_ref, company, journals_dict=journals_dict)

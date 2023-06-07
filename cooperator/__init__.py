from odoo import api, SUPERUSER_ID

from . import models
from . import report
from . import wizard


def post_init(cr, registry):
    # the subscription journal must be created for each company.
    env = api.Environment(cr, SUPERUSER_ID, {})
    subscription_request_model = env["subscription.request"]
    for company in env.companies:
        subscription_request_model.create_journal(company)

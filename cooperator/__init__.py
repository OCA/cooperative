from . import models
from . import report
from . import wizard

from odoo import api, SUPERUSER_ID


def _create_cooperator_sequences(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})

    companies = env["res.company"].search([])
    companies._create_cooperator_sequences()

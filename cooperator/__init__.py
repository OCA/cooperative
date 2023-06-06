from . import models
from . import report
from . import wizard

from odoo import api, SUPERUSER_ID


def _assign_default_mail_template_ids(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    companies = env["res.company"].search([])
    companies._setup_default_cooperator_mail_templates()

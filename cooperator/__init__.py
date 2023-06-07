from odoo import api, SUPERUSER_ID

from . import models
from . import report
from . import wizard


def post_init(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env.companies._init_cooperator_data()

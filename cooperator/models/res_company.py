# SPDX-FileCopyrightText: 2019 Coop IT Easy SC
# SPDX-FileContributor: Houssine Bakkali <houssine@coopiteasy.be>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from odoo import _, api, fields, models


class ResCompany(models.Model):
    _inherit = "res.company"
    _check_company_auto = True

    def _compute_base_logo(self):
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        self.logo_url = base_url + "/logo.png"

    coop_email_contact = fields.Char(string="Contact email address for the cooperator")
    subscription_maximum_amount = fields.Float(
        string="Maximum authorised subscription amount"
    )
    default_capital_release_request_payment_term = fields.Many2one(
        comodel_name="account.payment.term",
        string="Default Payment Term",
        help="Default payment term to use for capital release requests",
    )
    default_country_id = fields.Many2one(
        "res.country",
        string="Default country",
        default=lambda self: self.country_id,
    )
    default_lang_id = fields.Many2one("res.lang", string="Default lang")
    allow_id_card_upload = fields.Boolean(string="Allow ID Card upload")
    create_user = fields.Boolean(string="Create user for cooperator", default=False)
    board_representative = fields.Char(string="Board representative name")
    signature_scan = fields.Binary(string="Board representative signature")
    property_cooperator_account = fields.Many2one(
        comodel_name="account.account",
        string="Cooperator Account",
        domain=[
            ("account_type", "=", "asset_receivable"),
            ("deprecated", "=", False),
        ],
        help="This account will be"
        " the default one as the"
        " receivable account for the"
        " cooperators",
        check_company=True,
    )
    subscription_journal_id = fields.Many2one(
        "account.journal",
        "Subscription Journal",
        readonly=True,
        check_company=True,
    )
    unmix_share_type = fields.Boolean(
        string="Unmix share type",
        default=True,
        help="If checked, A cooperator will be"
        " authorised to have only one type"
        " of share",
    )
    display_logo1 = fields.Boolean(string="Display logo 1")
    display_logo2 = fields.Boolean(string="Display logo 2")
    bottom_logo1 = fields.Binary(string="Bottom logo 1")
    bottom_logo2 = fields.Binary(string="Bottom logo 2")
    logo_url = fields.Char(string="logo url", compute="_compute_base_logo")
    display_data_policy_approval = fields.Boolean(
        help="Choose to display a data policy checkbox on the cooperator"
        " website form."
    )
    data_policy_approval_required = fields.Boolean(
        string="Is data policy approval required?"
    )
    data_policy_approval_text = fields.Html(
        translate=True,
        help="Text to display aside the checkbox to approve data policy.",
    )
    display_internal_rules_approval = fields.Boolean(
        help="Choose to display an internal rules checkbox on the"
        " cooperator website form."
    )
    internal_rules_approval_required = fields.Boolean(
        string="Is internal rules approval required?"
    )
    internal_rules_approval_text = fields.Html(
        translate=True,
        help="Text to display aside the checkbox to approve internal rules.",
    )
    display_financial_risk_approval = fields.Boolean(
        help="Choose to display a financial risk checkbox on the"
        " cooperator website form."
    )
    financial_risk_approval_required = fields.Boolean(
        string="Is financial risk approval required?"
    )
    financial_risk_approval_text = fields.Html(
        translate=True,
        help="Text to display aside the checkbox to approve financial risk.",
    )
    display_generic_rules_approval = fields.Boolean(
        help="Choose to display generic rules checkbox on the"
        " cooperator website form."
    )
    generic_rules_approval_required = fields.Boolean(
        string="Is generic rules approval required?"
    )
    generic_rules_approval_text = fields.Html(
        translate=True,
        help="Text to display aside the checkbox to approve the generic rules.",
    )
    cooperator_certificate_mail_template = fields.Many2one(
        comodel_name="mail.template",
        string="Certificate email template",
        domain=[("model", "=", "res.partner"), ("is_cooperator_template", "=", True)],
        help="If left empty, the default global mail template will be used.",
    )
    cooperator_certificate_increase_mail_template = fields.Many2one(
        comodel_name="mail.template",
        string="Certificate increase email template",
        domain=[("model", "=", "res.partner"), ("is_cooperator_template", "=", True)],
        help="If left empty, the default global mail template will be used.",
    )
    send_certificate_email = fields.Boolean(
        string="Send certificate email", default=True
    )
    cooperator_confirmation_mail_template = fields.Many2one(
        comodel_name="mail.template",
        string="Share confirmation email template",
        domain=[
            ("model", "=", "subscription.request"),
            ("is_cooperator_template", "=", True),
        ],
        help="If left empty, the default global mail template will be used.",
    )
    send_confirmation_email = fields.Boolean(
        string="Send confirmation email", default=True
    )
    cooperator_capital_release_mail_template = fields.Many2one(
        comodel_name="mail.template",
        string="Capital release email template",
        domain=[("model", "=", "account.move"), ("is_cooperator_template", "=", True)],
        help="If left empty, the default global mail template will be used.",
    )
    send_capital_release_email = fields.Boolean(
        string="Send Capital Release email", default=True
    )
    cooperator_waiting_list_mail_template = fields.Many2one(
        comodel_name="mail.template",
        string="Waiting list email template",
        domain=[
            ("model", "=", "subscription.request"),
            ("is_cooperator_template", "=", True),
        ],
        help="If left empty, the default global mail template will be used.",
    )
    send_waiting_list_email = fields.Boolean(
        string="Send Waiting List email", default=True
    )
    cooperator_share_transfer_mail_template = fields.Many2one(
        comodel_name="mail.template",
        string="Share transfer email template",
        domain=[("model", "=", "res.partner"), ("is_cooperator_template", "=", True)],
        help="If left empty, the default global mail template will be used.",
    )
    cooperator_share_update_no_shares_mail_template = fields.Many2one(
        comodel_name="mail.template",
        string="Share transfer (no remaining shares) email template",
        domain=[("model", "=", "res.partner"), ("is_cooperator_template", "=", True)],
        help="If left empty, the default global mail template will be used.",
    )
    send_share_transfer_email = fields.Boolean(default=True)
    cooperator_share_update_mail_template = fields.Many2one(
        comodel_name="mail.template",
        string="Share update email template",
        domain=[("model", "=", "res.partner"), ("is_cooperator_template", "=", True)],
        help="If left empty, the default global mail template will be used.",
    )
    send_share_update_email = fields.Boolean(default=True)

    @api.onchange("data_policy_approval_required")
    def onchange_data_policy_approval_required(self):
        if self.data_policy_approval_required:
            self.display_data_policy_approval = True

    @api.onchange("internal_rules_approval_required")
    def onchange_internal_rules_approval_required(self):
        if self.internal_rules_approval_required:
            self.display_internal_rules_approval = True

    @api.onchange("financial_risk_approval_required")
    def onchange_financial_risk_approval_required(self):
        if self.financial_risk_approval_required:
            self.display_financial_risk_approval = True

    @api.onchange("generic_rules_approval_required")
    def onchange_generic_rules_approval_required(self):
        if self.generic_rules_approval_required:
            self.display_generic_rules_approval = True

    @api.model
    def _get_cooperator_mail_template_fields(self):
        return {
            "cooperator_confirmation_mail_template": "cooperator.email_template_confirmation",
            "cooperator_capital_release_mail_template": (
                "cooperator.email_template_release_capital"
            ),
            "cooperator_waiting_list_mail_template": "cooperator.email_template_waiting_list",
            "cooperator_certificate_mail_template": "cooperator.email_template_certificate",
            "cooperator_certificate_increase_mail_template": (
                "cooperator.email_template_share_increase"
            ),
            "cooperator_share_transfer_mail_template": (
                "cooperator.email_template_share_transfer"
            ),
            "cooperator_share_update_no_shares_mail_template": (
                "cooperator.email_template_share_update_no_shares"
            ),
            "cooperator_share_update_mail_template": "cooperator.email_template_share_update",
        }

    def _get_cooperator_template(self, name):
        self.ensure_one()
        template = getattr(self, name)
        if not template:
            return self.env.ref(self._get_cooperator_mail_template_fields()[name])
        return template

    def get_cooperator_certificate_mail_template(self):
        return self._get_cooperator_template("cooperator_certificate_mail_template")

    def get_cooperator_certificate_increase_mail_template(self):
        return self._get_cooperator_template(
            "cooperator_certificate_increase_mail_template"
        )

    def get_cooperator_confirmation_mail_template(self):
        return self._get_cooperator_template("cooperator_confirmation_mail_template")

    def get_cooperator_capital_release_mail_template(self):
        return self._get_cooperator_template("cooperator_capital_release_mail_template")

    def get_cooperator_waiting_list_mail_template(self):
        return self._get_cooperator_template("cooperator_waiting_list_mail_template")

    def get_cooperator_share_transfer_mail_template(self):
        return self._get_cooperator_template("cooperator_share_transfer_mail_template")

    def get_cooperator_share_update_no_shares_mail_template(self):
        return self._get_cooperator_template(
            "cooperator_share_update_no_shares_mail_template"
        )

    def get_cooperator_share_update_mail_template(self):
        return self._get_cooperator_template("cooperator_share_update_mail_template")

    def get_next_cooperator_number(self):
        self.ensure_one()
        return (
            self.env["ir.sequence"].with_company(self).next_by_code("cooperator.number")
        )

    def get_next_register_operation_number(self):
        self.ensure_one()
        return (
            self.env["ir.sequence"]
            .with_company(self)
            .next_by_code("register.operation")
        )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._create_cooperator_sequences()
        return records

    @api.model
    def _get_cooperator_sequence_map(self):
        return {
            "cooperator.number": _("Cooperator number sequence"),
            "register.operation": _("Cooperator register operation sequence"),
        }

    def _create_cooperator_sequences(self):
        for company in self:
            for code, name in self._get_cooperator_sequence_map().items():
                if not self.env["ir.sequence"].search(
                    [("code", "=", code), ("company_id", "=", company.id)]
                ):
                    self.env["ir.sequence"].create(
                        {
                            "name": name,
                            "code": code,
                            "company_id": company.id,
                        }
                    )

    def _accounting_data_initialized(self):
        return self.chart_template_id or self.env[
            "account.chart.template"
        ].existing_accounting(self)

    def _init_cooperator_data(self):
        """
        Generate default cooperator data for the company.
        """
        # this method exists to initialize data correctly for the following
        # possible cases:
        # 1. when a new company is created. in this case it will be called
        #    when the account chart template is loaded.
        # 2. when a database is initialized with the cooperator module but no
        #    l10n module, and the l10n_generic_coa module is loaded after the
        #    cooperator module by the post_init_hook of the account module. in
        #    this case it is first called by the xml data of this module
        #    (cooperator) (but with no effect, as explained below) and then
        #    again when the account chart template is loaded.
        # 3. when the cooperator module is installed on an existing database.
        #    in this case it is called by the xml data of this module.
        subscription_request_model = self.env["subscription.request"]
        for company in self:
            if not company._accounting_data_initialized():
                # if no account chart template has been loaded yet and no
                # accounting data exists, then no accounting data should be
                # created yet because all existing journals and accounts will
                # be deleted when the account chart template will be loaded.
                # this method will be called again after the account chart
                # template has been loaded.
                continue
            subscription_request_model.create_journal(company)
        # this is called here to support the first 2 cases explained above.
        self._init_cooperator_demo_data()

    def _init_cooperator_demo_data(self):
        if not self.env["ir.module.module"].search([("name", "=", "cooperator")]).demo:
            # demo data must not be loaded, nothing to do
            return
        account_account_model = self.env["account.account"]
        for company in self:
            if not company._accounting_data_initialized():
                # same remark as in _init_cooperator_data()
                continue
            if not company.property_cooperator_account:
                company.property_cooperator_account = account_account_model.create(
                    {
                        "code": "416101",
                        "name": "Cooperators",
                        "account_type": "asset_receivable",
                        "reconcile": True,
                        "company_id": company.id,
                    }
                )

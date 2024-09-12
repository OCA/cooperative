from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    coop_email_contact = fields.Char(
        related="company_id.coop_email_contact", readonly=False
    )
    subscription_maximum_amount = fields.Float(
        related="company_id.subscription_maximum_amount", readonly=False
    )
    # default_ is a special prefix, so I renamed putting default at the end
    capital_release_request_payment_term_default = fields.Many2one(
        related="company_id.default_capital_release_request_payment_term",
        readonly=False,
    )
    country_id_default = fields.Many2one(
        related="company_id.default_country_id", readonly=False
    )
    lang_id_default = fields.Many2one(
        related="company_id.default_lang_id", readonly=False
    )
    allow_id_card_upload = fields.Boolean(
        related="company_id.allow_id_card_upload", readonly=False
    )
    create_user = fields.Boolean(related="company_id.create_user", readonly=False)
    board_representative = fields.Char(
        related="company_id.board_representative", readonly=False
    )
    signature_scan = fields.Binary(related="company_id.signature_scan", readonly=False)
    property_cooperator_account = fields.Many2one(
        related="company_id.property_cooperator_account", readonly=False
    )
    subscription_journal_id = fields.Many2one(
        related="company_id.subscription_journal_id", readonly=False
    )
    unmix_share_type = fields.Boolean(
        related="company_id.unmix_share_type", readonly=False
    )
    display_logo1 = fields.Boolean(related="company_id.display_logo1", readonly=False)
    display_logo2 = fields.Boolean(related="company_id.display_logo2", readonly=False)
    bottom_logo1 = fields.Binary(related="company_id.bottom_logo1", readonly=False)
    bottom_logo2 = fields.Binary(related="company_id.bottom_logo2", readonly=False)
    logo_url = fields.Char(related="company_id.logo_url", readonly=False)
    display_data_policy_approval = fields.Boolean(
        related="company_id.display_data_policy_approval", readonly=False
    )
    data_policy_approval_required = fields.Boolean(
        related="company_id.data_policy_approval_required", readonly=False
    )
    data_policy_approval_text = fields.Html(
        related="company_id.data_policy_approval_text", readonly=False
    )
    display_internal_rules_approval = fields.Boolean(
        related="company_id.display_internal_rules_approval", readonly=False
    )
    internal_rules_approval_required = fields.Boolean(
        related="company_id.internal_rules_approval_required", readonly=False
    )
    internal_rules_approval_text = fields.Html(
        related="company_id.internal_rules_approval_text", readonly=False
    )
    display_financial_risk_approval = fields.Boolean(
        related="company_id.display_financial_risk_approval", readonly=False
    )
    financial_risk_approval_required = fields.Boolean(
        related="company_id.financial_risk_approval_required", readonly=False
    )
    financial_risk_approval_text = fields.Html(
        related="company_id.financial_risk_approval_text", readonly=False
    )
    display_generic_rules_approval = fields.Boolean(
        related="company_id.display_generic_rules_approval", readonly=False
    )
    generic_rules_approval_required = fields.Boolean(
        related="company_id.generic_rules_approval_required", readonly=False
    )
    generic_rules_approval_text = fields.Html(
        related="company_id.generic_rules_approval_text", readonly=False
    )
    cooperator_certificate_mail_template = fields.Many2one(
        related="company_id.cooperator_certificate_mail_template", readonly=False
    )
    cooperator_certificate_increase_mail_template = fields.Many2one(
        related="company_id.cooperator_certificate_increase_mail_template",
        readonly=False,
    )
    send_certificate_email = fields.Boolean(
        related="company_id.send_certificate_email", readonly=False
    )
    cooperator_confirmation_mail_template = fields.Many2one(
        related="company_id.cooperator_confirmation_mail_template", readonly=False
    )
    send_confirmation_email = fields.Boolean(
        related="company_id.send_confirmation_email", readonly=False
    )
    cooperator_capital_release_mail_template = fields.Many2one(
        related="company_id.cooperator_capital_release_mail_template", readonly=False
    )
    send_capital_release_email = fields.Boolean(
        related="company_id.send_capital_release_email", readonly=False
    )
    cooperator_waiting_list_mail_template = fields.Many2one(
        related="company_id.cooperator_waiting_list_mail_template", readonly=False
    )
    send_waiting_list_email = fields.Boolean(
        related="company_id.send_waiting_list_email", readonly=False
    )
    cooperator_share_transfer_mail_template = fields.Many2one(
        related="company_id.cooperator_share_transfer_mail_template", readonly=False
    )
    cooperator_share_update_no_shares_mail_template = fields.Many2one(
        related="company_id.cooperator_share_update_no_shares_mail_template",
        readonly=False,
    )
    send_share_transfer_email = fields.Boolean(
        related="company_id.send_share_transfer_email", readonly=False
    )
    cooperator_share_update_mail_template = fields.Many2one(
        related="company_id.cooperator_share_update_mail_template", readonly=False
    )
    send_share_update_email = fields.Boolean(
        related="company_id.send_share_update_email", readonly=False
    )

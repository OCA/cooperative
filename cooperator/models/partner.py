# Copyright 2019 Coop IT Easy SCRL fs
#   Houssine Bakkali <houssine@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from . import share_type


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _get_report_base_filename(self):
        self.ensure_one()
        if self.member:
            return "Cooperator Certificate - %s" % self.name
        else:
            return "unknown"

    @api.depends_context("company")
    def _get_share_type(self):
        return share_type.get_share_types(self.env)

    @api.depends_context("company")
    def _compute_cooperative_membership_id(self):
        company_id = self.env.company.id
        for record in self:
            record.cooperative_membership_id = record.get_cooperative_membership(
                company_id
            )

    def _search_cooperative_membership_id(self, operator, value):
        return [
            ("cooperative_membership_ids", operator, value),
            ("cooperative_membership_ids.company_id", "=", self.env.company.id),
        ]

    @api.depends_context("company")
    @api.depends(
        "parent_id.is_company",
        "parent_id.cooperative_membership_ids.member",
        "representative",
    )
    def _compute_representative_of_member_company(self):
        domain = self._search_representative_of_member_company("=", True) + [
            ("id", "in", self.ids)
        ]
        representatives = self.search(domain)
        for partner in self:
            partner.representative_of_member_company = partner in representatives

    def _search_representative_of_member_company(self, operator, value):
        # fixme: this only works correctly with "=", True and "!=", False
        return [
            ("representative", operator, value),
            ("parent_id.is_company", "=", True),
            (
                "parent_id.cooperative_membership_ids.company_id",
                "=",
                self.env.company.id,
            ),
            ("parent_id.cooperative_membership_ids.member", "=", True),
        ]

    cooperative_membership_ids = fields.One2many(
        "cooperative.membership",
        "partner_id",
        "Cooperative Memberships",
        readonly=True,
    )
    # the cooperative membership for the current company (company-dependent field)
    cooperative_membership_id = fields.Many2one(
        "cooperative.membership",
        "Cooperative Membership For Current Company",
        compute=_compute_cooperative_membership_id,
        search=_search_cooperative_membership_id,
    )
    share_ids = fields.One2many("share.line", "partner_id", string="Share Lines")
    company_register_number = fields.Char(string="Company Register Number")
    representative = fields.Boolean(string="Legal Representative")
    representative_of_member_company = fields.Boolean(
        string="Legal Representative of Member Company",
        compute=_compute_representative_of_member_company,
        search=_search_representative_of_member_company,
    )
    # allows for representative to have their own address
    # see https://github.com/coopiteasy/vertical-cooperative/issues/350
    type = fields.Selection(selection_add=[("representative", "Representative")])
    subscription_request_ids = fields.One2many(
        "subscription.request", "partner_id", string="Subscription request"
    )
    legal_form = fields.Selection([], string="Legal form")

    @api.onchange("parent_id")
    def onchange_parent_id(self):
        if len(self.parent_id) > 0:
            self.representative = True
        else:
            self.representative = False
        return super().onchange_parent_id()

    def has_representative(self):
        self.ensure_one()
        if self.child_ids.filtered("representative"):
            return True
        return False

    def get_representative(self):
        self.ensure_one()
        return self.child_ids.filtered("representative")

    def get_cooperator_from_email(self, email):
        if email:
            email = email.strip()
        # email could be falsy or be only made of whitespace.
        if not email:
            return self.browse()
        partner = self.search(
            [("cooperator", "=", True), ("email", "=", email)], limit=1
        )
        if not partner:
            partner = self.search([("email", "=", email)], limit=1)
        return partner

    def get_cooperator_from_crn(self, company_register_number):
        if company_register_number:
            company_register_number = company_register_number.strip()
        # company_register_number could be falsy or be only made of whitespace.
        if not company_register_number:
            return self.browse()
        partner = self.search(
            [
                ("cooperator", "=", True),
                ("company_register_number", "=", company_register_number),
            ],
            limit=1,
        )
        if not partner:
            partner = self.search(
                [("company_register_number", "=", company_register_number)], limit=1
            )
        return partner

    def get_cooperative_membership(self, company_id):
        self.ensure_one()
        return self.env["cooperative.membership"].search(
            [
                ("company_id", "=", company_id),
                ("partner_id", "=", self.id),
            ]
        )

    def create_cooperative_membership(self, company_id):
        cooperative_membership_model = self.env["cooperative.membership"]
        result = cooperative_membership_model.browse()
        for record in self:
            result |= cooperative_membership_model.create(
                {
                    "company_id": company_id,
                    "partner_id": record.id,
                    "cooperator": True,
                }
            )
        return result


# many fields that were previously defined directly on res.partner are now
# defined on cooperative.membership to allow to have different values per
# company. for backward compatibility, the fields are still available on
# res.partner and their value is company-dependent, meaning that their value
# changes depending on which company is the current company
# (self.env.company). to make this work, 3 methods are needed per field: a
# company-dependent compute method, a set method and a search method. instead
# of copying the same 3 methods for each of the fields, the following function
# allows to define a field and its methods on the class.


def add_company_dependent_related_field(
    model_class, delegate, name, field_type, **kwargs
):
    delegate_field_name = ".".join([delegate, name])

    def _compute(self):
        for record in self:
            setattr(record, name, getattr(getattr(record, delegate), name))

    def _set(self):
        for record in self:
            delegate_record = getattr(record, delegate)
            if not delegate_record:
                raise ValidationError(
                    _(
                        "Cannot set {name} field on {record}: {delegate} is not set"
                    ).format(name=name, record=record, delegate=delegate)
                )
            setattr(delegate_record, name, getattr(record, name))

    def _search(self, operator, value):
        return [(delegate_field_name, operator, value)]

    setattr(
        model_class,
        name,
        field_type(
            **kwargs,
            compute=api.depends_context("company")(
                api.depends(delegate_field_name)(_compute)
            ),
            inverse=_set,
            search=_search,
        ),
    )


def add_cooperative_membership_field(name, field_type, **kwargs):
    add_company_dependent_related_field(
        ResPartner, "cooperative_membership_id", name, field_type, **kwargs
    )


add_cooperative_membership_field(
    "cooperator",
    fields.Boolean,
    string="Cooperator",
    help="Check this box if this contact is a cooperator (effective or not).",
)
add_cooperative_membership_field(
    "member",
    fields.Boolean,
    string="Effective cooperator",
    help="Check this box if this cooperator is an effective member.",
    readonly=True,
)
add_cooperative_membership_field(
    "coop_candidate",
    fields.Boolean,
    string="Cooperator candidate",
    readonly=True,
)
add_cooperative_membership_field(
    "old_member",
    fields.Boolean,
    string="Old cooperator",
    help="Check this box if this cooperator is no more an effective member.",
)
add_cooperative_membership_field(
    "cooperator_register_number",
    fields.Integer,
    string="Cooperator Number",
    readonly=True,
)
add_cooperative_membership_field(
    "number_of_share",
    fields.Integer,
    string="Number of share",
    readonly=True,
)
add_cooperative_membership_field(
    "total_value",
    fields.Float,
    string="Total value of shares",
    readonly=True,
)
add_cooperative_membership_field(
    "cooperator_type",
    fields.Selection,
    selection=ResPartner._get_share_type,
    string="Cooperator Type",
    readonly=True,
)
add_cooperative_membership_field(
    "effective_date",
    fields.Date,
    string="Effective Date",
    readonly=True,
)
add_cooperative_membership_field(
    "data_policy_approved",
    fields.Boolean,
    string="Approved Data Policy",
)
add_cooperative_membership_field(
    "internal_rules_approved",
    fields.Boolean,
    string="Approved Internal Rules",
)
add_cooperative_membership_field(
    "financial_risk_approved",
    fields.Boolean,
    string="Approved Financial Risk",
)
add_cooperative_membership_field(
    "generic_rules_approved",
    fields.Boolean,
    string="Approved generic rules",
)

# Copyright 2026 PopSolutions
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from erpbrasil.base.fiscal import cnpj_cpf

from odoo import api, fields, models

from odoo.addons.l10n_br_base.tools import check_cnpj_cpf


class SubscriptionRequest(models.Model):
    _inherit = "subscription.request"

    vat = fields.Char(
        string="CPF/CNPJ",
        help="CPF para pessoa fisica, CNPJ para pessoa juridica. "
        "Usado para identificar o cooperado e evitar cadastro duplicado.",
    )

    legal_name = fields.Char(
        string="Razao Social",
        help="Razao social registrada na Receita Federal. "
        "Apenas para pessoa juridica.",
    )

    @api.constrains("vat", "country_id")
    def _check_vat_cnpj_cpf(self):
        """Reusa o validador oficial do l10n_br_base.

        Ele respeita o parametro l10n_br_base.disable_cpf_cnpj_validation e
        so valida quando o pais e o Brasil, entao cooperados estrangeiros
        continuam funcionando.
        """
        for request in self:
            check_cnpj_cpf(request.env, request.vat, request.country_id)

    @api.onchange("vat")
    def _onchange_vat_format(self):
        """Aplica a mascara (000.000.000-00 / 00.000.000/0000-00)."""
        if self.vat:
            self.vat = cnpj_cpf.formata(str(self.vat))

    @api.model_create_multi
    def create(self, vals_list):
        """No Brasil o CNPJ E o registro da empresa.

        O cooperator usa company_register_number na criacao e para casar o
        parceiro PJ; deixa-lo vazio quebra a renderizacao do e-mail de
        confirmacao. Preenche a partir do CPF/CNPJ em vez de ocultar o campo.
        """
        for vals in vals_list:
            if (
                vals.get("is_company")
                and vals.get("vat")
                and not vals.get("company_register_number")
            ):
                vals["company_register_number"] = vals["vat"]
        return super().create(vals_list)

    @api.onchange("vat", "is_company")
    def _onchange_vat_company_register(self):
        if self.is_company and self.vat:
            self.company_register_number = self.vat

    def get_partner_vals(self):
        vals = super().get_partner_vals()
        vals["vat"] = self.vat
        if self.is_company and self.legal_name:
            vals["legal_name"] = self.legal_name
        return vals

    def get_required_field(self):
        required_fields = super().get_required_field()[:]
        if "vat" not in required_fields:
            required_fields.append("vat")
        # O Brasil nao usa IBAN; sem esta remocao o formulario publico
        # ficaria insubmetivel, pois o cooperator exige iban mas o form
        # base tem apenas um container vazio para localizacoes.
        if "iban" in required_fields:
            required_fields.remove("iban")
        return required_fields

    def _get_partner_domain(self):
        """Casa o contato pelo CPF/CNPJ, que no Brasil e o identificador real.

        Cai no comportamento padrao (email) quando nao ha documento.
        """
        if self.vat:
            return [("vat", "=", self.vat)]
        return super()._get_partner_domain()

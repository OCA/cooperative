# Copyright 2026 PopSolutions
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase

CPF_VALIDO = "529.982.240-59"
CPF_INVALIDO = "111.111.111-11"
CNPJ_VALIDO = "55.087.795/0001-09"
CNPJ_INVALIDO = "55.087.795/0001-00"


class TestSubscriptionRequestBr(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.br = cls.env.ref("base.br")
        cls.share = cls.env["product.product"].create(
            {
                "name": "Cota Teste",
                "short_name": "Cota",
                "is_share": True,
                "default_share_product": True,
                "by_individual": True,
                "by_company": True,
                "list_price": 100,
            }
        )

    def _make(self, **kw):
        vals = {
            "name": "Fulano de Tal",
            "firstname": "Fulano",
            "lastname": "de Tal",
            "email": "fulano@example.org",
            "address": "Rua Um, 100",
            "zip_code": "01310-100",
            "city": "Sao Paulo",
            "country_id": self.br.id,
            "share_product_id": self.share.id,
            "ordered_parts": 1,
            "lang": "en_US",
        }
        vals.update(kw)
        return self.env["subscription.request"].create(vals)

    def _make_pj(self, **kw):
        vals = {
            "is_company": True,
            "company_name": "Empresa Exemplo Ltda",
            # obrigatorio no formulario publico; sem ele o template de
            # e-mail do cooperator quebra (bug upstream)
            "company_email": "contato@example.org",
            "vat": CNPJ_VALIDO,
        }
        vals.update(kw)
        return self._make(**vals)

    # --- validacao -------------------------------------------------
    def test_cpf_valido_e_aceito(self):
        self.assertEqual(self._make(vat=CPF_VALIDO).vat, CPF_VALIDO)

    def test_cpf_invalido_e_rejeitado(self):
        with self.assertRaises(ValidationError):
            self._make(vat=CPF_INVALIDO)

    def test_cnpj_valido_e_aceito(self):
        self.assertEqual(self._make_pj().vat, CNPJ_VALIDO)

    def test_cnpj_invalido_e_rejeitado(self):
        with self.assertRaises(ValidationError):
            self._make_pj(vat=CNPJ_INVALIDO)

    def test_estrangeiro_nao_e_validado_como_cpf(self):
        pt = self.env.ref("base.pt")
        self.assertEqual(self._make(country_id=pt.id, vat="999999").vat, "999999")

    def test_validacao_pode_ser_desligada_por_parametro(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "l10n_br_base.disable_cpf_cnpj_validation", "1"
        )
        self.assertEqual(self._make(vat=CPF_INVALIDO).vat, CPF_INVALIDO)

    def test_sem_documento_nao_valida(self):
        self.assertFalse(self._make().vat)

    # --- mascara / onchange ----------------------------------------
    def test_onchange_aplica_mascara_no_cpf(self):
        req = self._make()
        req.vat = "52998224059"
        req._onchange_vat_format()
        self.assertEqual(req.vat, CPF_VALIDO)

    def test_onchange_aplica_mascara_no_cnpj(self):
        req = self._make()
        req.vat = "55087795000109"
        req._onchange_vat_format()
        self.assertEqual(req.vat, CNPJ_VALIDO)

    def test_onchange_sem_documento_nao_falha(self):
        req = self._make()
        req.vat = False
        req._onchange_vat_format()
        self.assertFalse(req.vat)

    def test_onchange_preenche_registro_da_empresa(self):
        req = self._make_pj(company_register_number=False)
        req.is_company = True
        req.vat = CNPJ_VALIDO
        req._onchange_vat_company_register()
        self.assertEqual(req.company_register_number, CNPJ_VALIDO)

    def test_onchange_registro_nao_mexe_em_pessoa_fisica(self):
        req = self._make(vat=CPF_VALIDO)
        req._onchange_vat_company_register()
        self.assertFalse(req.company_register_number)

    # --- create ----------------------------------------------------
    def test_create_pj_preenche_registro_com_o_cnpj(self):
        self.assertEqual(self._make_pj().company_register_number, CNPJ_VALIDO)

    def test_create_pj_respeita_registro_ja_informado(self):
        req = self._make_pj(company_register_number="registro-manual")
        self.assertEqual(req.company_register_number, "registro-manual")

    def test_create_pf_nao_preenche_registro(self):
        self.assertFalse(self._make(vat=CPF_VALIDO).company_register_number)

    # --- integracao com o cooperator -------------------------------
    def test_vat_entra_como_obrigatorio(self):
        self.assertIn("vat", self._make(vat=CPF_VALIDO).get_required_field())

    def test_iban_nao_e_obrigatorio_no_brasil(self):
        req = self._make(vat=CPF_VALIDO)
        self.assertNotIn("iban", req.get_required_field())

    def test_vat_nao_e_duplicado_na_lista_de_obrigatorios(self):
        req = self._make(vat=CPF_VALIDO)
        self.assertEqual(req.get_required_field().count("vat"), 1)

    def test_vat_propaga_para_o_parceiro(self):
        req = self._make(vat=CPF_VALIDO)
        self.assertEqual(req.get_partner_vals()["vat"], CPF_VALIDO)

    def test_razao_social_propaga_apenas_para_pj(self):
        pj = self._make_pj(legal_name="Empresa Exemplo Ltda")
        self.assertEqual(pj.get_partner_vals()["legal_name"], "Empresa Exemplo Ltda")

    def test_razao_social_nao_propaga_para_pessoa_fisica(self):
        pf = self._make(vat=CPF_VALIDO, legal_name="Ignorada")
        self.assertNotIn("legal_name", pf.get_partner_vals())

    def test_parceiro_e_casado_pelo_documento(self):
        req = self._make(vat=CPF_VALIDO)
        self.assertEqual(req._get_partner_domain(), [("vat", "=", CPF_VALIDO)])

    def test_sem_documento_cai_no_padrao_por_email(self):
        req = self._make()
        self.assertEqual(
            req._get_partner_domain(), [("email", "=", "fulano@example.org")]
        )

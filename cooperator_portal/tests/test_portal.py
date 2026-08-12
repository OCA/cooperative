# SPDX-FileCopyrightText: 2026 PopSolutions
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import json
import re

from odoo.tests.common import HttpCase, TransactionCase, tagged

from odoo.addons.cooperator.tests.cooperator_test_mixin import CooperatorTestMixin

CSRF_RE = re.compile(r'name="csrf_token"\s+value="([^"]+)"')
PORTAL_PASSWORD = "portal_test_password"

FORM_FIELD_RE = re.compile(r'<(?:input|select|textarea)[^>]*\sname="([a-zA-Z_]+)"')


def _form_payload(case, csrf_token, values, overrides):
    """Build a /my/account payload from the fields the form really has.

    Extra keys are rejected by the portal details validation, and the
    field set depends on which modules extend the form, so only send
    values for inputs present in the rendered page.
    """
    page = case.url_open("/my/account")
    fields = set(FORM_FIELD_RE.findall(page.text))
    payload = {k: v for k, v in values.items() if k in fields}
    payload["csrf_token"] = csrf_token
    payload.update(overrides)
    return payload


class TestCooperatorPortalModels(TransactionCase, CooperatorTestMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.set_up_cooperator_test_data()
        cls.cooperator = cls.create_dummy_cooperator()

    def test_capital_release_access_url(self):
        invoice = self.env["account.move"].search(
            [
                ("partner_id", "=", self.cooperator.id),
                ("release_capital_request", "=", True),
            ],
            limit=1,
        )
        invoice._compute_access_url()
        self.assertEqual(
            invoice.access_url,
            f"/my/capital_release_requests/{invoice.id}",
        )

    def test_regular_invoice_keeps_default_access_url(self):
        invoice = self.env["account.move"].create(
            {"move_type": "out_invoice", "partner_id": self.cooperator.id}
        )
        invoice._compute_access_url()
        self.assertEqual(invoice.access_url, f"/my/invoices/{invoice.id}")

    def test_partner_write_drops_iban_key(self):
        # upstream portal writes the whole form dict to res.partner;
        # the iban key must be silently dropped
        self.cooperator.write({"iban": "BE71096123456769", "city": "Namur"})
        self.assertEqual(self.cooperator.city, "Namur")


@tagged("post_install", "-at_install")
class TestCooperatorPortalHttp(HttpCase, CooperatorTestMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.set_up_cooperator_test_data()
        cls.cooperator = cls.create_dummy_cooperator()
        cls.portal_user = (
            cls.env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "login": "portal.coop@example.org",
                    "password": PORTAL_PASSWORD,
                    "partner_id": cls.cooperator.id,
                    "groups_id": [(6, 0, [cls.env.ref("base.group_portal").id])],
                }
            )
        )
        cls.capital_release = cls.env["account.move"].search(
            [
                ("partner_id", "=", cls.cooperator.id),
                ("release_capital_request", "=", True),
            ],
            limit=1,
        )

    def _login(self):
        self.authenticate("portal.coop@example.org", PORTAL_PASSWORD)

    def test_home_shows_capital_release_requests(self):
        self._login()
        response = self.url_open("/my/home")
        self.assertEqual(response.status_code, 200)
        self.assertIn("/my/capital_release_requests", response.text)

    def test_capital_release_requests_list(self):
        self._login()
        response = self.url_open("/my/capital_release_requests")
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.capital_release.name, response.text)

    def test_capital_release_request_detail(self):
        self._login()
        response = self.url_open(
            f"/my/capital_release_requests/{self.capital_release.id}"
        )
        self.assertEqual(response.status_code, 200)

    def test_capital_release_report_download(self):
        self._login()
        response = self.url_open(
            f"/my/capital_release_requests/{self.capital_release.id}?report_type=pdf&download=true"
        )
        self.assertEqual(response.status_code, 200)

    def test_invoices_exclude_capital_releases(self):
        self._login()
        response = self.url_open("/my/invoices")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(self.capital_release.name, response.text)

    def test_account_page_shows_cooperator_fields(self):
        self._login()
        response = self.url_open("/my/account")
        self.assertEqual(response.status_code, 200)
        self.assertIn('name="iban"', response.text)

    def _account_payload(self, csrf_token, **overrides):
        partner = self.cooperator
        values = {
            "name": partner.name,
            "firstname": partner.firstname or "First",
            "lastname": partner.lastname or "Last",
            "phone": partner.phone or "+32 471 22 22 22",
            "email": partner.email,
            "street": partner.street or "Rue Test 1",
            "city": partner.city or "Brussels",
            "zipcode": partner.zip or "1000",
            "country_id": str(partner.country_id.id),
            "iban": "BE71096123456769",
            "birthdate_date": "1985-05-05",
            "gender": "female",
            "lang": "en_US",
        }
        return _form_payload(self, csrf_token, values, overrides)

    def test_account_update_writes_iban(self):
        self._login()
        page = self.url_open("/my/account")
        csrf_token = CSRF_RE.search(page.text).group(1)
        response = self.url_open("/my/account", data=self._account_payload(csrf_token))
        self.assertEqual(response.status_code, 200)
        bank = self.cooperator.bank_ids[0]
        self.assertEqual(bank.sanitized_acc_number.replace(" ", ""), "BE71096123456769")

    def test_account_invalid_iban_shows_error(self):
        self._login()
        page = self.url_open("/my/account")
        csrf_token = CSRF_RE.search(page.text).group(1)
        response = self.url_open(
            "/my/account",
            data=self._account_payload(csrf_token, iban="XX0000"),
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("not valid", response.text)


@tagged("post_install", "-at_install")
class TestCooperatorPortalExtra(HttpCase, CooperatorTestMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.set_up_cooperator_test_data()
        cls.cooperator = cls.create_dummy_cooperator()
        cls.portal_user = (
            cls.env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "login": "portal.extra@example.org",
                    "password": PORTAL_PASSWORD,
                    "partner_id": cls.cooperator.id,
                    "groups_id": [(6, 0, [cls.env.ref("base.group_portal").id])],
                }
            )
        )

    def _login(self):
        self.authenticate("portal.extra@example.org", PORTAL_PASSWORD)

    def test_home_counters_include_capital_releases(self):
        self._login()
        response = self.url_open(
            "/my/counters",
            data=json.dumps(
                {"params": {"counters": ["capital_release_request_count"]}}
            ),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 200)
        result = response.json()["result"]
        self.assertEqual(result["capital_release_request_count"], 1)

    def test_regular_invoice_detail_uses_default_values(self):
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.cooperator.id,
                "invoice_line_ids": [
                    (0, 0, {"name": "line", "quantity": 1, "price_unit": 10})
                ],
            }
        )
        invoice.action_post()
        self._login()
        response = self.url_open(f"/my/invoices/{invoice.id}")
        self.assertEqual(response.status_code, 200)

    def test_account_update_creates_bank_when_missing(self):
        self._login()
        self.cooperator.bank_ids.unlink()
        page = self.url_open("/my/account")
        csrf_token = CSRF_RE.search(page.text).group(1)
        values = {
            "name": self.cooperator.name,
            "firstname": self.cooperator.firstname or "First",
            "lastname": self.cooperator.lastname or "Last",
            "phone": "+32 471 44 44 44",
            "email": self.cooperator.email,
            "street": "Rue Nouvelle 2",
            "city": "Liege",
            "zipcode": self.cooperator.zip or "1000",
            "country_id": str(self.cooperator.country_id.id),
            "iban": "BE71096123456769",
            "birthdate_date": "1980-01-01",
            "gender": "other",
            "lang": "en_US",
        }
        payload = _form_payload(self, csrf_token, values, {})
        response = self.url_open("/my/account", data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.cooperator.bank_ids)

    def test_cooperator_certificate_download(self):
        self._login()
        response = self.url_open("/my/cooperator_certificate/pdf")
        self.assertEqual(response.status_code, 200)

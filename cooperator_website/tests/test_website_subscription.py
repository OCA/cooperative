# SPDX-FileCopyrightText: 2026 PopSolutions
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import json
import re
from unittest.mock import patch

from odoo.tests.common import HttpCase, tagged

from odoo.addons.cooperator.tests.cooperator_test_mixin import CooperatorTestMixin

CSRF_RE = re.compile(r'name="csrf_token"\s+value="([^"]+)"')


@tagged("post_install", "-at_install")
class TestWebsiteSubscription(HttpCase, CooperatorTestMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.set_up_cooperator_test_data()
        cls.website = cls.env["website"].get_current_website()
        cls.website.company_id = cls.company

    def _get_csrf_token(self, page="/become_cooperator"):
        response = self.url_open(page)
        self.assertEqual(response.status_code, 200)
        match = CSRF_RE.search(response.text)
        self.assertTrue(match, "csrf token not found in form page")
        return match.group(1)

    def _subscription_payload(self, csrf_token, **overrides):
        share_template = self.share_y.product_tmpl_id
        payload = {
            "csrf_token": csrf_token,
            "firstname": "Web",
            "lastname": "Visitor",
            "email": "web.visitor@example.org",
            "confirm_email": "web.visitor@example.org",
            "birthdate": "1990-01-01",
            "gender": "male",
            "phone": "+32 471 11 11 11",
            "iban": "BE71096123456769",
            "address": "Rue du Web 1",
            "zip_code": "1000",
            "city": "Brussels",
            "country_id": str(self.env.ref("base.be").id),
            "lang": "en_US",
            "share_product_id": str(share_template.id),
            "ordered_parts": "2",
            "total_parts": str(2 * self.share_y.list_price),
            "data_policy_approved": "on",
            "internal_rules_approved": "on",
            "financial_risk_approved": "on",
            "generic_rules_approved": "on",
        }
        # localization modules (e.g. l10n_br_cooperator) may add their
        # own required fields; keep the payload valid either way
        required = self.env["subscription.request"].sudo().get_required_field()
        if "vat" in required:
            payload["vat"] = "529.982.240-59"
        payload.update(overrides)
        return payload

    def _post_subscription(self, payload):
        return self.url_open("/subscription/subscribe_share", data=payload)

    # --- page rendering -------------------------------------------

    def test_become_cooperator_page_renders(self):
        response = self.url_open("/become_cooperator")
        self.assertEqual(response.status_code, 200)
        self.assertIn('name="firstname"', response.text)
        self.assertIn('name="ordered_parts"', response.text)

    def test_become_company_cooperator_page_renders(self):
        response = self.url_open("/become_company_cooperator")
        self.assertEqual(response.status_code, 200)
        self.assertIn('name="company_name"', response.text)

    def test_page_prefills_submitted_values(self):
        response = self.url_open("/become_cooperator?firstname=Prefilled")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Prefilled", response.text)

    # --- json helper route ----------------------------------------

    def test_get_share_product_returns_price_info(self):
        share_template = self.share_y.product_tmpl_id
        response = self.url_open(
            "/subscription/get_share_product",
            data=json.dumps({"params": {"share_product_id": share_template.id}}),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 200)
        result = response.json()["result"]
        self.assertEqual(
            result[str(share_template.id)]["list_price"],
            self.share_y.list_price,
        )

    # --- subscription flow ----------------------------------------

    def test_subscribe_share_individual(self):
        csrf_token = self._get_csrf_token()
        response = self._post_subscription(self._subscription_payload(csrf_token))
        self.assertEqual(response.status_code, 200)
        self.assertIn("successfully", response.text)

        request = self.env["subscription.request"].search(
            [("email", "=", "web.visitor@example.org")]
        )
        self.assertEqual(len(request), 1)
        self.assertEqual(request.source, "website")
        self.assertEqual(request.ordered_parts, 2)
        self.assertFalse(request.is_company)

    def test_subscribe_share_company(self):
        csrf_token = self._get_csrf_token("/become_company_cooperator")
        payload = self._subscription_payload(
            csrf_token,
            is_company="on",
            company_name="Web Company",
            company_email="web.company@example.org",
            confirm_email="web.company@example.org",
            company_register_number="0123.456.789",
            contact_person_function="CEO",
        )
        response = self._post_subscription(payload)
        self.assertEqual(response.status_code, 200)
        self.assertIn("successfully", response.text)

        request = self.env["subscription.request"].search(
            [("company_email", "=", "web.company@example.org")]
        )
        self.assertEqual(len(request), 1)
        self.assertTrue(request.is_company)
        # punctuation is stripped from the register number
        self.assertEqual(request.company_register_number, "0123456789")

    # --- validation error paths -----------------------------------

    def test_subscribe_missing_required_field(self):
        csrf_token = self._get_csrf_token()
        payload = self._subscription_payload(csrf_token, city="")
        response = self._post_subscription(payload)
        self.assertEqual(response.status_code, 200)
        self.assertIn("mandatory fields", response.text)
        self.assertFalse(
            self.env["subscription.request"].search(
                [("email", "=", "web.visitor@example.org")]
            )
        )

    def test_subscribe_email_mismatch(self):
        csrf_token = self._get_csrf_token()
        payload = self._subscription_payload(
            csrf_token, confirm_email="other@example.org"
        )
        response = self._post_subscription(payload)
        self.assertIn("don&#39;t match", response.text)

    def test_subscribe_existing_user_email(self):
        user = self.env.ref("base.user_admin")
        csrf_token = self._get_csrf_token()
        payload = self._subscription_payload(
            csrf_token, email=user.login, confirm_email=user.login
        )
        response = self._post_subscription(payload)
        self.assertIn("account already exists", response.text)

    def test_subscribe_invalid_iban(self):
        required = self.env["subscription.request"].sudo().get_required_field()
        if "iban" not in required:
            self.skipTest("a localization module removed iban from the required fields")
        csrf_token = self._get_csrf_token()
        payload = self._subscription_payload(csrf_token, iban="BE00000000000000")
        response = self._post_subscription(payload)
        self.assertIn("IBAN is not valid", response.text)

    def test_subscribe_exceeding_maximum_amount(self):
        self.company.subscription_maximum_amount = 10
        csrf_token = self._get_csrf_token()
        response = self._post_subscription(self._subscription_payload(csrf_token))
        self.assertIn("exceeds", response.text)


@tagged("post_install", "-at_install")
class TestWebsiteSubscriptionLogged(HttpCase, CooperatorTestMixin):
    PASSWORD = "website_test_password"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.set_up_cooperator_test_data()
        cls.website = cls.env["website"].get_current_website()
        cls.website.company_id = cls.company
        cls.cooperator = cls.create_dummy_cooperator()
        cls.user = (
            cls.env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "login": "member.web@example.org",
                    "password": cls.PASSWORD,
                    "partner_id": cls.cooperator.id,
                    "groups_id": [(6, 0, [cls.env.ref("base.group_portal").id])],
                }
            )
        )

    def _get_csrf_token(self, page="/become_cooperator"):
        response = self.url_open(page)
        self.assertEqual(response.status_code, 200)
        return CSRF_RE.search(response.text).group(1)

    def _payload(self, csrf_token, **overrides):
        share_template = self.share_y.product_tmpl_id
        payload = {
            "csrf_token": csrf_token,
            "logged": "on",
            "firstname": self.cooperator.firstname,
            "lastname": self.cooperator.lastname,
            "email": self.cooperator.email,
            "birthdate": "1990-01-01",
            "gender": "male",
            "phone": "+32 471 33 33 33",
            "iban": "BE71096123456769",
            "address": "Rue du Web 1",
            "zip_code": "1000",
            "city": "Brussels",
            "country_id": str(self.env.ref("base.be").id),
            "lang": "en_US",
            "share_product_id": str(share_template.id),
            "ordered_parts": "1",
            "total_parts": str(self.share_y.list_price),
            "data_policy_approved": "on",
            "internal_rules_approved": "on",
            "financial_risk_approved": "on",
            "generic_rules_approved": "on",
        }
        required = self.env["subscription.request"].sudo().get_required_field()
        if "vat" in required:
            payload["vat"] = "529.982.240-59"
        payload.update(overrides)
        return payload

    def test_logged_member_form_is_prefilled(self):
        self.authenticate("member.web@example.org", self.PASSWORD)
        response = self.url_open("/become_cooperator")
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.cooperator.firstname, response.text)
        self.assertIn(self.cooperator.email, response.text)

    def test_logged_member_subscribes_an_increase(self):
        self.authenticate("member.web@example.org", self.PASSWORD)
        csrf_token = self._get_csrf_token()
        response = self.url_open(
            "/subscription/subscribe_share", data=self._payload(csrf_token)
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("successfully", response.text)
        request = self.env["subscription.request"].search(
            [("partner_id", "=", self.cooperator.id), ("state", "=", "draft")]
        )
        self.assertEqual(len(request), 1)
        self.assertTrue(request.already_cooperator)

    def test_logged_member_cannot_mix_share_types(self):
        self.company.unmix_share_type = True
        self.authenticate("member.web@example.org", self.PASSWORD)
        csrf_token = self._get_csrf_token()
        payload = self._payload(
            csrf_token,
            share_product_id=str(self.share_x.product_tmpl_id.id),
            total_parts=str(self.share_x.list_price),
        )
        response = self.url_open("/subscription/subscribe_share", data=payload)
        self.assertIn("two different types", response.text)

    def test_id_card_upload_required(self):
        self.company.allow_id_card_upload = True
        self.authenticate("member.web@example.org", self.PASSWORD)
        csrf_token = self._get_csrf_token()
        response = self.url_open(
            "/subscription/subscribe_share", data=self._payload(csrf_token)
        )
        self.assertIn("ID card", response.text)

    def test_id_card_upload_creates_attachment(self):
        self.company.allow_id_card_upload = True
        self.authenticate("member.web@example.org", self.PASSWORD)
        csrf_token = self._get_csrf_token()
        response = self.url_open(
            "/subscription/subscribe_share",
            data=self._payload(csrf_token),
            files={"identity_card_scan": ("id.png", b"fake-image-bytes")},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("successfully", response.text)
        request = self.env["subscription.request"].search(
            [("partner_id", "=", self.cooperator.id), ("state", "=", "draft")]
        )
        attachment = self.env["ir.attachment"].search(
            [
                ("res_model", "=", "subscription.request"),
                ("res_id", "=", request.id),
            ]
        )
        self.assertEqual(attachment.name, "id.png")


@tagged("post_install", "-at_install")
class TestWebsiteSubscriptionCompanyLogged(HttpCase, CooperatorTestMixin):
    PASSWORD = "website_company_password"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.set_up_cooperator_test_data()
        cls.website = cls.env["website"].get_current_website()
        cls.website.company_id = cls.company
        cls.company_cooperator = cls.create_dummy_company_cooperator()
        cls.user = (
            cls.env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "login": "company.web@example.org",
                    "password": cls.PASSWORD,
                    "partner_id": cls.company_cooperator.id,
                    "groups_id": [(6, 0, [cls.env.ref("base.group_portal").id])],
                }
            )
        )

    def test_company_user_is_redirected_to_company_form(self):
        self.authenticate("company.web@example.org", self.PASSWORD)
        response = self.url_open("/become_cooperator")
        self.assertEqual(response.status_code, 200)
        # the company form is served with the company data prefilled
        self.assertIn('name="company_name"', response.text)
        self.assertIn(self.company_cooperator.name, response.text)


@tagged("post_install", "-at_install")
class TestWebsiteSubscriptionDefaults(HttpCase, CooperatorTestMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.set_up_cooperator_test_data()
        cls.website = cls.env["website"].get_current_website()
        cls.website.company_id = cls.company

    def test_page_without_default_share_product(self):
        self.env["product.product"].search(
            [("default_share_product", "=", True)]
        ).write({"default_share_product": False})
        response = self.url_open("/become_cooperator")
        self.assertEqual(response.status_code, 200)

    def test_page_without_default_country(self):
        self.company.default_country_id = False
        response = self.url_open("/become_cooperator")
        self.assertEqual(response.status_code, 200)

    def test_page_with_default_lang(self):
        self.company.default_lang_id = self.env["res.lang"].search(
            [("code", "=", "en_US")]
        )
        response = self.url_open("/become_cooperator")
        self.assertEqual(response.status_code, 200)


@tagged("post_install", "-at_install")
class TestWebsiteSubscriptionEdgeCases(HttpCase, CooperatorTestMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.set_up_cooperator_test_data()
        cls.website = cls.env["website"].get_current_website()
        cls.website.company_id = cls.company

    def _get_csrf_token(self, page="/become_cooperator"):
        response = self.url_open(page)
        return CSRF_RE.search(response.text).group(1)

    def _payload(self, csrf_token, **overrides):
        share_template = self.share_y.product_tmpl_id
        payload = {
            "csrf_token": csrf_token,
            "firstname": "Edge",
            "lastname": "Case",
            "email": "edge.case@example.org",
            "confirm_email": "edge.case@example.org",
            "birthdate": "1990-01-01",
            "gender": "male",
            "phone": "+32 471 55 55 55",
            "iban": "BE71096123456769",
            "address": "Rue Edge 1",
            "zip_code": "1000",
            "city": "Brussels",
            "country_id": str(self.env.ref("base.be").id),
            "lang": "en_US",
            "share_product_id": str(share_template.id),
            "ordered_parts": "1",
            "total_parts": str(self.share_y.list_price),
            "data_policy_approved": "on",
            "internal_rules_approved": "on",
            "financial_risk_approved": "on",
            "generic_rules_approved": "on",
        }
        required = self.env["subscription.request"].sudo().get_required_field()
        if "vat" in required:
            payload["vat"] = "390.533.440-20"
        payload.update(overrides)
        return payload

    def test_company_page_prefills_submitted_values(self):
        response = self.url_open("/become_company_cooperator?company_name=Prefilled+Co")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Prefilled Co", response.text)

    def test_public_visitor_declares_being_cooperator(self):
        csrf_token = self._get_csrf_token()
        payload = self._payload(csrf_token, already_cooperator="on")
        response = self.url_open("/subscription/subscribe_share", data=payload)
        self.assertIn("successfully", response.text)
        request = self.env["subscription.request"].search(
            [("email", "=", "edge.case@example.org")]
        )
        self.assertTrue(request.already_cooperator)

    def test_invalid_iban_when_required(self):
        registry_class = self.registry["subscription.request"]
        original = registry_class.get_required_field

        def with_iban(model_self):
            required = original(model_self)
            if "iban" not in required:
                required.append("iban")
            return required

        with patch.object(registry_class, "get_required_field", with_iban):
            csrf_token = self._get_csrf_token()
            payload = self._payload(csrf_token, iban="BE00INVALID")
            response = self.url_open("/subscription/subscribe_share", data=payload)
        self.assertIn("IBAN is not valid", response.text)

    def test_additional_validation_hook_can_reject(self):
        from ..controllers.main import WebsiteSubscription

        def reject(controller, kwargs, logged, values, post_file):
            values["error_msg"] = "rejected by custom hook"
            return False

        with patch.object(WebsiteSubscription, "_additional_validate", reject):
            csrf_token = self._get_csrf_token()
            response = self.url_open(
                "/subscription/subscribe_share",
                data=self._payload(csrf_token),
            )
        self.assertIn("rejected by custom hook", response.text)

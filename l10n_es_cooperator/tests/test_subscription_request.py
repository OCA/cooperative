from datetime import date

from odoo.tests.common import TransactionCase

from odoo.addons.cooperator.tests.cooperator_test_mixin import CooperatorTestMixin


class TestSubscriptionRequest(TransactionCase, CooperatorTestMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.set_up_cooperator_test_data()

    def test_create_subscription_without_partner(self):
        subscription_request = self.env["subscription.request"].create(
            {
                "share_product_id": self.share_y.id,
                "ordered_parts": 2,
                "firstname": "first name",
                "lastname": "last name",
                "email": "email@example.net",
                "phone": "dummy phone",
                "address": "dummy street",
                "zip_code": "dummy zip",
                "city": "dummy city",
                "country_id": self.ref("base.es"),
                "lang": "en_US",
                "gender": "other",
                "birthdate": "1980-01-01",
                "iban": "BE60096123456870",
                "source": "manual",
                "vat": "23917305L",
            }
        )
        self.assertEqual(subscription_request.type, "new")
        self.assertEqual(subscription_request.name, "first name last name")
        self.assertFalse(subscription_request.partner_id)
        subscription_request.validate_subscription_request()
        partner = subscription_request.partner_id
        self.assertTrue(partner)
        self.assertFalse(partner.is_company)
        self.assertEqual(partner.firstname, "first name")
        self.assertEqual(partner.lastname, "last name")
        self.assertEqual(partner.name, "first name last name")
        self.assertEqual(partner.email, "email@example.net")
        self.assertEqual(partner.phone, "dummy phone")
        self.assertEqual(partner.street, "dummy street")
        self.assertEqual(partner.zip, "dummy zip")
        self.assertEqual(partner.city, "dummy city")
        self.assertEqual(partner.country_id, self.browse_ref("base.es"))
        self.assertEqual(partner.lang, "en_US")
        self.assertEqual(partner.gender, "other")
        self.assertEqual(partner.birthdate_date, date(1980, 1, 1))
        self.assertEqual(partner.vat, "23917305L")
        self.assertTrue(partner.cooperator)

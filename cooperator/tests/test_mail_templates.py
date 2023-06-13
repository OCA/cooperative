# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from odoo.tests.common import SavepointCase


class TestMailTemplates(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.default_template = cls.env.ref("cooperator.email_template_confirmation")

    def test_new_company_gets_default_template(self):
        """
        When creating a company, the mail template defaults to the default one.
        """
        company = self.env["res.company"].create({"name": "Test Company"})
        self.assertEqual(
            company.get_cooperator_confirmation_mail_template(), self.default_template
        )

    def test_overwrite_template(self):
        """By setting the field, the get function no longer returns the default
        mail template.
        """
        company = self.env["res.company"].create({"name": "Test Company"})
        template = self.env["mail.template"].create({"name": "Test"})
        company.cooperator_confirmation_mail_template = template
        self.assertEqual(company.get_cooperator_confirmation_mail_template(), template)

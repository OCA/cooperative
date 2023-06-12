# SPDX-FileCopyrightText: 2023 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from odoo.tests.common import SavepointCase


class TestMailTemplates(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.default_template = cls.env.ref("cooperator.email_template_confirmation")

    def test_new_company_gets_copy_of_template(self):
        """When creating a company, they should correctly get a copy of the mail
        template.
        """
        company = self.env["res.company"].create({"name": "Test Company"})
        new_template = company.cooperator_confirmation_mail_template
        self.assertIn(company.name, new_template.name)

    def test_existing_company_gets_copy_of_template(self):
        """When running the default method on an existing company, they should
        correctly get a copy of the mail template. This mirrors the posthook.
        """
        company = self.env["res.company"].create({"name": "Test Company"})
        company.cooperator_confirmation_mail_template = False

        company._assign_default_cooperator_mail_template(
            "cooperator_confirmation_mail_template",
            "cooperator.email_template_confirmation",
        )
        new_template = company.cooperator_confirmation_mail_template
        self.assertIn(company.name, new_template.name)

    def test_assign_default_mail_template_no_copy(self):
        """When providing copy=False, the global template is used."""
        company = self.env["res.company"].create({"name": "Test Company"})
        company.cooperator_confirmation_mail_template = False

        company._assign_default_cooperator_mail_template(
            "cooperator_confirmation_mail_template",
            "cooperator.email_template_confirmation",
            copy=False,
        )
        new_template = company.cooperator_confirmation_mail_template
        self.assertEqual(new_template, self.default_template)

    def test_assign_no_overwrite(self):
        """When instructing not to overwrite, don't."""
        company = self.env["res.company"].create({"name": "Test Company"})
        template = company.cooperator_confirmation_mail_template

        company._assign_default_cooperator_mail_template(
            "cooperator_confirmation_mail_template",
            "cooperator.email_template_confirmation",
            overwrite=False,
        )
        new_template = company.cooperator_confirmation_mail_template
        self.assertEqual(template, new_template)

    def test_assign_overwrite(self):
        """When instructing to overwrite, do."""
        company = self.env["res.company"].create({"name": "Test Company"})
        template = company.cooperator_confirmation_mail_template

        company._assign_default_cooperator_mail_template(
            "cooperator_confirmation_mail_template",
            "cooperator.email_template_confirmation",
            overwrite=True,
        )
        new_template = company.cooperator_confirmation_mail_template
        self.assertNotEqual(template, new_template)

    def test_create_company_dont_overwrite_vals(self):
        """When defining a field in the create method, don't overwrite it."""
        company = self.env["res.company"].create(
            {
                "name": "Test Company",
                "cooperator_confirmation_mail_template": self.default_template.id,
            }
        )
        self.assertEqual(
            company.cooperator_confirmation_mail_template, self.default_template
        )

    def test_create_company_overwrite_falsy_val(self):
        """When 'defining' a field in the create method as falsy, do overwrite it."""
        company = self.env["res.company"].create(
            {
                "name": "Test Company",
                "cooperator_confirmation_mail_template": False,
            }
        )
        self.assertTrue(company.cooperator_confirmation_mail_template)

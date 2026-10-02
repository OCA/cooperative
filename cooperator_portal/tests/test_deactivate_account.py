# SPDX-FileCopyrightText: 2026 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later


from odoo.http import Request
from odoo.tests.common import HttpCase, tagged


@tagged("-at_install", "post_install")
class CooperatorPortalDeactivateAccountCase(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        login = "portal_user"
        cls.login = login
        cls.portal_user = cls.env["res.users"].create(
            {
                "name": login,
                "login": login,
                "password": login,
                "groups_id": [cls.env.ref("base.group_portal").id],
            }
        )

    def test_deactivate_account_not_called(self):
        self.authenticate(self.login, self.login)
        response = self.url_open(
            "/my/deactivate_account",
            data={
                "validation": self.login,
                "password": self.login,
                "csrf_token": Request.csrf_token(self),
            },
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(self.portal_user.active)

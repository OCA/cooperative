Gather and consolidate all cooperator settings in the application parameters.

Consider a refactoring for:

#. removing a potential redundancy between the boolean field "representative"
   and the address type "representative".
#. prevent new contacts to have the representative address type, if they are
   not representative.

See `this issue <https://github.com/coopiteasy/vertical-cooperative/issues/350>`_.

Known caveat: the cooperator localization modules will have to be split in
order to install the ``cooperator`` module without the ``cooperator_website``
module.

A “Cooperative Memberships” page should be added to the ``res.partner`` form,
displaying all the cooperative memberships of the partner
(``cooperative_membership_ids``). The page should only be visible for users
that are both in the ``cooperator_group_user`` group and in the
``base.group_multi_company`` group (how to do this?). Should it display the
memberships of all companies or only the ones in which the user is “logged in”
(checked in the menu)? If all companies, there would be a conflict with the
``cooperative_membership_rule_company`` ``ir.rule``.

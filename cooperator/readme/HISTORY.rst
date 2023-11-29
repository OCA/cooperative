14.0.2.0.0 (2023-07-25)
~~~~~~~~~~~~~~~~~~~~~~~

**Features**

- Each company now has their own mail templates for cooperator-related e-mails. If
  no template is set, the default (global) template is used. (`#73 <https://github.com/OCA/cooperative/issues/73>`_)
- ir.sequences used by this module are no longer global; each company has its own
  sequence for cooperator memberships. (`#74 <https://github.com/OCA/cooperative/issues/74>`_)
- Create subscription journal per company. (`#75 <https://github.com/OCA/cooperative/issues/75>`_)
- Improve multi-company consistency by setting ``company_id`` on records where
  needed and adding the ``check_company`` flag on ``Many2one`` fields. (`#77 <https://github.com/OCA/cooperative/issues/77>`_)
- ir.rules for multi-company usage added. Users cannot access records of this
  module if they are not members of the relevant company. (`#78 <https://github.com/OCA/cooperative/issues/78>`_)
- Move cooperative membership properties from ``res.partner`` to new
  ``cooperative.membership`` model and add company-dependent computed fields on
  ``res.partner`` for backward compatibility. (`#82 <https://github.com/OCA/cooperative/issues/82>`_)


14.0.1.6.0 (2023-02-23)
~~~~~~~~~~~~~~~~~~~~~~~

**Features**

- Removed all selection widgets. (`#55 <https://github.com/OCA/cooperative/issues/55>`_)


12.0.5.3.0 (2022-09-05)
~~~~~~~~~~~~~~~~~~~~~~~

**Improved Documentation**

- Adding USAGE.rst to inform that localization modules are necessary. (`#346 <https://github.com/coopiteasy/vertical-cooperative/issues/346>`_)


12.0.5.0.0 (2022-06-23)
~~~~~~~~~~~~~~~~~~~~~~~

**Deprecations and Removals**

- When no cooperator account is defined on the company, this module previously
  defaulted to the account with code '416000'. This behaviour has been removed
  because the code is Belgian-only. The functionality has been moved to
  ``l10n_be_cooperator``. (`#314 <https://github.com/coopiteasy/vertical-cooperative/issues/314>`_)


12.0.3.3.2 (2022-06-20)
~~~~~~~~~~~~~~~~~~~~~~~

**Bugfixes**

- Fix name computation crash (`#330 <https://github.com/coopiteasy/vertical-cooperative/issues/330>`_)

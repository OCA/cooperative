16.0.1.0.2 (2024-03-12)
~~~~~~~~~~~~~~~~~~~~~~~

**Bugfixes**

- Remove duplicated member field in ``res.partner`` form view. (`#47 <https://github.com/OCA/cooperative/issues/47>`_)


16.0.1.0.0 (2023-11-29)
~~~~~~~~~~~~~~~~~~~~~~~

**Features**

- Add a "Share Type" column to the cooperator register report. (`#86 <https://github.com/OCA/cooperative/issues/86>`_)
- Add a new "Registers" menu entry and move the "Subscription Register" menu
  entry there. (`#86 <https://github.com/OCA/cooperative/issues/86>`_)
- Use default filters instead of domains in contact views. (`#86 <https://github.com/OCA/cooperative/issues/86>`_)
- Merge the confirmation email template for individuals and companies into one. (`#86 <https://github.com/OCA/cooperative/issues/86>`_)
- Rename some files and XML IDs to improve consistency. (`#86 <https://github.com/OCA/cooperative/issues/86>`_)
- Update email templates to the default Odoo layout (what also makes them
  shorter). (`#86 <https://github.com/OCA/cooperative/issues/86>`_)
- Add a description to email templates. (`#86 <https://github.com/OCA/cooperative/issues/86>`_)
- Move the "Cooperator Candidates" menu entry to the "Cooperators" menu. (`#86 <https://github.com/OCA/cooperative/issues/86>`_)
- Add a new "Cooperator Register" view (and menu entry) to display the
  cooperative memberships and allow to print the cooperator register (report
  that was previously on the partner model). (`#86 <https://github.com/OCA/cooperative/issues/86>`_)
- Make the capital release request report inherit from the invoice report
  instead of copying and modifying it. (`#86 <https://github.com/OCA/cooperative/issues/86>`_)


**Bugfixes**

- Ensure that only shares related to the current company appear on the
  cooperator certificate. (`#86 <https://github.com/OCA/cooperative/issues/86>`_)
- Ensure reversals of capital release requests use a name prefix to not clash
  with normal entries ("RSUBJ" instead of "SUBJ"). (`#86 <https://github.com/OCA/cooperative/issues/86>`_)
- Fix subscription requests created by transfer operations: ensure that no
  confirmation email is sent, that they don't appear in the list of subscription
  requests and cannot be erroneously validated. (`#86 <https://github.com/OCA/cooperative/issues/86>`_)
- Fix the display of the first name in email templates and add tests to cover
  this. (`#86 <https://github.com/OCA/cooperative/issues/86>`_)
- Fix error when creating a new partner from the normal partner form. (`#86 <https://github.com/OCA/cooperative/issues/86>`_)
- Fix the layout of all reports by rewriting them from the default invoice
  layout. (`#86 <https://github.com/OCA/cooperative/issues/86>`_)
- Ensure creating a cooperator for a non-current company works (when a capital
  release request is paid). (`#86 <https://github.com/OCA/cooperative/issues/86>`_)
- Ensure that ``share.line.share_number`` cannot be negative. (`#86 <https://github.com/OCA/cooperative/issues/86>`_)
- Don't send a cooperator certificate if there are no remaining shares after an
  operation. (`#86 <https://github.com/OCA/cooperative/issues/86>`_)
- Fix the company name in confirmation email template: display the name of the
  company that made the subscription request instead of the name of the
  cooperative. (`#86 <https://github.com/OCA/cooperative/issues/86>`_)
- Ensure that the company_type value of a subscription request is copied to the
  legal_form field of the created partner. (`#86 <https://github.com/OCA/cooperative/issues/86>`_)
- Add unique per-company constraints on the cooperator register number and the
  operation register number. (`#86 <https://github.com/OCA/cooperative/issues/86>`_)
- Fix copyright statements: add missing ones and use the same format everywhere. (`#86 <https://github.com/OCA/cooperative/issues/86>`_)
- Fix consistency of XML files: XML declaration, spacing. (`#86 <https://github.com/OCA/cooperative/issues/86>`_)
- Display an error message instead of failing when trying to create a
  subscription request from a partner and no default share product is found. (`#86 <https://github.com/OCA/cooperative/issues/86>`_)
- Rename internal string value of "Blocked" subscription request state from
  ``block`` to ``blocked``. (`#86 <https://github.com/OCA/cooperative/issues/86>`_)
- Ensure per-company sequences are used (for the cooperator register number and
  the operation register number). (`#86 <https://github.com/OCA/cooperative/issues/86>`_)
- Prevent to create a subscription request where Email and Company Email have
  the same value, to avoid trying to create a recursive partner hierarchy when
  validating the subscription request (the partner being the parent of itself). (`#86 <https://github.com/OCA/cooperative/issues/86>`_)
- Fix the footer layout to add company logos: wrap the original layout instead
  of overwriting it. (`#86 <https://github.com/OCA/cooperative/issues/86>`_)
- Fix required company fields on subscription request form. (`#86 <https://github.com/OCA/cooperative/issues/86>`_)


**Deprecations and Removals**

- Remove the extra columns in the contacts list view; they can now be found in
  the cooperator register. (`#86 <https://github.com/OCA/cooperative/issues/86>`_)
- Remove deprecated ``subscription.request.create_comp_sub_req()``. Use
  the normal ``subscription.request.create()`` instead. (`#86 <https://github.com/OCA/cooperative/issues/86>`_)
- Remove the useless "subscription" operation request type. (`#86 <https://github.com/OCA/cooperative/issues/86>`_)


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

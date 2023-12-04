16.0.1.0.0 (2023-12-04)
~~~~~~~~~~~~~~~~~~~~~~~

**Features**

- Use the ``website.contactus_thanks`` webpage as a base for the thanks page
  instead of copying and modifying it. (`#88 <https://github.com/OCA/cooperative/issues/88>`_)


**Bugfixes**

- Fix confirmation email disappearing when re-rendering the form when a required
  field is missing. (`#88 <https://github.com/OCA/cooperative/issues/88>`_)
- Fix copyright statements: add missing ones and use the same format everywhere. (`#88 <https://github.com/OCA/cooperative/issues/88>`_)
- Fix validation of upload of identity card scan: correctly detect missing file
  and avoid creating empty attachments. (`#88 <https://github.com/OCA/cooperative/issues/88>`_)
- Fix form controls styling and attributes. (`#88 <https://github.com/OCA/cooperative/issues/88>`_)
- Fix form for companies by using a common layout for both forms (for
  individuals and for companies). (`#88 <https://github.com/OCA/cooperative/issues/88>`_)


**Deprecations and Removals**

- Remove deprecated ``WebsiteSubscription.preRenderThanks()``. Use
  ``WebsiteSubscription.pre_render_thanks()`` instead. (`#88 <https://github.com/OCA/cooperative/issues/88>`_)
- Remove display of company registry number, bank account number and cooperative
  email address on website pages. (`#88 <https://github.com/OCA/cooperative/issues/88>`_)


12.0.3.0.0 (2022-06-23)
~~~~~~~~~~~~~~~~~~~~~~~

**Deprecations and Removals**

- Removed reCAPTCHA logic out of this module. Install
  ``cooperator_website_recaptcha`` to regain the functionality. (`#312 <https://github.com/coopiteasy/vertical-cooperative/issues/312>`_)

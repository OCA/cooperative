16.0.1.2.0 (2026-02-24)
~~~~~~~~~~~~~~~~~~~~~~~

**Features**

- Pass created subscription request to ``.get_subscription_response()`` to allow for dependent modules to access it. (`#163 <https://github.com/OCA/cooperative/issues/163>`_)


**Bugfixes**

- Correctly detect whether a user is logged in when displaying the subscription form. This was only working correctly with the first company. (`#163 <https://github.com/OCA/cooperative/issues/163>`_)
- Ensure that the number of parts field can correctly be passed as an argument to the subscription form and that its value is kept in case of errors when submitting the form. (`#163 <https://github.com/OCA/cooperative/issues/163>`_)


16.0.1.1.0 (2026-02-23)
~~~~~~~~~~~~~~~~~~~~~~~

**Features**

- Ensure that the date of birth entered on the subscription form has at least 4 digits and is not in the future. (`#176 <https://github.com/OCA/cooperative/issues/176>`_)


16.0.1.0.2 (2026-02-13)
~~~~~~~~~~~~~~~~~~~~~~~

**Bugfixes**

- Fix validation error when the number of shares is equal to the minimum quantity. (`#177 <https://github.com/OCA/cooperative/issues/177>`_)


16.0.1.0.1 (2026-02-03)
~~~~~~~~~~~~~~~~~~~~~~~

**Bugfixes**

- Fix the validation of the minimum number of shares on the website form. (`#174 <https://github.com/OCA/cooperative/issues/174>`_)


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

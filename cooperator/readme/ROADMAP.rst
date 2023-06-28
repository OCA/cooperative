Gather and consolidate all cooperator settings in the application parameters.

Consider a refactoring for:
1. removing a potential redundancy between the boolean field "representative" and the address type "representative".
2. prevent new contacts to have the representative address type, if they are not representative.
See [this issue](https://github.com/coopiteasy/vertical-cooperative/issues/350)

known_caveats: the cooperator localization modules will have to be splitted in order to install the `cooperator` module without the `cooperator_website` module.

Registering a payment for a subscription request for a company other than the
current one does not create the cooperative membership information for the
partner.

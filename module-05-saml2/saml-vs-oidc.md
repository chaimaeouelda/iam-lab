# SAML 2.0 et OpenID Connect : tableau comparatif

| Critere | SAML 2.0 | OpenID Connect | Observe dans le lab |
|---|---|---|---|
| Standard | OASIS, 2005 | OpenID Foundation, 2014, au-dessus d'OAuth 2.0 | |
| Format de la preuve | Assertion XML | ID token JWT (JSON) | |
| Signature | XML Signature, certificat | JWS, cle publique dans le JWKS | |
| Transport | Navigateur : redirection puis POST | Redirection, puis echange du code de serveur a serveur | |
| Configuration | Metadonnees XML a echanger | Endpoint .well-known, JWKS dynamique | |
| Rotation des cles | Certificat a mettre a jour cote SP | JWKS relu automatiquement | |
| Autorisation d'API | Non prevue | OAuth 2.0 : scopes et access token | |
| Mobile et SPA | Peu adapte | Adapte, avec PKCE | |
| Demarrage de la connexion | SP-initiated ou IdP-initiated | SP-initiated (IdP-initiated deconseille) | |
| Deconnexion | Single Logout (SLO) | Logout RP-initiated ou back-channel | |
| Vocabulaire | IdP, SP, assertion, NameID, ACS | OP, client, ID token, claims, scopes | |
| Outil de debug | SAML-tracer | Decodeur JWT, DevTools | |
| Usage typique | Applications d'entreprise existantes | Web moderne, mobile, API | |

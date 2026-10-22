# iam-lab — Laboratoire IAM Acme Corp

Infrastructure complete d'Identity and Access Management construite de zero :
Keycloak, OpenLDAP, OIDC, SAML, MFA, RBAC/ABAC, automatisation du cycle de vie,
audit et durcissement, gouvernance et PAM.

Toute l'infrastructure tourne en local via Docker, avec une entreprise fictive
(Acme Corp, voir le document du module 1) comme fil conducteur.

## Architecture

Voir `module-10-capstone/schemas/architecture.png` : trois couches —
socle identite (OpenLDAP + Keycloak + PostgreSQL), applications protegees en
SSO (Grafana en OIDC, Nextcloud en SAML, une API Flask qui verifie les JWT),
et gouvernance/securite (CLI jml.py pour le cycle de vie, Vault pour les
secrets, Loki pour les logs).

![Architecture](module-10-capstone/schemas/architecture.png)

## Modules

| # | Module | Contenu principal |
|---|---|---|
| 1 | Fondamentaux IAM | Glossaire, politique d'acces Acme Corp, personas |
| 2 | Premier Keycloak | Keycloak + PostgreSQL, realm acme, roles, groupes |
| 3 | Annuaires LDAP | OpenLDAP, LDIF 30 utilisateurs, federation Keycloak |
| 4 | OAuth 2.0 / OIDC | Client credentials, Authorization Code, JWT, Grafana SSO |
| 5 | SAML 2.0 | Client SAML, Nextcloud, SAML-tracer, comparatif SAML/OIDC |
| 6 | MFA | TOTP,

@'
# Retour d'experience - lab IAM Acme Corp

## Ce qui a bien fonctionne
- (completer : ex. la federation LDAP -> roles Keycloak a bien illustre le RBAC)
- (completer : ex. la detection de brute force a stoppe une vraie attaque simulee)

## Points de blocage rencontres et comment ils ont ete resolus
- Reseau Docker : Grafana n'etait pas sur le reseau iam-net, corrige avec
  `docker network connect` puis en dur dans le compose.
- Jetons expires (5 min) lors de scripts PowerShell longs : resolu en
  regroupant les appels dans un seul bloc execute sans pause.
- Comptes locaux en conflit avec la federation LDAP (meme identifiant) :
  resolu en supprimant les comptes locaux avant la synchronisation.
- Alias PowerShell `ls` masquant une fonction personnalisee `LS` : renommee.
- (completer avec vos propres incidents)

## Incident traite
Des secrets d'infrastructure (mots de passe admin, secret client OIDC, jeton
Vault) ont ete exposes par inadvertance via des captures d'ecran partagees
pendant le developpement. Tous ont ete regeneres avant publication du depot,
et l'historique Git verifie pour confirmer l'absence de trace.

## Ce que je ferais differemment
- (completer : ex. activer la journalisation des le module 2, pas au module 9)
- (completer : ex. versionner l'export du realm apres chaque sous-etape)

## Competences demontrees
- Federation d'identite (LDAP), SSO multi-protocole (OIDC + SAML)
- RBAC et ABAC avec Keycloak Authorization Services
- Automatisation du cycle de vie des identites (Python, idempotence, tests)
- Detection d'intrusion et durcissement (brute force, MFA conditionnel)
- Gestion de secrets (Vault) et principes PAM
- Infrastructure as code (Docker Compose), gestion de version (Git)

## Pour aller plus loin
- (completer : ex. refaire ce lab avec Terraform pour le provisioning)
- (completer : ex. explorer SCIM pour un vrai provisioning automatise)

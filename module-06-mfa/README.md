# Module 6 : MFA et authentification moderne

Duree : ~3 h

## Realise
- [x] TOTP active pour un compte IT (application d'authentification)
- [x] Passkey enregistree (WebAuthn, via Windows Hello)
- [x] Flux conditionnel `browser-mfa-it` : MFA obligatoire uniquement pour le role `acme-it-admin`
- [x] Parcours de perte de second facteur teste : blocage, suppression par l'administrateur,
      re-enrolement force a la reconnexion

## Politique MFA par groupe

| Groupe | MFA |
|---|---|
| IT (`acme-it-admin`) | Obligatoire (TOTP) |
| DG, RH | Cible : obligatoire (POL-02) |
| Marketing, Ventes | Facultatif |

## A retenir
Le flux `browser-mfa-it` est un duplicata du flux `browser` standard, avec la condition
`User Configured` remplacee par `User Role = acme-it-admin`. Le flux d'origine reste disponible
pour revenir en arriere en un clic (Bind flow).

# Politique MFA d'Acme Corp

## Principe
Le second facteur est impose en fonction du role Keycloak. La condition `User Role` du flux
`browser-mfa-it` s'appuie sur les roles issus des groupes LDAP.

## Politique par groupe

| Groupe / role | MFA | Facteurs acceptes | Justification |
|---|---|---|---|
| IT (`acme-it-admin`) | Obligatoire | TOTP (passkey en complement) | Droits d'administration |
| Direction (`acme-dg`) | Cible : obligatoire | TOTP | Acces aux donnees financieres |
| RH (`acme-rh`) | Cible : obligatoire | TOTP | Donnees personnelles et salaires |
| Marketing, Ventes | Facultatif | TOTP ou passkey | Donnees moins sensibles |

Etat du lab : seul le groupe IT est contraint (conformement au sujet du module).

## Parametres
- TOTP : SHA1, 6 chiffres, periode de 30 secondes
- Passkey : discoverable credential requis, verification de l'utilisateur requise
- Flux : `browser-mfa-it`, lie comme flux navigateur du realm `acme`

## Recuperation en cas de perte du second facteur
1. L'utilisateur contacte le support et son identite est verifiee.
2. Un administrateur supprime le facteur perdu et ferme les sessions de l'utilisateur.
3. A la connexion suivante, un nouvel enrolement est impose.
4. L'operation est tracee dans les evenements Keycloak.

## Captures
Voir le dossier `captures/`.

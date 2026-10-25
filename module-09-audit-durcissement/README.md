# Module 9 : Audit, attaques et durcissement

Duree : ~5 h

## Realise
- [x] Login events et admin events actives
- [x] Attaque brute force simulee (compte de test), avec et sans la detection active :
      succes silencieux sans protection, blocage total avec la detection activee
- [x] Tableau de bord des echecs de connexion par utilisateur (export CSV + requetes PowerShell)
- [x] Checklist de durcissement appliquee et documentee (10 points)
- [x] Rapport de pentest interne redige

## Fichiers
- `wordlists/passwords.txt` : liste de mots de passe utilisee pour le test
- `events.csv` : export des evenements Keycloak de l'attaque
- `checklist-durcissement.md` : 10 points verifies (politique de mot de passe, detection de
  brute force, duree des jetons, CORS, MFA, comptes admin separes, etc.)
- `rapport-pentest-interne.md` : portee, resultat avant/apres durcissement, recommandations

## Resultat cle
Avant activation de la detection : le bon mot de passe finit par etre trouve, sans alerte.
Apres activation (5 echecs -> verrouillage progressif) : l'attaque echoue entierement, le
compte se bloque avant que le bon mot de passe ne soit teste (`user_temporarily_disabled`).

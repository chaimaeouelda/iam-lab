# Checklist de durcissement - realm acme

| # | Point | Statut | Preuve |
|---|---|---|---|
| 1 | Politique de mot de passe (12 car. min, complexite, historique) | Applique | capture policies.png |
| 2 | Detection de brute force (5 echecs, verrouillage progressif) | Applique | events.csv, etape 9 |
| 3 | Duree des tokens reduite (5 min access, 30 min idle) | Applique | capture tokens.png |
| 4 | Jetons allegues desactives par defaut | Applique | capture clients-advanced.png |
| 5 | CORS restreint (Web origins = origine exacte) | Applique | capture cors.png |
| 6 | En-tetes de securite (X-Frame-Options, CSP) | Applique | sortie curl -I |
| 7 | MFA obligatoire pour le groupe IT | Applique (module 6) | capture role-it.png |
| 8 | Compte admin separe des comptes quotidiens | Applique (POL-10) | - |
| 9 | Journalisation des connexions et actions admin | Applique | events.csv |
| 10 | Procedure de revocation de session en cas d'incident | Documentee | ce fichier, section incident |

## Procedure en cas d'incident (session hijacking suspecte)
1. Identifier l'utilisateur et la session dans Events (IP, user agent).
2. Users > (utilisateur) > Sessions > Sign out (ou Logout all active sessions du realm).
3. Forcer un changement de mot de passe (Required user actions > Update Password).
4. Verifier les Admin events pour des actions suspectes effectuees pendant la session.
5. Si un compte a privileges est touche, verifier aussi ses Service account roles.

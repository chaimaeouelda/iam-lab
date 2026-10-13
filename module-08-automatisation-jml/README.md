# Module 8 : automatisation du cycle de vie (JML)

## Outil : jml.py
CLI Python qui pilote l'API Admin de Keycloak (realm acme) avec un compte de service dedie
(client `jml-cli`, droits limites a realm-management).

| Commande | Role |
|---|---|
| `joiner`  | Creer un utilisateur local et l'ajouter a son groupe de departement |
| `mover`   | Changer de departement (ajoute le nouveau groupe, puis retire l'ancien) |
| `leaver`  | Desactiver le compte et couper ses sessions |
| `sync`    | Synchroniser un CSV RH (arrivees, mutations, departs) |
| `report`  | Exporter le CSV "qui a acces a quoi" |

Toutes les commandes d'ecriture acceptent `--dry-run`.

## Principes
- **Idempotence** : relancer une commande ne change rien si l'etat est deja correct.
- **Perimetre** : seuls les comptes du groupe `jml-managed` sont modifies. Les comptes de l'annuaire
  (LDAP en lecture seule) sont refuses.
- **Secrets** : le secret du client est dans `.env` (ignore par Git) ; les mots de passe temporaires
  sont affiches une seule fois et jamais stockes.

## Utilisation
    docker compose build jml
    function jml { docker compose run --rm jml @args }
    jml sync --csv rh.csv --dry-run
    jml sync --csv rh.csv
    jml report --out access-report.csv

## Tests
    docker compose run --rm --entrypoint python jml -m pytest -q
Les tests utilisent une fausse API Keycloak : ils verifient l'idempotence, le refus des comptes LDAP,
le mode --dry-run, la synchronisation CSV et le rapport.

## Limites connues
- Une mutation ne coupe pas les sessions : les jetons deja emis gardent leurs anciens roles
  jusqu'a expiration (5 minutes).
- Les comptes de l'annuaire se gerent dans l'annuaire (LDIF), pas avec cet outil.
- Les mutations vers IT ou Direction ne sont pas gerees (groupes locaux RH, Marketing, Ventes).
- Pas de suppression definitive : POL-07 prevoit 90 jours entre la desactivation et la suppression.

## Rapport
`access-report.csv` : username, enabled, source, groups, realm_roles, grafana_roles, api_roles.

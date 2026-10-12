# Matrice roles x applications (Acme Corp)

| Role metier | Grafana | API : lire | API : ecrire | API : supprimer |
|---|---|---|---|---|
| Tous (acme-employe) | viewer | oui | non | non |
| acme-marketing | editor | oui | non | non |
| acme-ventes | viewer | oui | oui | non |
| acme-manager (composite) | editor | oui | oui | non |
| acme-it-admin | admin | oui | non | oui |

## Mise en oeuvre
- Roles de client : grafana (viewer, editor, admin), acme-api (reports-read, reports-write, admin)
- Roles de realm composites : acme-marketing, acme-ventes, acme-it-admin, acme-manager
- Role par defaut : grafana viewer + acme-api reports-read
- Claim `grafana_roles` (Grafana) et `resource_access.acme-api.roles` (API)

## ABAC (Authorization Services)
- Ressource `rapport-financier`, scopes `view` et `edit`
- view : role acme-dg ou acme-rh ; edit : attribut department = rh

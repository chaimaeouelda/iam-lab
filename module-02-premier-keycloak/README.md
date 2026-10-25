# Module 2 : Premier Keycloak

Duree : ~3 h

## Realise
- [x] `docker-compose.yml` : Keycloak + PostgreSQL, HTTPS via certificat mkcert
- [x] Realm `acme` cree, avec 6 roles (`acme-employe` en role par defaut, `acme-dg`, `acme-rh`,
      `acme-marketing`, `acme-ventes`, `acme-it-admin`)
- [x] 3 groupes (RH, Marketing, Ventes), chacun porteur de son role
- [x] 5 utilisateurs crees (les personas d'Acme), testes via la console de compte
- [x] Export du realm en JSON, versionne dans Git (`export/acme-realm.json`)

## Fichiers
- `docker-compose.yml`, `.env.example`
- `export/acme-realm.json` : sauvegarde complete du realm, reutilisee a chaque incident

## Lecons apprises
- Le volume `pg-data` conserve toutes les donnees entre redemarrages ; ne jamais faire
  `docker compose down -v` par erreur.
- L'export JSON a permis de restaurer le realm au moins une fois apres une perte de donnees Docker.

#!/usr/bin/env python3
"""jml.py - Joiner / Mover / Leaver pour Keycloak (realm acme).

Principes :
  - idempotent : relancer une commande ne change rien si l'etat est deja bon ;
  - prudent    : ne touche que les comptes du groupe `jml-managed` (jamais l'annuaire LDAP) ;
  - --dry-run  : affiche ce qui serait fait, sans rien ecrire.
"""
import argparse
import csv
import os
import secrets
import sys
from dataclasses import dataclass, field

import requests

MANAGED_GROUP = "jml-managed"
DEPARTMENTS = {"rh": "RH", "marketing": "Marketing", "ventes": "Ventes"}
CSV_COLUMNS = ["username", "first_name", "last_name", "email", "department", "status"]
REPORT_COLUMNS = ["username", "enabled", "source", "groups", "realm_roles", "grafana_roles", "api_roles"]


class JmlError(Exception):
    pass


@dataclass
class Result:
    status: str                      # created | updated | unchanged
    actions: list = field(default_factory=list)
    password: str = None


# --------------------------------------------------------------------------- API Keycloak
class Keycloak:
    def __init__(self, url, realm, client_id, client_secret):
        self.base = f"{url}/admin/realms/{realm}"
        self.token_url = f"{url}/realms/{realm}/protocol/openid-connect/token"
        self.client_id, self.client_secret = client_id, client_secret
        self.http = requests.Session()
        self._token = None
        self._client_uuid = {}

    def _auth(self):
        r = self.http.post(self.token_url, timeout=10, data={
            "grant_type": "client_credentials",
            "client_id": self.client_id, "client_secret": self.client_secret})
        if r.status_code != 200:
            raise JmlError(f"authentification refusee ({r.status_code}) : {r.text[:150]}")
        self._token = r.json()["access_token"]

    def _req(self, method, path, **kw):
        for attempt in (1, 2):
            if not self._token:
                self._auth()
            r = self.http.request(method, self.base + path, timeout=15,
                                  headers={"Authorization": f"Bearer {self._token}"}, **kw)
            if r.status_code == 401 and attempt == 1:
                self._token = None
                continue
            break
        if r.status_code >= 400:
            raise JmlError(f"{method} {path} -> {r.status_code} : {r.text[:150]}")
        return r

    def find_user(self, username):
        for u in self._req("GET", "/users", params={"username": username, "exact": "true"}).json():
            if u["username"].lower() == username.lower():
                return u
        return None

    def create_user(self, username, first, last, email, password):
        r = self._req("POST", "/users", json={
            "username": username, "firstName": first, "lastName": last, "email": email,
            "enabled": True, "emailVerified": True,
            "credentials": [{"type": "password", "value": password, "temporary": True}]})
        return r.headers["Location"].rsplit("/", 1)[-1]

    def group_id(self, name):
        for g in self._req("GET", "/groups", params={"search": name}).json():
            if g["name"] == name:
                return g["id"]
        return None

    def user_groups(self, uid):
        return self._req("GET", f"/users/{uid}/groups").json()

    def add_to_group(self, uid, gid):
        self._req("PUT", f"/users/{uid}/groups/{gid}")

    def remove_from_group(self, uid, gid):
        self._req("DELETE", f"/users/{uid}/groups/{gid}")

    def set_enabled(self, uid, enabled):
        user = self._req("GET", f"/users/{uid}").json()
        user["enabled"] = enabled
        self._req("PUT", f"/users/{uid}", json=user)

    def list_sessions(self, uid):
        return self._req("GET", f"/users/{uid}/sessions").json()

    def logout(self, uid):
        self._req("POST", f"/users/{uid}/logout")

    def group_members(self, gid):
        return self._req("GET", f"/groups/{gid}/members", params={"max": 1000}).json()

    def list_users(self):
        return self._req("GET", "/users", params={"max": 1000}).json()

    def _client_id_of(self, client_id):
        if client_id not in self._client_uuid:
            found = self._req("GET", "/clients", params={"clientId": client_id}).json()
            self._client_uuid[client_id] = found[0]["id"] if found else None
        return self._client_uuid[client_id]

    def effective_roles(self, uid):
        roles = {"realm": [r["name"] for r in
                           self._req("GET", f"/users/{uid}/role-mappings/realm/composite").json()]}
        for client in ("grafana", "acme-api"):
            cid = self._client_id_of(client)
            roles[client] = [] if not cid else [r["name"] for r in
                self._req("GET", f"/users/{uid}/role-mappings/clients/{cid}/composite").json()]
        return roles


# --------------------------------------------------------------------------- logique metier
def _group_id(kc, name):
    gid = kc.group_id(name)
    if gid is None:
        raise JmlError(f"groupe '{name}' introuvable dans Keycloak")
    return gid


def _managed_user(kc, username):
    """Retourne (user, {nom_groupe: id}) ou refuse si le compte n'est pas gere par jml."""
    user = kc.find_user(username)
    if user is None:
        raise JmlError(f"utilisateur '{username}' introuvable")
    groups = {g["name"]: g["id"] for g in kc.user_groups(user["id"])}
    if MANAGED_GROUP not in groups:
        raise JmlError(f"'{username}' n'est pas gere par jml (compte LDAP ou manuel) : refus")
    return user, groups


def joiner(kc, username, first, last, email, department, password=None, dry=False):
    if department not in DEPARTMENTS:
        raise JmlError(f"departement inconnu '{department}' (valeurs : {', '.join(DEPARTMENTS)})")
    wanted = [MANAGED_GROUP, DEPARTMENTS[department]]
    gids = {name: _group_id(kc, name) for name in wanted}
    user = kc.find_user(username)
    actions, new_password = [], None

    if user is None:
        new_password = password or secrets.token_urlsafe(12)
        actions.append("create")
        actions += [f"add:{name}" for name in wanted]
        if not dry:
            uid = kc.create_user(username, first, last, email, new_password)
            for name in wanted:
                kc.add_to_group(uid, gids[name])
        return Result("created", actions, new_password)

    _, current = _managed_user(kc, username)
    for name in wanted:
        if name not in current:
            actions.append(f"add:{name}")
            if not dry:
                kc.add_to_group(user["id"], gids[name])
    return Result("updated" if actions else "unchanged", actions)


def mover(kc, username, department, dry=False):
    if department not in DEPARTMENTS:
        raise JmlError(f"departement inconnu '{department}' (valeurs : {', '.join(DEPARTMENTS)})")
    wanted = DEPARTMENTS[department]
    user, current = _managed_user(kc, username)
    actions = []
    if wanted not in current:                      # d'abord ajouter, puis retirer : jamais sans acces
        actions.append(f"add:{wanted}")
        if not dry:
            kc.add_to_group(user["id"], _group_id(kc, wanted))
    for name in DEPARTMENTS.values():
        if name != wanted and name in current:
            actions.append(f"remove:{name}")
            if not dry:
                kc.remove_from_group(user["id"], current[name])
    return Result("updated" if actions else "unchanged", actions)


def leaver(kc, username, dry=False):
    user, _ = _managed_user(kc, username)
    actions = []
    if user.get("enabled", True):
        actions.append("disable")
        if not dry:
            kc.set_enabled(user["id"], False)
    if kc.list_sessions(user["id"]):
        actions.append("logout")
        if not dry:
            kc.logout(user["id"])
    return Result("updated" if actions else "unchanged", actions)


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        missing = [c for c in CSV_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise JmlError(f"colonnes manquantes dans le CSV : {', '.join(missing)}")
        return [{k: (v or "").strip() for k, v in row.items()} for row in reader]


def sync(kc, rows, dry=False):
    """Retourne (lignes de resultat, nombre d'erreurs, orphelins)."""
    out, errors = [], 0
    for row in rows:
        name = row["username"]
        try:
            status = row["status"].lower()
            if status == "active":
                res = joiner(kc, name, row["first_name"], row["last_name"], row["email"],
                             row["department"].lower(), dry=dry)
                if res.status != "created":
                    extra = mover(kc, name, row["department"].lower(), dry=dry)
                    res = Result("updated" if (res.actions or extra.actions) else "unchanged",
                                 res.actions + extra.actions, res.password)
            elif status == "leaver":
                res = leaver(kc, name, dry=dry)
            else:
                raise JmlError(f"statut inconnu '{row['status']}' (active ou leaver)")
            out.append((name, res.status, res.actions, res.password))
        except JmlError as exc:
            errors += 1
            out.append((name, "error", [str(exc)], None))
    listed = {r["username"].lower() for r in rows}
    gid = kc.group_id(MANAGED_GROUP)
    orphans = sorted(m["username"] for m in (kc.group_members(gid) if gid else [])
                     if m["username"].lower() not in listed)
    return out, errors, orphans


def report(kc, path):
    rows = []
    for u in kc.list_users():
        roles = kc.effective_roles(u["id"])
        rows.append({
            "username": u["username"], "enabled": u.get("enabled", True),
            "source": "ldap" if u.get("federationLink") else "local",
            "groups": ";".join(sorted(g["name"] for g in kc.user_groups(u["id"]))),
            "realm_roles": ";".join(sorted(r for r in roles["realm"] if r.startswith("acme-"))),
            "grafana_roles": ";".join(sorted(roles["grafana"])),
            "api_roles": ";".join(sorted(roles["acme-api"])),
        })
    rows.sort(key=lambda r: r["username"])
    with open(path, "w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=REPORT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


# --------------------------------------------------------------------------- ligne de commande
def build_parser():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--dry-run", action="store_true", help="n'ecrit rien, affiche le plan")
    p = argparse.ArgumentParser(prog="jml.py", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    j = sub.add_parser("joiner", parents=[common], help="creer un utilisateur")
    j.add_argument("--username", required=True)
    j.add_argument("--first-name", required=True)
    j.add_argument("--last-name", required=True)
    j.add_argument("--email", required=True)
    j.add_argument("--department", required=True, choices=sorted(DEPARTMENTS))
    j.add_argument("--password", help="mot de passe temporaire (genere si absent)")
    m = sub.add_parser("mover", parents=[common], help="changer de departement")
    m.add_argument("--username", required=True)
    m.add_argument("--department", required=True, choices=sorted(DEPARTMENTS))
    lv = sub.add_parser("leaver", parents=[common], help="desactiver et couper les sessions")
    lv.add_argument("--username", required=True)
    s = sub.add_parser("sync", parents=[common], help="synchroniser un CSV RH")
    s.add_argument("--csv", required=True)
    r = sub.add_parser("report", help="exporter le rapport 'qui a acces a quoi'")
    r.add_argument("--out", default="access-report.csv")
    return p


def make_client():
    secret = os.environ.get("JML_CLIENT_SECRET")
    if not secret:
        raise JmlError("variable JML_CLIENT_SECRET manquante")
    return Keycloak(os.environ.get("KC_URL", "https://keycloak.lab.local"),
                    os.environ.get("KC_REALM", "acme"),
                    os.environ.get("JML_CLIENT_ID", "jml-cli"), secret)


def main(argv=None, kc=None):
    args = build_parser().parse_args(argv)
    tag = "[dry-run] " if getattr(args, "dry_run", False) else ""
    try:
        kc = kc or make_client()
        if args.cmd == "joiner":
            res = joiner(kc, args.username, args.first_name, args.last_name, args.email,
                         args.department, args.password, args.dry_run)
            print(f"{tag}[{res.status}] {args.username} : {', '.join(res.actions) or 'rien a faire'}")
            if res.password and not args.dry_run:
                print(f"Mot de passe temporaire : {res.password}  (a transmettre de facon securisee)")
        elif args.cmd == "mover":
            res = mover(kc, args.username, args.department, args.dry_run)
            print(f"{tag}[{res.status}] {args.username} : {', '.join(res.actions) or 'rien a faire'}")
        elif args.cmd == "leaver":
            res = leaver(kc, args.username, args.dry_run)
            print(f"{tag}[{res.status}] {args.username} : {', '.join(res.actions) or 'rien a faire'}")
        elif args.cmd == "sync":
            lines, errors, orphans = sync(kc, read_csv(args.csv), args.dry_run)
            for name, status, actions, pwd in lines:
                print(f"{tag}[{status}] {name} : {', '.join(actions) or 'rien a faire'}")
                if pwd and not args.dry_run:
                    print(f"    mot de passe temporaire : {pwd}")
            for name in orphans:
                print(f"[orphelin] {name} : gere par jml mais absent du CSV (non modifie)")
            print(f"{tag}{len(lines)} ligne(s), {errors} erreur(s)")
            return 1 if errors else 0
        elif args.cmd == "report":
            print(f"{report(kc, args.out)} utilisateur(s) ecrits dans {args.out}")
        return 0
    except JmlError as exc:
        print(f"ERREUR : {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

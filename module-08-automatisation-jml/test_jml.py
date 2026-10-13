import csv

import pytest

import jml


class FakeKC:
    """Fausse API Keycloak en memoire : meme interface que jml.Keycloak."""

    def __init__(self):
        self.groups = {"RH": "g-rh", "Marketing": "g-mkt", "Ventes": "g-ven", "jml-managed": "g-jml"}
        self.users, self.members, self.sessions, self.writes = {}, {g: set() for g in self.groups.values()}, {}, []
        # un compte d'annuaire : jamais gere par jml
        self.users["u-ldap"] = {"id": "u-ldap", "username": "sophie.martin", "enabled": True,
                                "federationLink": "ldap"}

    def find_user(self, username):
        return next((u for u in self.users.values() if u["username"] == username), None)

    def create_user(self, username, first, last, email, password):
        uid = f"u-{len(self.users)}"
        self.users[uid] = {"id": uid, "username": username, "enabled": True}
        self.writes.append(("create", username))
        return uid

    def group_id(self, name):
        return self.groups.get(name)

    def user_groups(self, uid):
        return [{"id": g, "name": n} for n, g in self.groups.items() if uid in self.members[g]]

    def add_to_group(self, uid, gid):
        self.members[gid].add(uid)
        self.writes.append(("add", uid, gid))

    def remove_from_group(self, uid, gid):
        self.members[gid].discard(uid)
        self.writes.append(("remove", uid, gid))

    def set_enabled(self, uid, enabled):
        self.users[uid]["enabled"] = enabled
        self.writes.append(("enabled", uid, enabled))

    def list_sessions(self, uid):
        return self.sessions.get(uid, [])

    def logout(self, uid):
        self.sessions[uid] = []
        self.writes.append(("logout", uid))

    def group_members(self, gid):
        return [self.users[u] for u in self.members[gid]]

    def list_users(self):
        return list(self.users.values())

    def effective_roles(self, uid):
        names = {n for n, g in self.groups.items() if uid in self.members[g]}
        return {"realm": ["acme-rh"] if "RH" in names else [],
                "grafana": ["viewer"], "acme-api": ["reports-read"]}


@pytest.fixture
def kc():
    return FakeKC()


def make(kc, name="nora.benali", dept="rh", **kw):
    return jml.joiner(kc, name, "Nora", "Benali", f"{name}@acme.lab.local", dept, **kw)


def groups_of(kc, name):
    return sorted(g["name"] for g in kc.user_groups(kc.find_user(name)["id"]))


# ------------------------------------------------------------------ Joiner
def test_joiner_cree_l_utilisateur_et_les_groupes(kc):
    res = make(kc)
    assert res.status == "created" and res.password
    assert groups_of(kc, "nora.benali") == ["RH", "jml-managed"]


def test_joiner_est_idempotent(kc):
    make(kc)
    writes = len(kc.writes)
    res = make(kc)
    assert res.status == "unchanged" and not res.actions
    assert len(kc.writes) == writes            # aucune ecriture a la 2e execution


def test_joiner_repare_un_groupe_manquant(kc):
    make(kc)
    uid = kc.find_user("nora.benali")["id"]
    kc.remove_from_group(uid, "g-rh")
    assert make(kc).actions == ["add:RH"]


def test_joiner_refuse_un_departement_inconnu(kc):
    with pytest.raises(jml.JmlError):
        make(kc, dept="compta")


def test_joiner_refuse_un_compte_ldap(kc):
    with pytest.raises(jml.JmlError, match="pas gere par jml"):
        make(kc, name="sophie.martin")


def test_dry_run_n_ecrit_rien(kc):
    res = make(kc, dry=True)
    assert res.status == "created" and res.actions
    assert kc.writes == [] and kc.find_user("nora.benali") is None


# ------------------------------------------------------------------ Mover
def test_mover_change_de_groupe(kc):
    make(kc)
    res = jml.mover(kc, "nora.benali", "ventes")
    assert res.actions == ["add:Ventes", "remove:RH"]
    assert groups_of(kc, "nora.benali") == ["Ventes", "jml-managed"]


def test_mover_est_idempotent(kc):
    make(kc)
    jml.mover(kc, "nora.benali", "ventes")
    assert jml.mover(kc, "nora.benali", "ventes").status == "unchanged"


def test_mover_refuse_un_compte_ldap_et_un_inconnu(kc):
    with pytest.raises(jml.JmlError):
        jml.mover(kc, "sophie.martin", "ventes")
    with pytest.raises(jml.JmlError, match="introuvable"):
        jml.mover(kc, "personne", "ventes")


# ------------------------------------------------------------------ Leaver
def test_leaver_desactive_et_coupe_les_sessions(kc):
    make(kc)
    uid = kc.find_user("nora.benali")["id"]
    kc.sessions[uid] = [{"id": "s1"}]
    res = jml.leaver(kc, "nora.benali")
    assert res.actions == ["disable", "logout"]
    assert kc.find_user("nora.benali")["enabled"] is False and kc.sessions[uid] == []


def test_leaver_est_idempotent(kc):
    make(kc)
    jml.leaver(kc, "nora.benali")
    assert jml.leaver(kc, "nora.benali").status == "unchanged"


def test_leaver_refuse_un_compte_ldap(kc):
    with pytest.raises(jml.JmlError):
        jml.leaver(kc, "sophie.martin")


# ------------------------------------------------------------------ CSV
def write_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(jml.CSV_COLUMNS)
        w.writerows(rows)


def test_sync_cree_deplace_et_desactive(kc, tmp_path):
    f = tmp_path / "rh.csv"
    write_csv(f, [["a.un", "A", "Un", "a@x", "rh", "active"], ["b.deux", "B", "Deux", "b@x", "ventes", "active"]])
    jml.sync(kc, jml.read_csv(f))
    write_csv(f, [["a.un", "A", "Un", "a@x", "marketing", "active"], ["b.deux", "B", "Deux", "b@x", "ventes", "leaver"]])
    out, errors, _ = jml.sync(kc, jml.read_csv(f))
    assert errors == 0
    assert groups_of(kc, "a.un") == ["Marketing", "jml-managed"]
    assert kc.find_user("b.deux")["enabled"] is False


def test_sync_est_idempotent(kc, tmp_path):
    f = tmp_path / "rh.csv"
    write_csv(f, [["a.un", "A", "Un", "a@x", "rh", "active"], ["b.deux", "B", "Deux", "b@x", "ventes", "active"]])
    jml.sync(kc, jml.read_csv(f))
    writes = len(kc.writes)
    out, errors, _ = jml.sync(kc, jml.read_csv(f))
    assert [o[1] for o in out] == ["unchanged", "unchanged"] and errors == 0
    assert len(kc.writes) == writes


def test_sync_signale_les_erreurs_sans_s_arreter(kc, tmp_path):
    f = tmp_path / "rh.csv"
    write_csv(f, [["sophie.martin", "S", "M", "s@x", "rh", "active"],
                  ["a.un", "A", "Un", "a@x", "rh", "active"],
                  ["c.trois", "C", "Trois", "c@x", "rh", "inconnu"]])
    out, errors, _ = jml.sync(kc, jml.read_csv(f))
    assert errors == 2 and [o[1] for o in out] == ["error", "created", "error"]


def test_sync_signale_les_orphelins(kc, tmp_path):
    make(kc, name="vieux.compte")
    f = tmp_path / "rh.csv"
    write_csv(f, [["a.un", "A", "Un", "a@x", "rh", "active"]])
    assert jml.sync(kc, jml.read_csv(f))[2] == ["vieux.compte"]


def test_csv_avec_colonne_manquante(tmp_path):
    f = tmp_path / "bad.csv"
    f.write_text("username,email\na,b\n", encoding="utf-8")
    with pytest.raises(jml.JmlError, match="colonnes manquantes"):
        jml.read_csv(f)


# ------------------------------------------------------------------ Rapport et CLI
def test_rapport_distingue_ldap_et_local(kc, tmp_path):
    make(kc)
    out = tmp_path / "r.csv"
    assert jml.report(kc, out) == 2
    rows = {r["username"]: r for r in csv.DictReader(open(out, encoding="utf-8-sig"))}
    assert rows["sophie.martin"]["source"] == "ldap"
    assert rows["nora.benali"]["source"] == "local" and rows["nora.benali"]["realm_roles"] == "acme-rh"
    assert rows["nora.benali"]["groups"] == "RH;jml-managed"


def test_cli_joiner_puis_code_de_sortie(kc, capsys):
    argv = ["joiner", "--username", "n.n", "--first-name", "N", "--last-name", "N",
            "--email", "n@x", "--department", "rh"]
    assert jml.main(argv, kc=kc) == 0
    assert "[created]" in capsys.readouterr().out
    assert jml.main(["leaver", "--username", "sophie.martin"], kc=kc) == 1

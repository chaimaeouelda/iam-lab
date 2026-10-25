import os
import requests
import jwt
from functools import wraps
from flask import Flask, request, jsonify, g

ISSUER = os.environ["ISSUER"]
AUDIENCE = os.environ.get("AUDIENCE", "acme-api")
CA_BUNDLE = os.environ.get("CA_BUNDLE", True)

app = Flask(__name__)
_cache = {"keys": []}
REPORTS = [{"id": 1, "title": "Ventes T3"}, {"id": 2, "title": "Budget marketing"}]


def load_keys():
    url = ISSUER + "/protocol/openid-connect/certs"
    data = requests.get(url, verify=CA_BUNDLE, timeout=5).json()
    _cache["keys"] = jwt.PyJWKSet.from_dict(data).keys


def signing_key(token):
    kid = jwt.get_unverified_header(token).get("kid")
    for attempt in range(2):
        if attempt == 1 or not _cache["keys"]:
            load_keys()
        for key in _cache["keys"]:
            if key.key_id == kid:
                return key.key
    raise jwt.InvalidTokenError("unknown signing key")


def require(role=None):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            header = request.headers.get("Authorization", "")
            if not header.startswith("Bearer "):
                return jsonify(error="missing bearer token"), 401
            token = header[7:]
            try:
                claims = jwt.decode(token, signing_key(token), algorithms=["RS256"],
                                    audience=AUDIENCE, issuer=ISSUER)
            except Exception as exc:
                return jsonify(error="invalid token", detail=str(exc)), 401
            roles = set(claims.get("resource_access", {}).get(AUDIENCE, {}).get("roles", []))
            if role and role not in roles:
                return jsonify(error="forbidden", required=role, roles=sorted(roles)), 403
            g.claims, g.roles = claims, roles
            return fn(*args, **kwargs)
        return wrapper
    return decorator


@app.get("/health")
def health():
    return jsonify(status="ok")


@app.get("/me")
@require()
def me():
    return jsonify(user=g.claims.get("preferred_username"), roles=sorted(g.roles),
                   department=g.claims.get("department"))


@app.get("/reports")
@require("reports-read")
def list_reports():
    return jsonify(REPORTS)


@app.post("/reports")
@require("reports-write")
def add_report():
    body = request.get_json(silent=True) or {}
    item = {"id": len(REPORTS) + 1, "title": body.get("title", "untitled")}
    REPORTS.append(item)
    return jsonify(item), 201


@app.delete("/reports/<int:report_id>")
@require("admin")
def delete_report(report_id):
    global REPORTS
    REPORTS = [r for r in REPORTS if r["id"] != report_id]
    return jsonify(deleted=report_id)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

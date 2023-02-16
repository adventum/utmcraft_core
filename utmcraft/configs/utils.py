import os
import urllib.parse


def get_redis_conn_str():
    if (scheme := os.getenv("REDIS_SCHEME")) not in {"redis", "rediss"}:
        raise ValueError(
            f"REDIS_SCHEME .env must be 'redis' or 'rediss' but got '{scheme}'"
        )
    if (host := os.getenv("REDIS_HOST")) is None:
        raise ValueError("REDIS_HOST .env must be set")
    if (port := os.getenv("REDIS_PORT")) is None:
        raise ValueError("REDIS_PORT .env must be set")
    if (password := os.getenv("REDIS_PASSWORD")) is None:
        raise ValueError("REDIS_PASSWORD .env must be set")
    if (db := os.getenv("REDIS_DB")) is None:
        raise ValueError("REDIS_DB .env must be set")
    conn = [scheme, f":{password}@{host}:{port}", f"/{db}"]
    if scheme == "redis":
        conn += ["", "", ""]
        return urllib.parse.urlunparse(conn)
    if (ca_certs := os.getenv("REDIS_CA_CERT")) is None:
        raise ValueError(
            "REDIS_CA_CERT .env must be set because REDIS_SCHEME = 'rediss'"
        )
    conn += [
        "",
        f"ssl_cert_reqs=required&ssl_ca_certs={urllib.parse.quote_plus(ca_certs)}",
        "",
    ]
    return urllib.parse.urlunparse(conn)

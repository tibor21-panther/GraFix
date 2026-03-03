import logging
import ldap3
from ldap3.core.exceptions import LDAPException

log = logging.getLogger("grafix.ldap")


def authenticate(username_input: str, password: str, config: dict) -> tuple[bool, str]:
    dc              = config["dc"]
    port            = int(config.get("port", 389))
    use_ssl         = bool(config.get("use_ssl", False))
    domain          = config["domain"]
    ldap_base       = config["ldap_base"]
    bind_user       = config.get("ldap_bind_user", "")
    bind_password   = config.get("ldap_bind_password", "")
    allowed_group   = config["allowed_group"]
    timeout         = int(config.get("connection_timeout", 5))

    if "\\" in username_input:
        _, sam = username_input.split("\\", 1)
    else:
        sam = username_input
    sam = sam.strip()

    log.info("=== Bejelentkezési kísérlet: %s ===", username_input)
    log.info("DC: %s  port: %s  ssl: %s", dc, port, use_ssl)
    log.info("ldap_base: %s  csoport: %s", ldap_base, allowed_group)

    if not sam or not password:
        log.warning("Hiányzó felhasználónév vagy jelszó")
        return False, "Felhasználónév és jelszó megadása kötelező"

    try:
        server = ldap3.Server(
            dc,
            port=port,
            use_ssl=use_ssl,
            get_info=ldap3.NONE,
            connect_timeout=timeout,
        )

        # ── 1. Service account bind ────────────────────────────────────────────
        svc_conn = None
        if bind_user and bind_password:
            svc_bind_dn = f"{domain}\\{bind_user}"
            log.info("Service account bind kísérlet: %s", svc_bind_dn)
            svc_conn = ldap3.Connection(
                server,
                user=svc_bind_dn,
                password=bind_password,
                authentication=ldap3.NTLM,
                raise_exceptions=False,
            )
            result = svc_conn.bind()
            log.info("Service account bind eredmény: %s | result: %s | desc: %s",
                     result, svc_conn.result.get("result"), svc_conn.result.get("description"))
            if not result:
                log.error("Service account bind sikertelen: %s", svc_conn.result)
                return False, "LDAP service account kapcsolat sikertelen (ellenőrizd a config-ot)"
        else:
            log.warning("Service account nincs megadva a config-ban — service bind kihagyva")

        # ── 2. Felhasználó NTLM bind (jelszó ellenőrzés) ──────────────────────
        user_bind_dn = f"{domain}\\{sam}"
        log.info("User bind kísérlet: %s", user_bind_dn)
        user_conn = ldap3.Connection(
            server,
            user=user_bind_dn,
            password=password,
            authentication=ldap3.NTLM,
            raise_exceptions=False,
        )
        result = user_conn.bind()
        log.info("User bind eredmény: %s | result: %s | desc: %s",
                 result, user_conn.result.get("result"), user_conn.result.get("description"))
        if not result:
            log.warning("User bind sikertelen: %s", user_conn.result)
            if svc_conn:
                svc_conn.unbind()
            return False, "Sikertelen bejelentkezés: hibás felhasználónév vagy jelszó"

        # ── 3. Csoporttagság ellenőrzés ────────────────────────────────────────
        search_conn = svc_conn if svc_conn else user_conn

        group_filter = f"(&(objectClass=group)(cn={allowed_group}))"
        log.info("Csoport keresés — filter: %s  base: %s", group_filter, ldap_base)
        search_conn.search(ldap_base, group_filter, attributes=["distinguishedName"])
        log.info("Csoport keresés találatok: %d  |  %s",
                 len(search_conn.entries),
                 [str(e.distinguishedName) for e in search_conn.entries])

        if not search_conn.entries:
            user_conn.unbind()
            if svc_conn:
                svc_conn.unbind()
            log.error("Csoport nem található: %s", allowed_group)
            return False, f"A '{allowed_group}' csoport nem található a könyvtárban"

        group_dn = search_conn.entries[0].distinguishedName.value
        log.info("Csoport DN: %s", group_dn)

        user_filter = (
            f"(&(objectClass=person)"
            f"(sAMAccountName={sam})"
            f"(memberOf:1.2.840.113556.1.4.1941:={group_dn}))"
        )
        log.info("User csoporttagság keresés — filter: %s", user_filter)
        search_conn.search(ldap_base, user_filter, attributes=["sAMAccountName"])
        log.info("Csoporttagság találatok: %d  |  %s",
                 len(search_conn.entries),
                 [str(e.sAMAccountName) for e in search_conn.entries])

        user_conn.unbind()
        if svc_conn:
            svc_conn.unbind()

        if not search_conn.entries:
            log.warning("User '%s' nincs a '%s' csoportban", sam, allowed_group)
            return False, f"Hozzáférés megtagadva: a '{allowed_group}' csoportba kell tartoznia"

        log.info("Sikeres bejelentkezés: %s", sam)
        return True, sam

    except LDAPException as e:
        log.exception("LDAPException: %s", e)
        return False, f"LDAP kapcsolati hiba: {e}"
    except Exception as e:
        log.exception("Váratlan hiba: %s", e)
        return False, f"Váratlan hiba: {e}"

import ldap3
from ldap3.core.exceptions import LDAPException


def authenticate(username_input: str, password: str, config: dict) -> tuple[bool, str]:
    """
    AD hitelesítés két lépésben:
      1. Service account binddal ellenőrzi, hogy a user létezik
      2. User NTLM binddal ellenőrzi a jelszót
      3. Service account kapcsolaton ellenőrzi a csoporttagságot

    Returns:
        (True,  sam_account_name)  – sikeres belépés, jogosult csoport tagja
        (False, hibaüzenet)        – sikertelen
    """
    dc              = config["dc"]
    port            = int(config.get("port", 389))
    use_ssl         = bool(config.get("use_ssl", False))
    domain          = config["domain"]
    ldap_base       = config["ldap_base"]
    bind_user       = config.get("ldap_bind_user", "")
    bind_password   = config.get("ldap_bind_password", "")
    allowed_group   = config["allowed_group"]
    timeout         = int(config.get("connection_timeout", 5))

    # SAM kinyerése "DOMAIN\user" formátumból
    if "\\" in username_input:
        _, sam = username_input.split("\\", 1)
    else:
        sam = username_input
    sam = sam.strip()

    if not sam or not password:
        return False, "Felhasználónév és jelszó megadása kötelező"

    try:
        server = ldap3.Server(
            dc,
            port=port,
            use_ssl=use_ssl,
            get_info=ldap3.NONE,
            connect_timeout=timeout,
        )

        # ── 1. Service account bind (csoport és user kereséshez) ──────────────
        svc_conn = None
        if bind_user and bind_password:
            svc_conn = ldap3.Connection(
                server,
                user=f"{domain}\\{bind_user}",
                password=bind_password,
                authentication=ldap3.NTLM,
                raise_exceptions=False,
            )
            if not svc_conn.bind():
                return False, "LDAP service account kapcsolat sikertelen (ellenőrizd a config-ot)"

        # ── 2. Felhasználó NTLM bind (jelszó ellenőrzés) ──────────────────────
        user_conn = ldap3.Connection(
            server,
            user=f"{domain}\\{sam}",
            password=password,
            authentication=ldap3.NTLM,
            raise_exceptions=False,
        )
        if not user_conn.bind():
            if svc_conn:
                svc_conn.unbind()
            return False, "Sikertelen bejelentkezés: hibás felhasználónév vagy jelszó"

        # ── 3. Csoporttagság ellenőrzés ────────────────────────────────────────
        # Service account connectionen keresünk (ha van), különben user connon
        search_conn = svc_conn if svc_conn else user_conn

        # Csoport DN keresése (OU-tól független)
        search_conn.search(
            ldap_base,
            f"(&(objectClass=group)(cn={allowed_group}))",
            attributes=["distinguishedName"],
        )
        if not search_conn.entries:
            user_conn.unbind()
            if svc_conn:
                svc_conn.unbind()
            return False, f"A '{allowed_group}' csoport nem található a könyvtárban"

        group_dn = search_conn.entries[0].distinguishedName.value

        # Rekurzív csoporttagság (LDAP_MATCHING_RULE_IN_CHAIN)
        ldap_filter = (
            f"(&(objectClass=person)"
            f"(sAMAccountName={sam})"
            f"(memberOf:1.2.840.113556.1.4.1941:={group_dn}))"
        )
        search_conn.search(ldap_base, ldap_filter, attributes=["sAMAccountName"])

        user_conn.unbind()
        if svc_conn:
            svc_conn.unbind()

        if not search_conn.entries:
            return False, f"Hozzáférés megtagadva: a '{allowed_group}' csoportba kell tartoznia"

        return True, sam

    except LDAPException as e:
        return False, f"LDAP kapcsolati hiba: {e}"
    except Exception as e:
        return False, f"Váratlan hiba: {e}"

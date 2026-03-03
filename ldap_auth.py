import ldap3
from ldap3.core.exceptions import LDAPException


def authenticate(username_input: str, password: str, config: dict) -> tuple[bool, str]:
    """
    AD hitelesítés NTLM-mel + csoporttagság ellenőrzés.

    Returns:
        (True, sam_account_name)  – sikeres belépés, jogosult csoport tagja
        (False, hibaüzenet)       – sikertelen
    """
    dc            = config["dc"]
    domain        = config["domain"]
    ldap_base     = config["ldap_base"]
    allowed_group = config["allowed_group"]

    # SAM kinyerése "DOMAIN\user" formátumból
    if "\\" in username_input:
        _, sam = username_input.split("\\", 1)
    else:
        sam = username_input
    sam = sam.strip()

    if not sam or not password:
        return False, "Felhasználónév és jelszó megadása kötelező"

    try:
        server = ldap3.Server(dc, get_info=ldap3.NONE, connect_timeout=5)

        # Közvetlen NTLM bind a felhasználó hitelesítő adataival
        conn = ldap3.Connection(
            server,
            user=f"{domain}\\{sam}",
            password=password,
            authentication=ldap3.NTLM,
            raise_exceptions=False,
        )

        if not conn.bind():
            return False, "Sikertelen bejelentkezés: hibás felhasználónév vagy jelszó"

        # Csoport DN keresése (OU-tól független)
        conn.search(
            ldap_base,
            f"(&(objectClass=group)(cn={allowed_group}))",
            attributes=["distinguishedName"],
        )
        if not conn.entries:
            conn.unbind()
            return False, f"A '{allowed_group}' csoport nem található a könyvtárban"

        group_dn = conn.entries[0].distinguishedName.value

        # Rekurzív csoporttagság ellenőrzés (LDAP_MATCHING_RULE_IN_CHAIN)
        ldap_filter = (
            f"(&(objectClass=person)"
            f"(sAMAccountName={sam})"
            f"(memberOf:1.2.840.113556.1.4.1941:={group_dn}))"
        )
        conn.search(ldap_base, ldap_filter, attributes=["sAMAccountName"])

        if not conn.entries:
            conn.unbind()
            return False, f"Hozzáférés megtagadva: a '{allowed_group}' csoportba kell tartoznia"

        conn.unbind()
        return True, sam

    except LDAPException as e:
        return False, f"LDAP kapcsolati hiba: {e}"
    except Exception as e:
        return False, f"Váratlan hiba: {e}"

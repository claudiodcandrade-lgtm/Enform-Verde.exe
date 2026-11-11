"""ESA MAAP 90-day renewal reminder; never persist, log or transmit a token.

The authoritative date is when the user CREATED/RENEWED the token at ESA,
not the date an old token was pasted into Enform Verde. If that date is not
known, expiry status is UNKNOWN and no validity is claimed.
"""
from __future__ import annotations

import json
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

MAAP_TOKEN_PORTAL="https://portal.maap.eo.esa.int/ini/services/auth/token/"
TOKEN_VALIDITY_DAYS=90
WARN_DAYS=15
STATUS_FILENAME="esa_maap_token_renewal.json"
# Date explicitly provided by the owner for the currently active token.
# Seed once only; every later renewal date takes precedence.
INITIAL_TOKEN_ISSUE_DATE=date(2026,11,8)


def status_path(home=None):
    return Path(home if home is not None else Path.home())/".enform_verde"/STATUS_FILENAME


def save_renewal_date(issued_on=None, *, path=None, today=None):
    """Store only the calendar issue date; NEVER the token or any hash of it."""
    issued_on=issued_on or datetime.now(timezone.utc).date()
    if isinstance(issued_on,str):
        issued_on=date.fromisoformat(issued_on)
    if not isinstance(issued_on,date):
        raise ValueError("Data de emissão inválida")
    reference_today=today or datetime.now(timezone.utc).date()
    if issued_on>reference_today:
        raise ValueError("Data de emissão não pode ser futura")
    location=Path(path) if path is not None else status_path()
    location.parent.mkdir(parents=True,exist_ok=True)
    payload={"schema":1,"issued_on":issued_on.isoformat(),"validity_days":TOKEN_VALIDITY_DAYS}
    tmp=location.with_name(location.name+".tmp")
    try:
        tmp.write_text(json.dumps(payload,ensure_ascii=False),encoding="utf-8")
        if os.name!="nt":
            os.chmod(tmp,0o600)
        tmp.replace(location)
    finally:
        if tmp.exists():tmp.unlink()
    return renewal_status(path=location,today=reference_today)


def initialize_current_token_date(*, path=None, today=None):
    """Seed owner's stated 2026-11-08 date only if no record yet.

    Does not overwrite any previously registered renewal. The seed is
    applicable solely to the current (Nov 2026) installation and must not
    claim validity on a future new installation.
    """
    today=today or datetime.now(timezone.utc).date()
    location=Path(path) if path is not None else status_path()
    if location.exists():
        return renewal_status(path=location,today=today)
    if today<INITIAL_TOKEN_ISSUE_DATE:
        return renewal_status(path=location,today=today)
    if today>=INITIAL_TOKEN_ISSUE_DATE+timedelta(days=TOKEN_VALIDITY_DAYS):
        # An absent record on a future install does not establish that an
        # unentered 2026 token is still in use.
        return renewal_status(path=location,today=today)
    return save_renewal_date(INITIAL_TOKEN_ISSUE_DATE,path=location,today=today)


def renewal_status(*, path=None, today=None):
    today=today or datetime.now(timezone.utc).date()
    location=Path(path) if path is not None else status_path()
    try:
        record=json.loads(location.read_text(encoding="utf-8"))
        if record.get("schema")!=1:raise ValueError("schema")
        issued=date.fromisoformat(record["issued_on"])
        if issued>today:raise ValueError("future issue date")
    except (FileNotFoundError,ValueError,TypeError,KeyError,UnicodeError,OSError):
        return {"state":"UNKNOWN","days_remaining":None,"issued_on":None,
                "expires_on":None,"url":MAAP_TOKEN_PORTAL}
    expires=issued+timedelta(days=TOKEN_VALIDITY_DAYS)
    days=(expires-today).days
    state="EXPIRED" if days<=0 else "EXPIRING_SOON" if days<=WARN_DAYS else "VALID_ESTIMATED"
    return {"state":state,"days_remaining":days,
            "issued_on":issued.isoformat(),"expires_on":expires.isoformat(),
            "url":MAAP_TOKEN_PORTAL}


def is_authentication_failure(exc):
    """Only verified authentication failures, not missing scenes or timeout."""
    code=getattr(getattr(exc,"response",None),"status_code",None)
    if code in (401,403):return True
    if code==400:
        try:
            error=str(exc.response.json().get("error","")).lower()
            return error in ("invalid_grant","invalid_token")
        except (TypeError,ValueError,AttributeError):
            return False
    return False

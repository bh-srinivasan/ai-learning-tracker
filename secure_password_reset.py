#!/usr/bin/env python3
"""
Reset Admin Password in Azure SQL (env-driven, non-interactive)

- Reads the new password from environment variables (no getpass)
- Uses env vars for DB connection (or a full connection string override)
- Generates PBKDF2 hash with Werkzeug (configurable)
- Parameterized UPDATE for safety

Required env vars:
  NEW_ADMIN_PASSWORD              -> the new password to set for the admin user
  AZURE_SQL_SERVER                -> e.g. ai-learning-sql-centralus.database.windows.net
  AZURE_SQL_DATABASE              -> e.g. ai-learning-db
  (Either provide the below, or a full CONNECTION_STRING)
    AZURE_SQL_USER                -> SQL user (omit if using AAD Authentication in connection string)
    AZURE_SQL_PASSWORD            -> SQL password (omit if using AAD Authentication)

Optional env vars:
  CONNECTION_STRING               -> full ODBC connection string (overrides all connection parts)
  ODBC_DRIVER                     -> default: "ODBC Driver 18 for SQL Server"
  ENCRYPT                         -> default: "yes"
  TRUST_SERVER_CERT               -> default: "no"
  TIMEOUT_SECONDS                 -> default: "15"

  # Table/column overrides (if your schema differs)
  USERS_TABLE                     -> default: "users"
  USERNAME_COLUMN                 -> default: "username"
  PASSWORD_HASH_COLUMN            -> default: "password_hash"
  TARGET_USERNAME                 -> default: "admin"

  # Hash configuration (Werkzeug)
  HASH_METHOD                     -> default: "pbkdf2:sha256"
  HASH_SALT_LENGTH                -> default: "16"
  MIN_PASSWORD_LENGTH             -> default: "8"

  # Diagnostics
  DEBUG                           -> "1" for more verbose logs (secrets redacted)

Usage:
  # bash
  export NEW_ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'Strong@Password123')
  export AZURE_SQL_SERVER="ai-learning-sql-centralus.database.windows.net"
  export AZURE_SQL_DATABASE="ai-learning-db"
  export AZURE_SQL_USER="your-sql-user"
  export AZURE_SQL_PASSWORD="your-sql-password"
  python reset_admin_password.py

  # Or provide a full connection string, e.g. with AAD auth:
  export CONNECTION_STRING='DRIVER={ODBC Driver 18 for SQL Server};SERVER=...;DATABASE=...;Authentication=ActiveDirectoryDefault;Encrypt=yes;TrustServerCertificate=no;'
  python reset_admin_password.py
"""

import os
import sys
import re

# ---- Dependencies checks ----
try:
    import pyodbc
except Exception as e:
    print("❌ Missing or failed to import 'pyodbc'. Install it first:\n   pip install pyodbc")
    sys.exit(1)

try:
    from werkzeug.security import generate_password_hash
except Exception as e:
    print("❌ Missing or failed to import 'werkzeug'. Install it first:\n   pip install werkzeug")
    sys.exit(1)


def _bool_env(name: str, default: bool = False) -> bool:
    val = os.getenv(name, "")
    return (val == "1") or (val.lower() in {"true", "yes", "y"}) if isinstance(val, str) else default


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except Exception:
        return default


def _sanitize_identifier(identifier: str, name_for_error: str) -> str:
    """
    Allow only alphanumerics and underscore for SQL identifiers to avoid injection via env vars.
    """
    if not re.fullmatch(r"[A-Za-z0-9_]+", identifier or ""):
        raise ValueError(f"Invalid {name_for_error}: '{identifier}'. Only letters, numbers, and underscore are allowed.")
    return identifier


def _redact(s: str) -> str:
    if not s:
        return s
    return "********"


def build_connection_string() -> str:
    # Allow full override via CONNECTION_STRING
    full = os.getenv("CONNECTION_STRING")
    if full:
        return full

    driver = os.getenv("ODBC_DRIVER", "ODBC Driver 18 for SQL Server")
    server = os.getenv("AZURE_SQL_SERVER")
    database = os.getenv("AZURE_SQL_DATABASE")
    username = os.getenv("AZURE_SQL_USER")
    password = os.getenv("AZURE_SQL_PASSWORD")
    encrypt = os.getenv("ENCRYPT", "yes")
    tsc = os.getenv("TRUST_SERVER_CERT", "no")

    if not server or not database:
        raise ValueError("Missing AZURE_SQL_SERVER or AZURE_SQL_DATABASE environment variables.")

    # If username/password not supplied, we expect the driver-side Authentication in CONNECTION_STRING (or external auth)
    if username and password:
        conn = (
            f"DRIVER={{{driver}}};"
            f"SERVER={server};DATABASE={database};"
            f"UID={username};PWD={password};"
            f"Encrypt={encrypt};TrustServerCertificate={tsc};"
        )
    else:
        # No SQL credentials provided; rely on driver-based Authentication if present separately
        conn = (
            f"DRIVER={{{driver}}};"
            f"SERVER={server};DATABASE={database};"
            f"Encrypt={encrypt};TrustServerCertificate={tsc};"
        )
    return conn


def main() -> int:
    debug = _bool_env("DEBUG", False)

    # Read the new password from env
    new_password = os.getenv("NEW_ADMIN_PASSWORD")
    if not new_password:
        print("❌ NEW_ADMIN_PASSWORD not set. Aborting.")
        return 1

    min_len = _int_env("MIN_PASSWORD_LENGTH", 8)
    if len(new_password) < min_len:
        print(f"❌ Password must be at least {min_len} characters. Aborting.")
        return 1

    # Hash parameters
    method = os.getenv("HASH_METHOD", "pbkdf2:sha256")
    salt_length = _int_env("HASH_SALT_LENGTH", 16)

    # Table & column names (sanitized)
    try:
        users_table = _sanitize_identifier(os.getenv("USERS_TABLE", "users"), "USERS_TABLE")
        username_col = _sanitize_identifier(os.getenv("USERNAME_COLUMN", "username"), "USERNAME_COLUMN")
        pwdhash_col = _sanitize_identifier(os.getenv("PASSWORD_HASH_COLUMN", "password_hash"), "PASSWORD_HASH_COLUMN")
    except ValueError as ve:
        print(f"❌ {ve}")
        return 1

    target_username = os.getenv("TARGET_USERNAME", "admin")

    # Generate hash
    try:
        password_hash = generate_password_hash(new_password, method=method, salt_length=salt_length)
        if debug:
            print("🔐 Generated hash using:", method, f"(salt_length={salt_length})")
    except Exception as e:
        print(f"❌ Error generating password hash: {e}")
        return 1

    # Build connection string
    try:
        conn_str = build_connection_string()
    except Exception as e:
        print(f"❌ Connection configuration error: {e}")
        return 1

    if debug:
        # Redact secrets in logs
        print("🔧 Connection details (redacted):")
        print("  CONNECTION_STRING:", ("(override provided)" if os.getenv("CONNECTION_STRING") else "(built)"))
        print("  ODBC_DRIVER:", os.getenv("ODBC_DRIVER", "ODBC Driver 18 for SQL Server"))
        print("  AZURE_SQL_SERVER:", os.getenv("AZURE_SQL_SERVER"))
        print("  AZURE_SQL_DATABASE:", os.getenv("AZURE_SQL_DATABASE"))
        print("  AZURE_SQL_USER:", _redact(os.getenv("AZURE_SQL_USER")))
        print("  AZURE_SQL_PASSWORD:", _redact(os.getenv("AZURE_SQL_PASSWORD")))

        print("  Table:", users_table, "| User column:", username_col, "| Hash column:", pwdhash_col)
        print("  Target username:", target_username)

    timeout = _int_env("TIMEOUT_SECONDS", 15)

    # Execute update
    try:
        print("🔄 Connecting to Azure SQL Database...")
        with pyodbc.connect(conn_str, timeout=timeout) as conn:
            with conn.cursor() as cur:
                print("🔄 Updating admin password hash...")
                sql = f"UPDATE [{users_table}] SET [{pwdhash_col}] = ? WHERE [{username_col}] = ?"
                cur.execute(sql, (password_hash, target_username))
                # Note: Some drivers set rowcount after commit; still call commit then check
                conn.commit()
                rows = cur.rowcount

        if rows and rows > 0:
            print(f"✅ Password updated for user '{target_username}'. ({rows} row(s) affected)")
            return 0
        else:
            print(f"❌ No rows updated. User '{target_username}' not found?")
            return 2
    except pyodbc.Error as e:
        print(f"❌ ODBC error: {e}")
        return 3
    except Exception as e:
        print(f"❌ Error updating password: {e}")
        return 4
    finally:
        # Best-effort clear (note: Python immutability may keep copies in memory)
        new_password = None

if __name__ == "__main__":
    sys.exit(main())

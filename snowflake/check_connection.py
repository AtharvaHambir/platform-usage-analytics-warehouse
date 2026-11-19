"""Check the project identity after the account owner runs the access worksheet."""
from pathlib import Path
import os

import snowflake.connector


def connect():
    key = Path(os.environ["PLATFORM_SNOWFLAKE_KEY"]).expanduser()
    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user="PLATFORM_USAGE_DBT_USER",
        authenticator="SNOWFLAKE_JWT",
        private_key_file=str(key),
        role="PLATFORM_USAGE_DBT_ROLE",
        database="PLATFORM_USAGE_LAB",
        schema="ANALYTICS",
        login_timeout=20,
    )


def main():
    with connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute("select current_user(), current_role(), current_database(), current_schema()")
            print(cursor.fetchone())


if __name__ == "__main__":
    main()

import pandas as pd

import sqlite3


def load_acc_data(path_to_sql_db: str):
    connection = sqlite3.connect(path_to_sql_db)

    # validate data
    def do_verify_data_integrity(cnx) -> None:
        no_missing_sub_accs = pd.read_sql_query(
            """select distinct  subscriptions.account_id from subscriptions
            where  subscriptions.account_id not in (select distinct account_id from accounts)""", con=cnx
        )
        assert len(no_missing_sub_accs) == 0, "Unknown IDs present in Subs!. DB corrupted"

        no_missing_event_accs_df = pd.read_sql_query("""select distinct  events.account_id from events
            where  events.account_id not in (select distinct account_id from accounts)""", con=cnx)

        assert len(no_missing_event_accs_df) == 0, "Unknown IDs present in events!. DB corrupted"
        assert len(
            pd.read_sql_query(
                """select account_id, subscription_id, count(*) occurence from subscriptions group by account_id, subscription_id having occurence > 1""",
                con=cnx
            )
        ) == 0, "One would expect account to have a single subscription!"

    do_verify_data_integrity(connection)

    with open("data/grouping.sql", "r") as f:
        grouped_data = f.read()

    grouped_data_df = pd.read_sql_query(grouped_data, connection, )

    with open("data/stats_per_acc.sql", "r") as f:
        stats_per_acc_statement = f.read()

    stats_per_acc_df = pd.read_sql_query(stats_per_acc_statement, connection, parse_dates=[
        "date_signup", "date_subscription", "first_event_date"
    ])
    return stats_per_acc_df

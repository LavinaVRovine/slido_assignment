import pandas as pd
import sqlite3
import streamlit as st
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

connection = sqlite3.connect('./data/_data.db')


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


with open("./data/grouping.sql", "r") as f:
    grouped_data = f.read()

grouped_data_df = pd.read_sql_query(grouped_data, connection, )


with open("./data/stats_per_acc.sql", "r") as f:
    stats_per_acc_statement = f.read()

stats_per_acc_df = pd.read_sql_query(stats_per_acc_statement, connection, parse_dates=[
    "date_signup", "date_subscription", "first_event_date"
])
paying_inactive_accs = stats_per_acc_df[(stats_per_acc_df["n_events"].isnull() & ~stats_per_acc_df["subscription_id"].isnull())]

domain_additional_flags_df = (
            paying_inactive_accs.groupby("domain")["domain"].count() / stats_per_acc_df.groupby("domain")[
        "domain"].count()).to_frame("inactive_percentage")

skoncil jsem tady. snazim se otagovat upsell/consolidate dle dealu
stats_per_acc_df.groupby(["domain", "plan", ], dropna=False)[["price"]].size()




grouped_stats = stats_per_acc_df.groupby("domain").agg(n_accounts=("account_id", "count"), n_users=("users", "sum"),
                                                       n_subscriptions=("subscription_id", "count"),
                                                       revenue=("price", "sum"), n_events=("n_events", "sum"),
                                                       total_participants=("total_participants", "sum"),
                                                       total_active_participants=("total_active_participants", "sum"), )
grouped_stats["activation_30"] = stats_per_acc_df[stats_per_acc_df["date_diff"] <= 30].groupby("domain")["account_id"].count() / grouped_stats["n_accounts"]
grouped_stats["activation_90"] = stats_per_acc_df[stats_per_acc_df["date_diff"] <= 90].groupby("domain")["account_id"].count() / grouped_stats["n_accounts"]
grouped_stats["avg_joined_participants"] = grouped_stats["total_participants"] / grouped_stats["n_events"]
grouped_stats["avg_active_participants"] = grouped_stats["total_active_participants"] / grouped_stats["n_events"]

for c in ("n_users", "n_subscriptions", "revenue", "n_events", "total_participants", "total_active_participants"):
    try:
        grouped_stats[c] = grouped_stats[c].astype(int)
    except TypeError:
        continue

possible_issue_filter_values = {"None": "Showing all domains", "Multiple plans": "Domains with Enterprise sub + other",
                                "Inactive accounts": "Showing domains with paying inactive accounts"}
selected_domain = st.sidebar.selectbox(
    "Select Domain", options=stats_per_acc_df["domain"].unique()
)

table_data = stats_per_acc_df[stats_per_acc_df["domain"] == selected_domain]
# weird stuff, selecting series casts ints to floats?
selected_domain_stats = grouped_stats.loc[selected_domain]


def calculate_delta_and_cast(selected_domain_row: pd.Series, col_name: str):
    return int((selected_domain_row[col_name] -grouped_stats[col_name].mean()))


# "KPIs"
with st.container():
    st.header(body=f"Account data for {selected_domain}" if selected_domain else "All account data")
    st.write("KPI deltas are computed against dataset averages")
    cols = st.columns(4)
    cols[0].metric("N accounts", value=selected_domain_stats["n_accounts"].astype(int),
                   delta=calculate_delta_and_cast(selected_domain_stats, "n_accounts"))
    cols[1].metric("N users", value=selected_domain_stats["n_users"].astype(int),
                   delta=calculate_delta_and_cast(selected_domain_stats, "n_users"))
    cols[2].metric("N subscriptions", value=selected_domain_stats["n_subscriptions"].astype(int),
                   delta=calculate_delta_and_cast(selected_domain_stats, "n_subscriptions"))
    cols[3].metric("Revenue", value=selected_domain_stats["revenue"].astype(int),
                   delta=calculate_delta_and_cast(selected_domain_stats, "revenue"))
    cols_2 = st.columns(4)

    cols_2[0].metric("N events", value=selected_domain_stats["n_events"].astype(int),
                     delta=calculate_delta_and_cast(selected_domain_stats, "n_events"))
    cols_2[1].metric("N total participants", value=selected_domain_stats["total_participants"].astype(int),
                     delta=calculate_delta_and_cast(selected_domain_stats, "total_participants"
                                                    ))
    cols_2[2].metric("Avg participants per event", value=f'{round(selected_domain_stats["avg_joined_participants"],1)}',
                     delta=round(selected_domain_stats["avg_joined_participants"] - grouped_stats[
                         "avg_joined_participants"].mean(), 1))
    cols_3 = st.columns(4)
    cols_3[0].metric("N active total participants",
                     value=selected_domain_stats["total_active_participants"].astype(int),
                     delta=calculate_delta_and_cast(selected_domain_stats, "total_active_participants"
                                                    ))
    cols_3[1].metric("Avg active participants per event", value=round(selected_domain_stats["avg_active_participants"],1),
                     delta=round(selected_domain_stats["avg_active_participants"] - grouped_stats[
                         "avg_active_participants"].mean(),1))
    # interesting, the :.0% is not working for streamlit?
    cols_3[2].metric("Activation 30", value=f'{round(selected_domain_stats["activation_30"]*100,1)}%',
                     delta=f'{round((selected_domain_stats["activation_30"] - grouped_stats["activation_30"].mean())*100, 1)}%')
    cols_3[3].metric("Activation 90", value=f'{round(selected_domain_stats["activation_90"]*100, 0)}%',
                     delta=f'{round((selected_domain_stats["activation_90"] - grouped_stats["activation_90"].mean()) *100,1)}%')
st.header(body=f"Revenue per plan type")
st.bar_chart(data=table_data.groupby("plan")[["price"]].sum().sort_values(by="price",ascending=False), )#orientation="vertical")
st.header(body=f"Accounts per plan type")
st.bar_chart(data=table_data.groupby("plan", dropna=False)[["price"]].size(), )#orientation="vertical")




st.header(body=f"Account data for {selected_domain}" if selected_domain else "All account data")
st.table(table_data)
print()

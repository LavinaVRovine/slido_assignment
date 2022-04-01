import pandas as pd
import numpy as np
import streamlit as st
from typing import List
from calculations import flag_domains, calculate_domain_statistics
from helpers import FilterHelper
from load_data import load_acc_data
from create_kpis import add_kpi_boxes_to_st_container

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)


# hardcoded issue possibilities i came up with
possible_issue_filter_values = [
    FilterHelper("No filter", "Showing all domains", None, None),
    FilterHelper("Multiple plans worth merging", "Domains with Enterprise sub + others", "is_to_merge",
                 "Multiple deals, that could be integrated into an existing enterprise deal"),
    FilterHelper("Inactive accounts", "Showing domains with paying inactive accounts", "is_inactive",
                 "Fair amount of inactive users"),
    FilterHelper("No enterprise deal", "Domains with no enterprise  deals", "is_to_upsell",
                 "No enterprise deal. Lets change that!"),
    FilterHelper("Multiple enterprise deals", "Multiple enterprise deals", "is_to_consolidate",
                 "Multiple enterprise deals. Let's consolidate deals for simplicity"),
]

revenue_from_enterprise_data_pct_selector = st.sidebar.slider("Flag to merge if at least % Revenue non-enterprise",
                                                              min_value=0.1, max_value=0.9,
                                                              value=0.5, step=.1,
                                                              help="It's probably not important to try to upsell a deal, that makes 5% from non-enterprise users")
# calculate all the requested data
stats_per_acc_df = load_acc_data(path_to_sql_db='./data/_data.db')
domain_additional_flags_df = flag_domains(stats_per_acc_df, revenue_from_enterprise_data_pct_selector)
grouped_stats = calculate_domain_statistics(stats_per_acc_df)




domain_filter_selector = st.sidebar.multiselect(
    "Filter by potencial action", options=[d.filter_key for d in possible_issue_filter_values]
)

selected_issue_filter_values: List[FilterHelper] = [x for x in possible_issue_filter_values if
                                                    x.filter_key in domain_filter_selector]
if "No filter" in domain_filter_selector or not domain_filter_selector:
    available_domains = stats_per_acc_df["domain"].unique()
    st.sidebar.markdown("_Showing all domains_")
else:
    cols = [x.df_col_name for x in possible_issue_filter_values if x.filter_key in domain_filter_selector]
    all_masks = []
    for c in cols:
        all_masks.append(
            (domain_additional_flags_df[c] == True)
        )

    available_domains = domain_additional_flags_df.loc[np.array(all_masks).any(axis=0)].index.get_level_values("domain")
    st.sidebar.markdown(
        '_' + " | ".join([v.human_readable_desc_of_issue for v in possible_issue_filter_values if
                          v.filter_key in domain_filter_selector]) + '_')

selected_domain = st.sidebar.selectbox(
    "Select Domain", options=available_domains
)
# TODO: should i merge the two?
selected_domain_flags = domain_additional_flags_df.loc[selected_domain]
table_data = stats_per_acc_df[stats_per_acc_df["domain"] == selected_domain]
# weird stuff, selecting series casts ints to floats?
selected_domain_stats = grouped_stats.loc[selected_domain]

# infoboxes and "KPIs"
with st.container():
    st.header(body=f"Account data for {selected_domain}" if selected_domain else "All account data")
    # add tags if any are appicable for the domain
    domains_flags = []
    for f in [x for x in possible_issue_filter_values if x.df_col_name]:
        if selected_domain_flags[f.df_col_name] == True:
            domains_flags.append(
                f.domain_human_readable_desc
            )
    if domains_flags:
        st.markdown("Domain might have these issues:")
        flag_cols = st.columns(len(domains_flags))
        for i, l in enumerate(domains_flags):
            flag_cols[i].warning(l)
    add_kpi_boxes_to_st_container(selected_domain_stats=selected_domain_stats, grouped_stats=grouped_stats)

st.header(body=f"Revenue per plan type")
st.bar_chart(data=table_data.groupby("plan")[["price"]].sum().sort_values(by="price",
                                                                          ascending=False), )  # orientation="vertical")
st.header(body=f"Accounts per plan type")
st.bar_chart(data=table_data.groupby("plan", dropna=False)[["price"]].size(), )  # orientation="vertical")

st.header(body=f"Underlying data for {selected_domain}" if selected_domain else "All underlying data")

st.table(table_data)

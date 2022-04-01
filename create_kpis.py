import pandas as pd
import streamlit as st


def add_kpi_boxes_to_st_container(selected_domain_stats, grouped_stats) -> None:
    def calculate_delta_and_cast(selected_domain_row: pd.Series, col_name: str):
        return int((selected_domain_row[col_name] - grouped_stats[col_name].mean()))

    st.markdown("_KPI deltas are computed against dataset averages_")
    cols = st.columns(4)
    cols[0].metric("N accounts", value=selected_domain_stats["n_accounts"].astype(int),
                   delta=calculate_delta_and_cast(selected_domain_stats, "n_accounts"))
    cols[1].metric("N users", value=selected_domain_stats["n_users"].astype(int),
                   delta=calculate_delta_and_cast(selected_domain_stats, "n_users"))
    cols[2].metric("N subscriptions", value=selected_domain_stats["n_subscriptions"].astype(int),
                   delta=calculate_delta_and_cast(selected_domain_stats, "n_subscriptions"))
    cols[3].metric("Revenue", value=f'{selected_domain_stats["revenue"].astype(int)}€',
                   delta=f'{calculate_delta_and_cast(selected_domain_stats, "revenue")}€')
    cols_2 = st.columns(4)

    cols_2[0].metric("N events", value=selected_domain_stats["n_events"].astype(int),
                     delta=calculate_delta_and_cast(selected_domain_stats, "n_events"))
    cols_2[1].metric("N total participants", value=selected_domain_stats["total_participants"].astype(int),
                     delta=calculate_delta_and_cast(selected_domain_stats, "total_participants"
                                                    ))
    cols_2[2].metric("Avg participants per event",
                     value=f'{round(selected_domain_stats["avg_joined_participants"], 1)}',
                     delta=round(selected_domain_stats["avg_joined_participants"] - grouped_stats[
                         "avg_joined_participants"].mean(), 1))
    cols_3 = st.columns(4)
    cols_3[0].metric("N active total participants",
                     value=selected_domain_stats["total_active_participants"].astype(int),
                     delta=calculate_delta_and_cast(selected_domain_stats, "total_active_participants"
                                                    ))
    cols_3[1].metric("Avg active participants per event",
                     value=round(selected_domain_stats["avg_active_participants"], 1),
                     delta=round(selected_domain_stats["avg_active_participants"] - grouped_stats[
                         "avg_active_participants"].mean(), 1))
    # interesting, the :.0% is not working for streamlit?
    cols_3[2].metric("Activation 30", value=f'{round(selected_domain_stats["activation_30"] * 100, 1)}%',
                     delta=f'{round((selected_domain_stats["activation_30"] - grouped_stats["activation_30"].mean()) * 100, 1)}%')
    cols_3[3].metric("Activation 90", value=f'{round(selected_domain_stats["activation_90"] * 100, 0)}%',
                     delta=f'{round((selected_domain_stats["activation_90"] - grouped_stats["activation_90"].mean()) * 100, 1)}%')
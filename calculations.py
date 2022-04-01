import pandas as pd


def flag_domains(statistics_per_account_df: pd.DataFrame, revenue_from_enterprise_data_pct_selector: float) -> pd.DataFrame:
    """
    Create 'tagging' to identify potencial issues ->
    To reduce number of domains per criteria/issue type for easier investigation.
    :param statistics_per_account_df: DF grouped on account level
    :return: DF on domain level, containing tags that might be signalizing issues with that client
    """
    paying_inactive_accs = statistics_per_account_df[
        (statistics_per_account_df["n_events"].isnull() & ~statistics_per_account_df["subscription_id"].isnull())]
    domain_additional_flags_df = (
            paying_inactive_accs.groupby("domain")["domain"].count() / statistics_per_account_df.groupby("domain")[
        "domain"].count()).to_frame("inactive_percentage")

    domain_plan_sizes_df = statistics_per_account_df.groupby(["domain", "plan", ], dropna=False)[["price"]].size()
    enterprise_count = domain_plan_sizes_df[(domain_plan_sizes_df.index.get_level_values("plan") == "Enterprise")]
    enterprise_count.name = "n_enterprises"
    domain_additional_flags_df = domain_additional_flags_df.join(enterprise_count.droplevel("plan"))
    prices = statistics_per_account_df.groupby(["domain", "plan", ], dropna=False)[["price"]].sum()
    domain_additional_flags_df["pct_revenue_from_enterprise"] = prices[prices.index.get_level_values("plan") == "Enterprise"].droplevel("plan") / statistics_per_account_df.groupby(["domain", ], dropna=False)[["price"]].sum()
    non_enterprise_count = domain_plan_sizes_df[
        ~(domain_plan_sizes_df.index.get_level_values("plan") == "Enterprise")].groupby(level="domain").sum()
    non_enterprise_count.name = "non_enterprise_count"
    domain_additional_flags_df = domain_additional_flags_df.join(non_enterprise_count)
    # TODO: it might be worth explaining, while certain thresholds were selected
    domain_additional_flags_df["is_inactive"] = domain_additional_flags_df["inactive_percentage"] > .5
    domain_additional_flags_df["is_to_consolidate"] = domain_additional_flags_df["n_enterprises"] > 1
    domain_additional_flags_df["is_to_upsell"] = ((domain_additional_flags_df["n_enterprises"].isnull())  )
    domain_additional_flags_df["is_to_merge"] = ((domain_additional_flags_df["non_enterprise_count"] > 1) & (
        ~domain_additional_flags_df["n_enterprises"].isnull()) & (domain_additional_flags_df["pct_revenue_from_enterprise"] < revenue_from_enterprise_data_pct_selector)) # TODO: probably not a good idea to hardcode
    return domain_additional_flags_df


def calculate_domain_statistics(stats_per_acc_df: pd.DataFrame) -> pd.DataFrame:
    """
    Just calculate requested statistics on domain level
    :param stats_per_acc_df:
    :return: DF of grouped statistics on domain level
    """
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

    return grouped_stats

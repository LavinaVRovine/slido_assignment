from dataclasses import dataclass


@dataclass
class FilterHelper:
    """
    Just to store some filtering information easily
    """
    filter_key: str
    human_readable_desc_of_issue: str
    df_col_name: str
    domain_human_readable_desc: str

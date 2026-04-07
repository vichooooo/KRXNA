from typing import TypedDict, Optional
import pandas as pd


class AgentState(TypedDict):
    question: str
    dataframes: dict
    route: Optional[str]
    query_result: Optional[str]
    chart_path: Optional[str]
    summary: Optional[str]
    final_answer: Optional[str]
    reasoning: Optional[str]
    retry_count: int
    is_valid: Optional[bool]
    selected_dataset: Optional[str]

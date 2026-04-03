from typing import TypedDict, Optional, List
import pandas as pd

class AgentState(TypedDict):
    question: str                  # the user's original question
    dataframes: dict               # all loaded CSVs {filename: dataframe}
    route: Optional[str]           # which node to send to: query/chart/summary
    query_result: Optional[str]    # result from pandas query
    chart_path: Optional[str]      # path to generated chart
    summary: Optional[str]         # text summary result
    final_answer: Optional[str]    # the final response shown to user
    reasoning: Optional[str]       # agent's explanation of its thinking
    retry_count: int               # how many times we've retried
    is_valid: Optional[bool]       # did the validator approve the answer
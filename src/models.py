from dataclasses import dataclass, field
from typing import List, Optional, Dict

@dataclass
class SummarySentence:
    sentence: str
    status: Optional[str] = None           # "Verified" / "Partially verified" / "Not verified"
    supporting_quote: Optional[str] = None

@dataclass
class StrategyRecord:
    country: str
    strategy_name: str
    primary_link: Optional[str] = None
    secondary_links: List[str] = field(default_factory=list)

    raw_text: Optional[str] = None
    summary_sentences: List[SummarySentence] = field(default_factory=list)

    # Optional meta
    notes: Dict[str, str] = field(default_factory=dict)

from datetime import datetime
from typing import Dict, cast

from item_synchronizer.resolution_strategy import (
    AlwaysFirstRS,
    AlwaysSecondRS,
    LeastRecentRS,
    MostRecentRS,
    ResolutionStrategy,
)

# Various resolution strategies with their respective names so that the user can choose which
# one they want. ------------------------------------------------------------------------------
name_to_resolution_strategy: Dict[str, ResolutionStrategy] = {
    "MostRecentRS": MostRecentRS(
        date_getter_A=lambda item: cast(datetime, item["updated"]),
        date_getter_B=lambda item: cast(datetime, item["modified"]),
    ),
    "MostRecentRS": LeastRecentRS(
        date_getter_A=lambda item: cast(datetime, item["updated"]),
        date_getter_B=lambda item: cast(datetime, item["modified"]),
    ),
    AlwaysFirstRS.name: AlwaysFirstRS(),  # type: ignore
    AlwaysSecondRS.name: AlwaysSecondRS(),  # type: ignore
}

#!/usr/bin/env python3

from taskw_gcal_sync import TWGCalAggregator
from taskw_gcal_sync.clogger import setup_logging
import logging


def main():
    """Main."""

    logger = logging.getLogger(__name__)
    setup_logging(__name__)
    logger.info("Initialising...")

    tw_config = {
        "tags": ["remindme"],
    }
    gcal_config = {
    }

    with TWGCalAggregator(tw_config=tw_config,
                          gcal_config=gcal_config) as aggregator:

        aggregator.start()

        tw_items = aggregator.tw_side.get_all_items()
        gcal_items = aggregator.gcal_side.get_all_items()

        # Check and potentially register items
        aggregator.register_items(tw_items, "tw")
        aggregator.register_items(gcal_items, "gcal")


if __name__ == "__main__":
    main()

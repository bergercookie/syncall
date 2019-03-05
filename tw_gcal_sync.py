#!/usr/bin/env python3

from taskw_gcal_sync import TWGCalAggregator, GCalSide, TaskWarriorSide
from taskw_gcal_sync.clogger import setup_logging
import logging


def main():
    """Main."""

    logger = logging.getLogger(__name__)
    setup_logging(__name__)
    logger.info("Initialising...")

    tw_config = {
        "tags": "remindme",
    }
    gcal_config = {
    }

    with TWGCalAggregator(tw_config=tw_config,
                          gcal_config=gcal_config) as aggregator:

        aggregator.start()

        tw_items = aggregator.tw_side.get_items()
        gcal_items = aggregator.gcal_side.get_items()
        print("tw_items: ", tw_items)
        print("gcal_items: ", gcal_items)

        # tw_side.add_reminder("This is the new reminder", due="2018-01-01")
        # print("Reminders: {}".format(reminders))
        # print("Length: {}".format(len(reminders)))


if __name__ == "__main__":
    main()

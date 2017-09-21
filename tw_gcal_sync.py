#!/usr/bin/env python

from taskw_gcal_sync import TWGCalAggregator, GCalSide, TaskWarriorSide


def main():
    """Main."""
    with TWGCalAggregator() as aggregator:

        reminders = aggregator.tw_side.get_reminders()
        print("Reminders: {}".format(reminders))
        print("Length: {}".format(len(reminders)))

        reminders = aggregator.gcal_side.get_reminders()
        print("Google Calendar Reminders: {}".format(reminders))
        print("Length: {}".format(len(reminders)))

        # tw_side.add_reminder("This is the new reminder", due="2018-01-01")
        # print("Reminders: {}".format(reminders))
        # print("Length: {}".format(len(reminders)))


if __name__ == "__main__":
    main()

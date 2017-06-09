#!/usr/bin/env python

from taskw_gcal_sync import TWGCalAggregator, GCalSide, TaskWarriorSide


def main():
    """Main."""
    tw_side = TaskWarriorSide()

    reminders = tw_side.get_reminders()
    print("Reminders: {}".format(reminders))
    print("Length: {}".format(len(reminders)))


    tw_side.reminder_add("This is the new reminder", due="2018-01-01")
    print("Reminders: {}".format(reminders))
    print("Length: {}".format(len(reminders)))


if __name__ == "__main__":
    main()

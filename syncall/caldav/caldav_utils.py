import caldav


def icalendar_component(obj: caldav.CalendarObjectResource):
    """The .icalendar_component isn't picked up by linters

    Ignore the warning when accessing it.
    """

    return obj.icalendar_component  # type: ignore


def calendar_todos(calendar: caldav.Calendar):
    return calendar.todos(include_completed=True)

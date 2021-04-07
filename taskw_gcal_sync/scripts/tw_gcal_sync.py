import click

from taskw_gcal_sync.logger import logger
from taskw_gcal_sync.TWGCalAggregator import TWGCalAggregator


@click.command()
@click.option(
    "-c",
    "--gcal-calendar",
    required=True,
    type=str,
    help="Name of the Google Calendar to sync (will be created if not there)",
)
@click.option(
    "-t",
    "--taskwarrior-tag",
    "tw_tags",
    required=True,
    type=str,
    help="Taskwarrior tags to sync",
    multiple=True,
)
@click.option(
    "-o",
    "--order-by",
    type=click.Choice(["description", "end", "entry", "id", "modified", "status", "urgency"]),
    help="Sort the tasks, based on this key and then register/modify/delete them",
)
@click.option(
    "--ascending-order/--descending-order",
    default=True,
    help="Specify ascending/descending order for the order-by option",
)
def main(gcal_calendar, tw_tags, order_by, ascending_order):
    """Main."""

    assert len(tw_tags) == 1, "Trying with multiple tags hasn't been tested yet. Exiting..."

    logger.info("Initialising...")
    tw_config = {"tags": list(tw_tags)}
    gcal_config = {"calendar_summary": gcal_calendar}

    with TWGCalAggregator(tw_config=tw_config, gcal_config=gcal_config) as aggregator:

        aggregator.start()

        # Check and potentially register items
        # tw
        tw_items = aggregator.tw_side.get_all_items(
            order_by=order_by, use_ascending_order=ascending_order
        )
        aggregator.register_items(tw_items, "tw")

        # gcal
        gcal_items = aggregator.gcal_side.get_all_items(
            order_by=order_by, use_ascending_order=ascending_order
        )
        aggregator.register_items(gcal_items, "gcal")

        # Synchronise deleted items
        aggregator.synchronise_deleted_items("tw")
        aggregator.synchronise_deleted_items("gcal")


if __name__ == "__main__":
    main()

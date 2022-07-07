import asana
from bubop import format_dict, logger


def list_asana_workspaces(client: asana.Client) -> None:
    """List the Asana workspaces known to the provided client."""
    items = {}

    workspaces = client.workspaces.find_all()
    for workspace in workspaces:
        items[workspace["name"]] = "gid=%s" % workspace["gid"]

    logger.success(
        format_dict(
            header="\n\nAsana workspaces",
            items=items,
        )
    )

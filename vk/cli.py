import click

import vk.utils as utils

from .commands.install import install
from .commands.layer import layer, layerset
from .commands.pull import pull
from .commands.push import push
from .commands.query import query
from .commands.record import record
from .commands.replay import replay


@click.group()
@click.option('--verbose', is_flag=True)
def cli(verbose):
    """VKCLI - Command line interface for Vulkan layer operations on Android."""
    utils.set_verbosity(verbose)


cli.add_command(install)
cli.add_command(layer)
cli.add_command(layerset)
cli.add_command(pull)
cli.add_command(push)
cli.add_command(query)
cli.add_command(record)
cli.add_command(replay)


def main():
    try:
        cli()
    except click.BadParameter as e:
        e.show()
    except RuntimeError as e:
        click.echo(e)


if __name__ == '__main__':
    main()
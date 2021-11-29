import click
import vk.config as config
import vk.utils as utils

from enum import IntEnum

class QueryMode(IntEnum):
    App = 1
    Layer = 2
    LayerSet = 3


def _print_app_trace_list(app_name: str) -> None:
    """Print trace list with indentiation."""
    root_trace_folder = config.GfxrConfigSettings.get_root_trace_folder()
    trace_list = utils.list_dir(f'{root_trace_folder}/{app_name}')
    if not trace_list:
        return

    click.echo(f'{app_name}:')
    for trace in trace_list:
        click.echo(f'└─ {trace}')


def _show_traces_on_device(input: str) -> None:
    """Show trace files on device.

    Show trace files according to user input:

    ? => Select app and print corresponding traces.
    * => Show all traces in the trace repo on device.
    app_name => Show traces related to specified app.

    Args:
        input: Input argument.

    Raises:
        RuntimeError: An error occured executing adb command.
    """
    root_trace_folder = config.GfxrConfigSettings.get_root_trace_folder()
    if input == '?':
        app_name = utils.get_valid_app_name(input)
        _print_app_trace_list(app_name)
    elif input == '*':
        app_trace_folders = utils.list_dir(root_trace_folder)
        for app_name in app_trace_folders:
            _print_app_trace_list(app_name)
    else:
        app_name = utils.extract_package_name(input)
        app_trace_folders = utils.list_dir(root_trace_folder)
        if app_name in app_trace_folders:
            _print_app_trace_list(app_name)
        else:
            click.echo(f'Can not find traces for "{input}"')


def show_layer_state(show_details: bool) -> None:
    """Show current layer configuration on device.

    Args:
        show_details: If True, show actual system properties.
    """
    global_layers = utils.get_debug_vulkan_layers()
    global_layer_info = 'none' if not global_layers else ':'.join(global_layers)

    debug_app_name = utils.get_gpu_debug_app()
    debug_app_layers = utils.get_gpu_debug_layers()
    debug_app_layer_info = 'none' if not debug_app_layers else ':'.join(debug_app_layers)

    if not show_details:
        click.echo(f'{global_layer_info} (global)')
        click.echo('{} ({})'.format(debug_app_layer_info, debug_app_name))
    else:
        click.echo(f'debug.vulkan.layers: {global_layer_info}')
        click.echo('enable_gpu_debug_layers: {}'.format(utils.get_enable_gpu_debug_layers()))
        click.echo(f'gpu_debug_app: {debug_app_name}')
        click.echo(f'gpu_debug_layers: {debug_app_layer_info}')


@click.command()
@click.option('--app', 'mode', flag_value=int(QueryMode.App), help='Show installed packages.')
@click.option('--layer', 'mode', flag_value=int(QueryMode.Layer), help='Show current active layers.')
@click.option('--layerset', 'mode', flag_value=int(QueryMode.LayerSet), help='Show layer preset.')
@click.option('--trace', type=str, metavar='<app_name>', help='Show traces of <app_name> on device.')
@click.option('--detailed', 'show_details', is_flag=True, help='Show detailed system configurations.')
def query(mode, trace, show_details):
    """Query device info related to apps, traces, layers, etc.

    \b
    >> Example 1: Query installed app on devices.
    $ vk query --app

    \b
    >> Example 2: Query traces from com.foo.bar on device.
    $ vk query --trace com.foo.bar

    \b
    >> Example 3: Query traces from selected app on device.
    $ vk query --trace ?
    """

    if mode == QueryMode.App:
        result = utils.get_package_list()
        click.echo('\n'.join(result))
    elif trace is not None:
        _show_traces_on_device(trace)
    elif mode == QueryMode.Layer:
        show_layer_state(show_details)
    elif mode == QueryMode.LayerSet:
        settings = config.Settings()
        settings.show_layers()
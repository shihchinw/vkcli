import click
import vk.config as config
import vk.utils as utils

from vk.commands.query import show_layer_state


def _add_layers(layer_str, current_layers, set_layers_func):
    """Append layers to current_layers and set to device props.

    Args:
        layer_str: A string in <layer1:layer2:layerN> format.
        current_layers: A list of current layers.
        set_layers_func: A function takes layer list to updates system properties.
    """
    for layer in layer_str.split(':'):
        if layer not in current_layers:
            current_layers.append(layer)
    set_layers_func(current_layers)


def _remove_layers(layer_str, current_layers, set_layers_func):
    """Remove layers from current_layers and update to device props.

    Args:
        layer_str: A string in <layer1:layer2:layerN> format.
        current_layers: A list of current layers.
        set_layers_func: A function takes layer list to updates system properties.
    """
    new_layers = []
    remove_layers = layer_str.split(':')
    for layer in current_layers:
        if layer not in remove_layers:
            new_layers.append(layer)
    set_layers_func(new_layers)


@click.command()
@click.option('--app', 'app_name', type=str, metavar='<app_name>',
              help='Modify per-app layer configuration.')
@click.option('--add', 'add_layer_str', type=str, metavar='<layer_names>',
              help='Add layers <layer1:layer2:layerN>.')
@click.option('--remove', 'remove_layer_str', metavar='<layer_names>', type=str,
              help='Remove layers <layer1:layer2:layerN>.')
@click.option('--set', 'set_layer_str', metavar='<layer_names>', type=str,
              help='Set layers <layer1:layer2:layerN>.')
@click.option('--clear', is_flag=True, help='Clear active layer settings.')
def layer(app_name, add_layer_str, remove_layer_str, set_layer_str, clear):
    """Configure active layer settings.

    \b
    <app_name> could be set to:
        ? Select entity from prompt menu later
        ! Use last used app_name
        Any other string

    \b
    >> Example 1: Add VK_LAYER_foo:VK_LAYER_bar globally.
    $ vk layer --add VK_LAYER_foo:VK_LAYER_bar

    \b
    >> Example 2: Add VK_LAYER_foo to <app_name>.
    $ vk layer --app <app_name> --add VK_LAYER_foo

    \b
    >> Example 3: Add VK_LAYER_foo to selected app.
    $ vk layer --app ? --add VK_LAYER_foo

    \f
    https://developer.android.com/ndk/guides/graphics/validation-layer#enable-layers-outside-app
    """

    if add_layer_str and clear:
        raise click.UsageError('--add can not be used with --clear')
    elif set_layer_str and (add_layer_str or remove_layer_str):
        raise click.UsageError('--set can not be used with --add or --remove')

    if clear:
        utils.enable_gpu_debug_layers(False)
        utils.set_gpu_debug_app('')
        utils.set_gpu_debug_layers(None)
        utils.set_debug_vulkan_layers(None)
        click.echo('Clear all relevant layer settings.')
        return

    if app_name:
        try:
            app_name = config.get_valid_app_name(app_name)
        except click.BadParameter as e:
            e.show()
            return

        # Set per-app layer configuration.
        utils.enable_gpu_debug_layers(True)
        utils.set_gpu_debug_app(app_name)

        current_layers = utils.get_gpu_debug_layers()
        set_layer_func = utils.set_gpu_debug_layers
    else:
        current_layers = utils.get_debug_vulkan_layers()
        set_layer_func = utils.set_debug_vulkan_layers

    if set_layer_str:
        set_layer_func(None)    # Remove all layers
        _add_layers(set_layer_str, [], set_layer_func)
    else:
        if add_layer_str:
            _add_layers(add_layer_str, current_layers, set_layer_func)

        if remove_layer_str == '*':
            set_layer_func(None)     # Remove all layers
        elif remove_layer_str:
            _remove_layers(remove_layer_str, current_layers, set_layer_func)

    click.echo('\nSuccessfully update active layers:')
    show_layer_state(False)


def _save_layer_preset(preset_name):
    settings = config.Settings()
    if settings.has_layer_preset(preset_name) and \
        not click.confirm(f'Override existent preset {preset_name}?'):
        return

    app_layers_value = utils.get_gpu_debug_layers_value()
    global_layers_value = utils.get_debug_vulkan_layers_value()
    app_name = utils.get_gpu_debug_app()

    settings.set_layer_preset(preset_name, global_layers_value, app_name, app_layers_value)
    click.echo(f'Save preset \'{preset_name}\' successfully.')
    show_layer_state(False)


def _load_layer_preset(preset_name):
    settings = config.Settings()

    preset_name_list = settings.get_layer_preset_names()

    if preset_name == '?':
        settings.show_layers(show_indices=True)
        click.echo('')
        preset_count = len(preset_name_list)
        selected_idx = -1
        while not (0 < selected_idx < preset_count):
            selected_idx = click.prompt('Please choose preset (ctrl+c to abort)', type=int)
            if not (0 < selected_idx < preset_count):
                click.echo(f'Error: selected index {selected_idx} is out-of-range!')

        preset_name = preset_name_list[selected_idx]
    elif preset_name not in preset_name_list:
        raise click.BadParameter(f'Can not find preset named \'{preset_name}\'')

    global_layers_value, app_name, app_layers_value = settings.get_layer_preset(preset_name)

    utils.set_debug_vulkan_layers(global_layers_value.split(':'))
    utils.set_gpu_debug_app(app_name)
    utils.set_gpu_debug_layers(app_layers_value.split(':'))
    click.echo(f'Load preset \'{preset_name}\' successfully.')
    show_layer_state(False)


@click.command()
@click.argument('preset_name', type=str)
@click.option('--save', 'action', flag_value='save', help='Save settings to preset.')
@click.option('--load', 'action', flag_value='load', help='Load settings from preset.')
@click.option('--delete', 'action', flag_value='delete', help='Delete preset.')
def layerset(action, preset_name):
    """Customize layer presets.

    PRESET_NAME is the name of preset entry.

    \b
    >> Example 1: Save current layer settings to PRESET_NAME.
    $ vk layerset --save PRESET_NAME.

    \b
    >> Example 2: Load PRESET_NAME to overwrite current layer settings.
    $ vk layerset --load PRESET_NAME.
    """

    if action == 'save':
        _save_layer_preset(preset_name)
    elif action == 'load':
        _load_layer_preset(preset_name)
    elif action == 'delete':
        settings = config.Settings()
        settings.delete_layer_preset(preset_name)
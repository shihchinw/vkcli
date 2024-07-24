import click
import glob
import os

import vk.config as  config
import vk.utils as utils


def get_selected_layer_path():
    """Prompt menu and get selected item."""

    last_layer_bin_folder = config.get_last_layer_bin_folder()
    if not last_layer_bin_folder or not os.path.exists(last_layer_bin_folder):
        utils.log_warning('Can not found last validate installation folder of layer binaries')
        return

    filepath_list = [x for x in os.listdir(last_layer_bin_folder) if x.endswith('.so')]
    selected_layer_name = utils.get_selected_item(filepath_list, 'Valid layer binaries:\n'+ '-' * 80,
                                                  'Please select a layer file to install (ctrl+c to abort)')
    click.echo(f'Selected layer binary: {selected_layer_name}')
    return os.path.join(last_layer_bin_folder, selected_layer_name)


@click.command()
@click.option('--app', 'app_name', type=str, metavar='<app_name>',
              help='Target app for layer installation. Type ? for later selection.')
@click.argument('layer_path', type=click.Path())
def install(app_name, layer_path):
    """Install layers to device.

    LAYER_PATH could be a file path or a directory contains multiple *.so files.

    Global layer installation requires root access. Without root access, we need to specify
    --app to install app-wise layers.

    \b
    <app_name> could be set to:
        ? Select entity from prompt menu later
        ! Use last used app_name
        Any other string

    \b
    >> Example 1: Install layer.so to based directory of target application <app_name>.
    $ vk install --app <app_name> layer.so

    \b
    >> Example 2: Install layer.so to based directory of selected application.
    $ vk install --app ? layer.so

    \b
    >> Example 3: Install *.so within layer_folder to <app_name>'s base directory.
    $ vk install --app <app_name> layer_folder

    \b
    >> Example 4: Prompt menu of layer binaries in last installed folder, and install selected layer binary to app.
    $ vk install --app <app_name> ?
    """

    filepath_list = None
    if os.path.isdir(layer_path):
        filepath_list = glob.glob(os.path.join(layer_path, '*.so'))
        if not filepath_list:
            click.echo('Found no layers')
            return

        click.echo(f'Found layers:')
        for filepath in filepath_list:
            click.echo(filepath)

        config.set_last_layer_bin_folder(layer_path)    # Store folder path for later usage.
    elif layer_path == '?':
        layer_path = get_selected_layer_path()
        if layer_path:
            filepath_list = [layer_path]
    else:
        if not os.path.exists(layer_path):
            layer_name = os.path.basename(layer_path)
            if not layer_name.endswith('.so'):
                layer_name = f'{layer_name}.so'

            layer_path = config.resolve_layer_filepath(layer_name)
            if os.path.exists(layer_path):
                click.echo(f'Found resolved file path: {layer_path}')
            else:
                click.echo(f'Can not find layer binary "{layer_name}" on host')
                return

        filepath_list = [layer_path]

    if not filepath_list:
        return

    is_userdebug_build = utils.is_userdebug_build()

    if app_name is None:
        click.echo('Install layers globally (require ROOT access!)')
        utils.adb_exec('root')
        utils.adb_exec('disable-verity')
        utils.adb_exec('shell setenforce 0')
        dst_folder = '/data/local/debug/vulkan'
        utils.create_folder_if_not_exists(dst_folder)
    else:
        app_name = config.get_valid_app_name(app_name)
        if is_userdebug_build:
            dst_folder = f'/data/data/{app_name}'
        else:
            dst_folder = '/data/local/tmp/'

    for filepath in filepath_list:
        filename = os.path.basename(filepath)
        utils.adb_push(filepath, dst_folder)
        if is_userdebug_build:
            utils.adb_exec(f'shell chmod +x {dst_folder}/{filename}')
        elif app_name:
            utils.copy_layer_file_to_app_folder(app_name, filename)

    if app_name:
        click.echo(f'Install layers to \'{app_name}\' successfully.')
    else:
        click.echo(f'Install layers to {dst_folder} successfully.')

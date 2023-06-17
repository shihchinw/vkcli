import click
import glob
import os

import vk.config as  config
import vk.utils as utils

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
    $ vk install --app <app_name> layder_folder
    """

    if os.path.isdir(layer_path):
        filepath_list = glob.glob(f'{layer_path}/*.so')
    else:
        filepath_list = [layer_path]

    if filepath_list:
        click.echo(f'Found layers:')
        for filepath in filepath_list:
            click.echo(filepath)

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

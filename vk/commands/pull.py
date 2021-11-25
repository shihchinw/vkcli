import click
import os
import vk.utils as utils

from vk.config import GfxrConfigSettings as ConfigSettings


def _pull_file_to_local(src_filepath_on_device, local_dst_folder_path, session):
    """Copy file from device to local directory.

    Args:
        src_filepath_on_device: File path on device.
        local_dst_folder_path: Destination folder on local.
        session: utils.ConfirmSession for overwrite decision.
    """
    filename = os.path.basename(src_filepath_on_device)
    dst_filepath = os.path.join(local_dst_folder_path, filename)
    if not os.path.exists(dst_filepath):
        click.echo(f'Copying {src_filepath_on_device} to {local_dst_folder_path}')
        utils.adb_pull(src_filepath_on_device, local_dst_folder_path)
        return

    if not session.force_overwrite():
        msg = f'{dst_filepath} already exists, overwrite it?'
        if not session.confirm(msg):
            return

    # Overwrite file.
    dst_bak_filepath = utils.get_bak_filepath(dst_filepath)
    os.rename(dst_filepath, dst_bak_filepath)
    display_src_path = src_filepath_on_device if utils.is_verbose() else filename
    click.echo(f'Copying {display_src_path} to {local_dst_folder_path}')
    utils.adb_pull(src_filepath_on_device, local_dst_folder_path)
    os.remove(dst_bak_filepath)


def _pull_trace_folder(src_path_on_device, local_dst_path, session):
    """Copy folder from device to local directory.

    Args:
        src_path_on_device: Folder path on device.
        local_dst_path: Destination folder path on local.
        session: utils.ConfirmSession for overwrite decision.
    """
    basename = os.path.basename(src_path_on_device)
    local_dst_folder_path = os.path.join(local_dst_path, basename)
    if not os.path.exists(local_dst_folder_path):
        os.makedirs(local_dst_folder_path)
        click.echo(f'Copying {src_path_on_device} to {local_dst_path}')
        utils.adb_pull(src_path_on_device, local_dst_path)
        return

    trace_filenames = utils.list_dir(src_path_on_device)
    for trace_name in trace_filenames:
        src_filepath_on_device = os.path.join(src_path_on_device, trace_name)
        _pull_file_to_local(src_filepath_on_device, local_dst_folder_path, session)


def _pull_traces(src_path, local_dst_path, session):
    """Pull trace files to local_dst_path.

    Args:
        src_path: Trace file name or '?' to select from menu.
        local_dst_path: Local folder.
        session: Confirm session for file overwrite.

    Raises:
        BadParameter: If not found trace repo on device.
        RuntimeError: If failed to execute shell commands.
    """
    if src_path == '?':
        app_name = utils.get_valid_app_name('?')
        settings = ConfigSettings(app_name)
        trace_path_list = utils.list_dir(settings.get_trace_folder_on_device())
        trace_name = utils.get_selected_item(trace_path_list, 'Trace files:', 'Please select a trace')
        src_path_on_device = settings.get_trace_path_on_device(trace_name)
    else:
        app_name = utils.extract_package_name(src_path)
        root_trace_folder = ConfigSettings.get_root_trace_folder()
        app_trace_folders = utils.list_dir(root_trace_folder)
        if app_name not in app_trace_folders:
            raise click.BadParameter(f'Can not find \'{app_name}\' in trace repo on device.')

        settings = ConfigSettings(app_name)
        if app_name == src_path:
            # Pull whole traces from app to local host.
            src_path_on_device = settings.get_trace_folder_on_device()
            _pull_trace_folder(src_path_on_device, local_dst_path, session)
            return
        else:
            src_path_on_device = settings.get_trace_path_on_device(src_path)

    if not os.path.exists(local_dst_path):
        os.makedirs(local_dst_path)
        click.echo(f'Copying {src_path_on_device} to {local_dst_path}')
        utils.adb_pull(src_path_on_device, local_dst_path)
    else:
        _pull_file_to_local(src_path_on_device, local_dst_path, session)


@click.command()
@click.option('-d', '--destination', 'dst_folder', type=click.Path(),
              metavar='<path>', default='./output', help='Local destination path.')
@click.option('-f', '--force', is_flag=True, help='Force overwrite local files.')
@click.argument('path', type=click.Path())
def pull(path, dst_folder, force):
    """Pull traces from device.

    PATH could be package name or trace name with naming convention: <app_name>-trace_name.gfxr.
    If PATH is ?, <app_name> could be selected from menu.

    \b
    >> Example 1: Pull trace with explicit file name.
    $ vk pull com.foo.bar-test.gfxr

    \b
    >> Example 2: Pull all traces in trace repo of com.foo.bar from device.
    $ vk pull com.foo.bar

    \b
    >> Example 3: Pull all traces from selected trace repo on device.
    $ vk pull ?
    """

    session = utils.ConfirmSession(force)
    _pull_traces(path, dst_folder, session)
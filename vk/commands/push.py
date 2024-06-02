import click
import os
import vk.utils as utils

from vk.config import GfxrConfigSettings as ConfigSettings


def _push_trace_file(filepath, session):
    """Push trace file to trace repo on device.

    Args:
        filepath: Path to trace file.

    Raises:
        Abort: If user cancels file overwrite.
        RuntimeError: If failed to execution push command.
    """

    _, ext = os.path.splitext(filepath)
    if ext != '.gfxr':
        raise click.BadParameter(f'Unsupport file type {ext}')

    trace_filename = os.path.basename(filepath)
    app_name = utils.extract_package_name(trace_filename)
    if not app_name:
        raise click.BadParameter(f'Can not find app name: {app_name}')

    settings = ConfigSettings(app_name)
    trace_folder_on_device = settings.get_trace_folder_on_device()

    trace_filenames = utils.list_dir(trace_folder_on_device)
    if trace_filename not in trace_filenames:
        utils.create_folder_if_not_exists(trace_folder_on_device)
        click.echo(f'Push {filepath} to {trace_folder_on_device}')
        utils.adb_push(filepath, trace_folder_on_device)
        return

    if not session.force_overwrite():
        msg = f'{trace_filename} already exists on device, overwrite it?'
        if not session.confirm(msg):
            return

    # Overwrite existent file on device.
    capture_tag = utils.extract_trace_capture_tag(trace_filename)
    dst_path_on_device = settings.resolve_trace_path_on_device(capture_tag)
    dst_bak_path_on_device = utils.get_bak_filepath(dst_path_on_device)
    utils.adb_exec(f'shell mv {dst_path_on_device} {dst_bak_path_on_device}')
    click.echo(f'Push {filepath} to {trace_folder_on_device}')
    utils.adb_push(filepath, trace_folder_on_device)
    utils.adb_exec(f'shell rm {dst_bak_path_on_device}')    # Remove old backup file.


@click.command()
@click.option('-f', '--force', is_flag=True, help='Force overwrite file on device.')
@click.argument('src_path', type=click.Path())
def push(src_path, force):
    """Push traces to device."""

    if not os.path.exists(src_path):
        raise click.BadParameter(f'{src_path} was not found!')

    session = utils.ConfirmSession(force)
    if os.path.isfile(src_path):
        _push_trace_file(src_path, session)
        return

    root, _, files = next(os.walk(src_path))
    for path in files:
        _push_trace_file(os.path.join(root, path), session)

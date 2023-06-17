import click
import os
import vk.config as config
import vk.utils as utils


class DumpSession:

    def __init__(self, app_name, layer_name):
        self.app_name = app_name
        self.layer_name = layer_name

    def __enter__(self):
        self.old_global_layers = utils.get_debug_vulkan_layers()
        self.old_app_name = utils.get_gpu_debug_app()
        self.old_app_layers = utils.get_gpu_debug_layers()
        self.old_enable_app_layers = utils.get_enable_gpu_debug_layers()

        utils.enable_gpu_debug_layers(True)
        if self.app_name is None:
            # Set layer globally.
            utils.set_debug_vulkan_layers(self.old_global_layers + [self.layer_name])
            utils.set_gpu_debug_app(None)
            utils.set_gpu_debug_layers(None)
        else:
            utils.set_debug_vulkan_layers(None)
            if self.old_app_name != self.app_name:
                utils.set_gpu_debug_app(self.app_name)
                utils.set_gpu_debug_layers([self.layer_name])
            else:
                utils.set_gpu_debug_layers(self.old_app_layers + [self.layer_name])

            utils.stop_app(self.app_name)
            utils.start_app(self.app_name)

    def __exit__(self, exc_type, exc_value, exc_tb):
        if self.app_name:
            utils.stop_app(self.app_name)

        utils.set_debug_vulkan_layers(self.old_global_layers)
        utils.enable_gpu_debug_layers(self.old_enable_app_layers)
        utils.set_gpu_debug_app(self.old_app_name)
        utils.set_gpu_debug_layers(self.old_app_layers)


@click.command()
@click.option('--app', 'app_name', type=str, metavar='<app_name>',
              help='Dump API of <app_name> (?/!/any other str).')
@click.option('-r', '--range', type=str, default='0-0', help='Output frame range "start(-count(-step))"')
@click.option('-f', '--format', type=click.Choice(['text', 'html', 'json'], case_sensitive=False),
              default='text', help='Output file format.')
@click.option('-t', '--timestamp', 'show_timestamp', is_flag=True, default=False, help='Show timestamp of function calls.')
@click.option('-d', '--destination', 'local_dst_folder', type=click.Path(),
              metavar='<path>', default='./output', help='Local output folder path.')
@click.argument('filename', type=click.Path(), default='')
def dump_api(app_name, range, show_timestamp, format, filename, local_dst_folder):
    """Dump API log with VK_LAYER_LUNARG_api_dump.

    \b
    <app_name> could be set to:
        ? Select entity from prompt menu later
        ! Use last used app_name
        Any other string

    While <app_name> is null, it would dump API of the latest launch of VK application after layer setup (require ROOT access).

    \b
    >> Example 1: Launch com.foo.bar and then dump its API log.
    $ vk dump-api --app com.foo.bar

    \b
    >> Example 2: Launch app from selection and then dump its API log.
    $ vk dump-api --app ?

    \b
    >> Example 3: Launch com.foo.bar and then dump its API log of 8 frames start from frame 5.
    $ vk dump-api --app com.foo.bar --range 5-8

    \f
    https://vulkan.lunarg.com/doc/view/1.3.216.0/mac/api_dump_layer.html
    """

    layer_filename = 'libVkLayer_api_dump.so'
    output_dst_folder = '/sdcard/Android'

    if app_name:
        app_name = config.get_valid_app_name(app_name)
        output_dst_folder = f'/data/data/{app_name}'
        if not filename:
            filename = app_name
        if not utils.check_layer_in_app_folder(app_name, layer_filename):
            utils.log_error(f"Can not find '{layer_filename}' installed for {app_name}.\n"
                            "Please install the layer for the app first.")
            return
    elif not utils.check_layer_in_global_folder(layer_filename):
        utils.log_error(f"Can not find {layer_filename} installed globally.\n"
                        "Please install the layer first (require ROOT access).")
        return

    if not filename:
        filename = 'vk_apidump'

    time_str = utils.get_time_str()
    ext = 'log' if format == 'text' else format
    filepath = f"{filename}_{time_str}.api.{ext}"
    output_path_on_device = f'{output_dst_folder}/{filepath}'

    try:
        # Configure API dump options
        utils.adb_setprop('debug.apidump_log_filename', output_path_on_device)
        utils.adb_setprop('debug.apidump_output_format', format)
        utils.adb_setprop('debug.apidump_output_range', range)
        utils.adb_setprop('debug.apidump_detailed', True)
        utils.adb_setprop('debug.apidump_timestamp', show_timestamp)

        ret = None
        with DumpSession(app_name, 'VK_LAYER_LUNARG_api_dump'):
            click.echo(f"Start dumping API (range={range}) to {output_path_on_device}")
            ret = utils.acquire_valid_input('Want to Stop or Stop-and-Pull (s/sp)? ', ('s', 'sp'))

        if ret == 'sp':
            if not os.path.exists(local_dst_folder):
                os.makedirs(local_dst_folder)

            click.echo(f'Copying {output_path_on_device} to {local_dst_folder}')
            utils.adb_pull(output_path_on_device, local_dst_folder)

        utils.adb_exec(f"shell rm {output_path_on_device}")
        click.echo(f"{output_path_on_device} has been deleted on device.")
    except KeyboardInterrupt:
        click.echo('API dump is canceled.')
        utils.adb_exec(f"shell rm {output_path_on_device}")
        click.echo(f"{output_path_on_device} has been deleted.")


@click.command()
@click.option('--app', 'app_name', type=str, metavar='<app_name>',
              help='Dump API of <app_name>.')
@click.option('-r', '--range', type=str, default='1-5', help='Output frame range "start-count(-step)"')
@click.option('-d', '--destination', 'local_dst_folder', type=click.Path(),
              metavar='<path>', default='./output', help='Local output folder path.')
@click.argument('filename', type=click.Path(), default='screenshot')
def dump_img(app_name, range, filename, local_dst_folder):
    """Dump screenshots by VK_LAYER_LUNARG_screenshot.

    \b
    <app_name> could be set to:
        ? Select entity from prompt menu later
        ! Use last used app_name
        Any other string

    While <app_name> is null, it would dump screenshots of the latest launch of VK application after layer setup (require ROOT access).

    \b
    >> Example 1: Launch com.foo.bar and then dump its screenshots.
    $ vk dump-img --app com.foo.bar

    \b
    >> Example 2: Launch app from selection and then dump its screenshots.
    $ vk dump-img --app ?

    \b
    >> Example 3: Launch app from selection and then dump 5 screenshots every 3 frames start from frame 10.
    $ vk dump-img --app ? --range 10-5-3

    \f
    https://vulkan.lunarg.com/doc/view/1.3.204.1/linux/screenshot_layer.html
    """

    layer_filename = 'libVkLayer_screenshot.so'
    if app_name:
        try:
            app_name = config.get_valid_app_name(app_name)
            if not utils.check_layer_in_app_folder(app_name, layer_filename):
                utils.log_error(f"Can not find {layer_filename} installed for {app_name}.\n"
                                "Please install the layer for the app first.")
                return
        except click.BadParameter as e:
            e.show()
            return

        try:
            # Grant read/write permission for external storage.
            utils.adb_exec(f'shell pm grant {app_name} android.permission.READ_EXTERNAL_STORAGE')
            utils.adb_exec(f'shell pm grant {app_name} android.permission.WRITE_EXTERNAL_STORAGE')
        except RuntimeError:
            utils.log_error(f'Failed to grant read/write permission for external storage from {app_name}.')
            return
    elif not utils.check_layer_in_global_folder(layer_filename):
        utils.log_error(f"Can not find {layer_filename} installed globally.\n"
                        "Please install the layer first (require ROOT access).")
        return

    time_str = utils.get_time_str()
    output_folder_on_device = f"/sdcard/Android/vkcli/{filename}_{time_str}"

    try:
        utils.adb_setprop('debug.vulkan.screenshot.dir', output_folder_on_device)
        utils.adb_setprop('debug.vulkan.screenshot', range)
        utils.create_folder_if_not_exists(output_folder_on_device)

        ret = None
        with DumpSession(app_name, 'VK_LAYER_LUNARG_screenshot'):
            click.echo(f"Start dumping screenshots (range [start-count-step]={range}) to {output_folder_on_device}")
            ret = utils.acquire_valid_input('Want to Stop or Stop-and-Pull (s/sp)? ', ('s', 'sp'))

        if ret == 'sp':
            if not os.path.exists(local_dst_folder):
                os.makedirs(local_dst_folder)

            click.echo(f'Copying {output_folder_on_device} to {local_dst_folder}')
            utils.adb_pull(output_folder_on_device, local_dst_folder)

        utils.delete_dir(output_folder_on_device)
        click.echo(f"{output_folder_on_device} has been deleted on device.")
    except KeyboardInterrupt:
        click.echo('Screenshot dump is canceled.')
        utils.delete_dir(output_folder_on_device)
        click.echo(f"{output_folder_on_device} has been deleted.")
    finally:
        utils.adb_setprop('debug.vulkan.screenshot', '""')

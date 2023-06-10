import click
import os
import vk.utils as utils


def _while_input(message: str, validate_set: set):
    """Acquire validated user input.

    Args:
        message: prompt message.
        validate_set: set of validated string tokens.
    """
    while True:
        ret = input(message)
        if ret in validate_set:
            return ret

class DumpSession:

    def __init__(self, app_name):
        self.app_name = app_name

    def __enter__(self):
        self.old_global_layers = utils.get_debug_vulkan_layers()
        self.old_app_name = utils.get_gpu_debug_app()
        self.old_app_layers = utils.get_gpu_debug_layers()
        self.old_enable_app_layers = utils.get_enable_gpu_debug_layers()

        utils.enable_gpu_debug_layers(True)
        if self.app_name is None:
            # Set layer globally.
            utils.set_debug_vulkan_layers(self.old_global_layers + ['VK_LAYER_LUNARG_api_dump'])
            utils.set_gpu_debug_app(None)
            utils.set_gpu_debug_layers(None)
        else:
            utils.set_debug_vulkan_layers(None)
            if self.old_app_name != self.app_name:
                utils.set_gpu_debug_app(self.app_name)
                utils.set_gpu_debug_layers(['VK_LAYER_LUNARG_api_dump'])
            else:
                utils.set_gpu_debug_layers(self.old_app_layers + ['VK_LAYER_LUNARG_api_dump'])

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
              help='Dump API of <app_name>.')
@click.option('-r', '--range', type=str, default='0-0', help='Output frame range "start-count(-step)"')
@click.option('-t', '--timestamp', 'show_timestamp', is_flag=True, default=False, help='Show timestamp of function calls.')
@click.option('-f', '--format', type=click.Choice(['text', 'html', 'json'], case_sensitive=False),
              default='text', help='Output file format.')
@click.option('-d', '--destination', 'local_dst_folder', type=click.Path(),
              metavar='<path>', default='./output', help='Local output folder path.')
@click.argument('filename', type=click.Path(), default='vk_apidump')
def dump_api(app_name, range, show_timestamp, format, filename, local_dst_folder):
    """Dump API log with VK_LAYER_LUNARG_api_dump.

    When <app_name> is ?, its value could be selected later. While <app_name> is null, it would record
    first VK application after layer setup (require ROOT access).

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

    if app_name:
        try:
            app_name = utils.get_valid_app_name(app_name)
            if not utils.check_layer_in_app_folder(app_name, 'libVkLayer_api_dump.so'):
                utils.log_error(f"Can not find 'libVkLayer_api_dump.so' installed for {app_name}.\n"
                                "Please install the layer for the app first.")
                return
        except click.BadParameter as e:
            e.show()
            return

    time_str = utils.get_time_str()
    ext = 'log' if format == 'text' else format
    filepath = f"{filename}_{time_str}.{ext}"
    output_path_on_device = f"/sdcard/Android/{filepath}"

    try:
        # Configure API dump options
        utils.adb_setprop('debug.apidump_log_filename', output_path_on_device)
        utils.adb_setprop('debug.apidump_output_format', format)
        utils.adb_setprop('debug.apidump_output_range', range)
        utils.adb_setprop('debug.apidump_detailed', True)
        utils.adb_setprop('debug.apidump_timestamp', show_timestamp)

        ret = None
        with DumpSession(app_name):
            click.echo(f"Start dumping API (range={range}) to {output_path_on_device}")
            ret = _while_input('Want to Stop or Stop-and-Pull (s/sp)? ', ('s', 'sp'))

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
import click
import os
import vk.config as config
import vk.utils as utils


class RecordSession:

    def __init__(self, app_name):
        self.app_name = app_name

    def __enter__(self):
        self.old_global_layers = utils.get_debug_vulkan_layers()
        self.old_app_name = utils.get_gpu_debug_app()
        self.old_app_layers = utils.get_gpu_debug_layers()
        self.old_enable_app_layers = utils.get_enable_gpu_debug_layers()

        utils.enable_gpu_debug_layers(True)
        utils.set_debug_vulkan_layers(None)
        utils.set_gpu_debug_app(self.app_name)
        utils.set_gpu_debug_layers(['VK_LAYER_LUNARG_gfxreconstruct'])

    def __exit__(self, exc_type, exc_value, exc_tb):
        utils.set_debug_vulkan_layers(self.old_global_layers)
        utils.enable_gpu_debug_layers(self.old_enable_app_layers)
        utils.set_gpu_debug_app(self.old_app_name)
        utils.set_gpu_debug_layers(self.old_app_layers)


@click.command()
@click.argument('app_name', type=str, default='?')
@click.option('-f', '--filename', default='capture.gfxr', metavar='<trace_name>', help='Set trace name.')
@click.option('--pull', 'pull_folder', type=click.Path(), metavar='<local_folder>',
              help='Pull output files from device to <local_folder>.')
@click.option('--log', 'enable_log', is_flag=True, default=False, help='Write log messages.')
def record(app_name, filename, enable_log, pull_folder):
    """Record API trace of APP_NAME.

    \b
    APP_NAME could be set to:
        ? Select entity from prompt menu later
        ! Use last used APP_NAME
        Any other string

    \b
    >> Example 1: Launch com.foo.bar and then record a trace as test.gfxr.
    $ vk record -f test.gfxr com.foo.bar

    \b
    >> Example 2: Launch app from selection, and then record a trace as test.gfxr.
    $ vk record -f test.gfxr ?
    """
    app_name = config.get_valid_app_name(app_name)
    settings = config.GfxrConfigSettings(app_name)
    utils.stop_app(app_name)
    # utils.adb_cmd(f'shell am kill {app_name}')

    if not filename.endswith('gfxr'):
        filename = f'{filename}.gfxr'

    with RecordSession(app_name) as rec:
        settings.set_capture_options(filename, enable_log=enable_log)

        click.echo(f'Start recording {app_name}...')
        utils.create_folder_if_not_exists(settings.get_trace_folder_on_device())
        utils.start_app(app_name)
        utils.wait_until_app_launch(app_name)
        utils.wait_until_app_exit(app_name)

    click.echo('Finish recording {}'.format(settings.trace_path))

    if pull_folder:
        if not os.path.exists(pull_folder):
            os.makedirs(pull_folder)

        utils.adb_pull(settings.trace_path, pull_folder)
        if enable_log:
            utils.adb_pull(settings.log_path, pull_folder)

        click.echo(f'Finish copying output files to host: "{pull_folder}"')
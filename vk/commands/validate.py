import click
import os
import vk.config as config
import vk.utils as utils

_VALIDATION_LAYER_NAME = 'VK_LAYER_KHRONOS_validation'
_VALIDATION_LAYER_FILE_NAME = 'libVkLayer_khronos_validation.so'

class ValidationSession:

    _VK_LAYER_ENABLES = 'debug.vvl.enables'
    _VK_LAYER_DISABLES = 'debug.vvl.disables'

    def __init__(self, app_name):
        self.app_name = app_name

    def __enter__(self):
        self.old_global_layers = utils.get_debug_vulkan_layers()
        self.old_app_name = utils.get_gpu_debug_app()
        self.old_app_layers = utils.get_gpu_debug_layers()
        self.old_enable_app_layers = utils.get_enable_gpu_debug_layers()
        self.old_layer_enable_config = utils.adb_getprop(self._VK_LAYER_ENABLES)
        self.old_layer_disable_config = utils.adb_getprop(self._VK_LAYER_DISABLES)

        utils.enable_gpu_debug_layers(True)
        utils.set_debug_vulkan_layers(None)
        utils.set_gpu_debug_app(self.app_name)
        utils.set_gpu_debug_layers(self.old_app_layers + [_VALIDATION_LAYER_NAME])
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        print('Exit')
        utils.set_debug_vulkan_layers(self.old_global_layers)
        utils.enable_gpu_debug_layers(self.old_enable_app_layers)
        utils.set_gpu_debug_app(self.old_app_name)
        utils.set_gpu_debug_layers(self.old_app_layers)
        utils.adb_setprop(self._VK_LAYER_ENABLES, self.old_layer_enable_config)
        utils.adb_setprop(self._VK_LAYER_DISABLES, self.old_layer_disable_config)

    def set_validation_flags(self, check_sync, check_bp, not_check_core):
        enable_flags = []
        disable_flags = []

        if check_sync:
            enable_flags.append('VK_VALIDATION_FEATURE_ENABLE_SYNCHRONIZATION_VALIDATION_EXT')
            # Max bytes of setprop value is 92, therefore we could not disable following features at the same time.
            # disable_flags.append('VK_VALIDATION_FEATURE_DISABLE_API_PARAMETERS_EXT')
            # disable_flags.append('VK_VALIDATION_FEATURE_DISABLE_OBJECT_LIFETIMES_EXT')
            # disable_flags.append('VK_VALIDATION_FEATURE_DISABLE_CORE_CHECKS_EXT')

        if check_bp:
            enable_flags.append('VK_VALIDATION_FEATURE_ENABLE_BEST_PRACTICES_EXT:VALIDATION_CHECK_ENABLE_VENDOR_SPECIFIC_ARM')

        if not_check_core:
            disable_flags.append('VK_VALIDATION_FEATURE_DISABLE_CORE_CHECKS_EXT')

        # For non-root devices, we can't setprop without 'debug' prefix.
        # In validation layer, the property has prefix 'debug.vvl'
        # https://github.com/KhronosGroup/Vulkan-ValidationLayers/blob/27a8c7a33ab376acbcba52e0ceb8224a388ca9a7/layers/vk_layer_config.cpp#L97
        #
        # To enable configuration, we need to use 'debug.vvl.enables' instead of 'debug.vvl.VK_LAYER_ENABLE'
        # https://github.com/KhronosGroup/Vulkan-ValidationLayers/blob/27a8c7a33ab376acbcba52e0ceb8224a388ca9a7/layers/layer_options.cpp#L41
        #
        # Note: It seems vk_layer_settings.txt not supported on Android yet.
        utils.adb_setprop(self._VK_LAYER_ENABLES, ':'.join(enable_flags))
        utils.adb_setprop(self._VK_LAYER_DISABLES, ':'.join(disable_flags))


@click.command()
@click.option('--app', 'app_name', type=str, metavar='<app_name>', default='?',
              help='Target app for layer installation. Type ? for later selection.')
@click.option('-cs', '--check-sync', 'check_sync', is_flag=True, default=False, help='Check synchronization')
@click.option('-cbp', '--check-bp', 'check_bp', is_flag=True, default=False, help='Check Arm best practices')
@click.option('-nc', '--not-check-core', 'not_check_core', is_flag=True, default=False, help='Check parameter/object usage errors')
@click.option('-p', 'prompt', is_flag=True, default=False, help='Prompt to launch app manually')
def validate(app_name, check_sync, check_bp, not_check_core, prompt):
    """Validate application with validation layers.

    \b
    APP_NAME could be set to:
        ? Select entity from prompt menu later
        ! Use last used APP_NAME
        Any other string

    \b
    >> Example 1: launch com.foo.bar for regular validation.
    $ vk validate --app com.foo.bar

    \b
    >> Example 2: Launch com.foo.bar for synchronization validation.
    $ vk validate --app com.foo.bar -cs

    \b
    >> Example 3: Launch com.foo.bar for Arm best practices validation
    $ vk validate --app com.foo.bar -cbp

    \b
    >> Example 4: Manually launch and validate com.foo.bar
    $ vk validate --app com.foo.bar -p

    \f
    https://vulkan.lunarg.com/doc/view/1.3.283.0/windows/khronos_validation_layer.html
    """

    app_name = config.get_valid_app_name(app_name)

    if not utils.check_layer_in_app_folder(app_name, _VALIDATION_LAYER_FILE_NAME):
            utils.log_error(f"Can not find {_VALIDATION_LAYER_FILE_NAME} installed for {app_name}.\n"
                            "Please install the layer for the app first.")
            return

    utils.stop_app(app_name)

    with ValidationSession(app_name) as vs:
        vs.set_validation_flags(check_sync, check_bp, not_check_core)

        click.echo(f'Validating {app_name}')
        utils.unlock_device_screen()

        if not prompt:
            utils.start_app(app_name)
        else:
            click.echo(f'Please manually launch {app_name} (ctrl+c to abort)')
            click.echo('Waiting for app launch...')

        utils.wait_until_app_launch(app_name)
        click.echo(f'{app_name} is launched')
        utils.wait_until_app_exit(app_name)

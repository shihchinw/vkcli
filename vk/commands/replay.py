import click
import os
import vk.config as config
import vk.utils as utils


@click.command()
@click.argument('trace_name', type=str, default='?')
@click.option('-pf', '--pause-frame', type=int, metavar='N',
              help='Pause after replaying frame N.')
@click.option('-si', '--surface-index', default=-1, metavar='N',
              help='Restrict rendering to Nth surface object.')
@click.option('-ss', '--screenshots', 'screenshots_range', type=str, metavar='<range>',
              help='Dump screenshots for the specified frames <range>. Ex. 1,5-10')
@click.option('-sss', '--screenshot-scale', type=float, default=1.0, metavar='',
              help='Screenshot scale')
@click.option('-sspf', '--screenshot-prefix', type=str, default='screenshot',
              help='Prefix to screenshot file names')
@click.option('-sfa', '--skip-failed-allocations', is_flag=True,
              help='Skip failed allocations during capture.')
@click.option('-opc', '--omit-pipeline-cache', is_flag=True,
              help='Omit pipeline cache data.')
@click.option('--pull', 'pull_folder', type=click.Path(), metavar='<local_folder>',
              help='Pull output files from device to <local_folder>.')
def replay(trace_name, pause_frame, surface_index, screenshots_range, screenshot_scale, screenshot_prefix,
        skip_failed_allocations, omit_pipeline_cache, pull_folder):
    """Replay TRACE_NAME on device.

    \b
    TRACE_NAME supports 4 types of inputs:
    1. ? => Select package and trace file name subsequently.
    2. ! => Select trace file from last set package name
    3. package_name => select trace file name from menu.
    4. trace_file_name

    \b
    >> Example 1: Replay trace from selections.
    $ vk replay ?

    \b
    >> Example 2: Replay selected trace from repo of com.foo.bar.
    $ vk replay com.foo.bar

    \b
    >> Example 3: Replay trace with explicit name.
    $ vk replay com.foo.bar-test.gfxr

    \b
    >> Example 4: Replay trace and dump screenshots of 1st and 5-10th frames to local folder.
    $ vk replay com.foo.bar-test.gfxr -ss 1,5-10
    """

    replayer_name = 'com.lunarg.gfxreconstruct.replay'
    replayer_activity = f'{replayer_name}/android.app.NativeActivity'
    utils.stop_app(replayer_name)

    if trace_name in ['?', '!']:
        app_name = config.get_valid_app_name(trace_name)
        trace_name = app_name
    else:
        app_name = utils.extract_package_name(trace_name)

    settings = config.GfxrConfigSettings(app_name)
    if trace_name == app_name:
        # Select from list files.
        trace_list = utils.list_dir(settings.get_trace_folder_on_device())
        trace_name = utils.get_selected_item(trace_list, \
            'Available traces:', 'Please choose a trace (ctrl+c to abort)')
        trace_name = trace_name[len(app_name)+1:]  # Remove prefix package name.
        trace_path = settings.resolve_trace_path_on_device(trace_name)
    else:
        trace_name = trace_name[len(app_name)+1:]  # Remove prefix package name.
        trace_path = settings.resolve_trace_path_on_device(trace_name)
        if not utils.check_file_existence(trace_path):
            raise click.BadParameter('{} does not exist!'.format(trace_path))

    args = []
    if pause_frame:
        args.append(f'--pause-frame {pause_frame}')
    if surface_index:
        args.append(f'--surface-index {surface_index}')

    if screenshots_range:
        device_screenshot_folder = settings.get_temp_snap_folder_on_device()
        utils.create_folder_if_not_exists(device_screenshot_folder)
        args.append(f'--screenshots {screenshots_range}')
        args.append(f'--screenshot-dir {device_screenshot_folder}')
        args.append(f'--screenshot-prefix {screenshot_prefix}')
        args.append(f'--screenshot-scale {screenshot_scale}')
        args.append(f'--screenshot-format png')

    if skip_failed_allocations:
        args.append('--sfa')
    if omit_pipeline_cache:
        args.append('--opcd')

    args.append(trace_path)
    extras = "--es 'args' '{}'".format(' '.join(args))
    result = utils.start_app_activity(replayer_activity, extras)

    if 'Error:' in result:
        click.echo(result)
    elif screenshots_range:
        utils.wait_until_app_exit(replayer_name)

        if not pull_folder:
            pull_folder = f'./output/{app_name}/{trace_name}'

        if not os.path.exists(pull_folder):
            os.makedirs(pull_folder)

        utils.adb_pull(device_screenshot_folder, pull_folder)
        utils.delete_dir(device_screenshot_folder)


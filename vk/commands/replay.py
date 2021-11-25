import click
import vk.config as config
import vk.utils as utils


@click.command()
@click.argument('trace_name', type=str, default='?')
@click.option('-pf', '--pause-frame', type=int, metavar='N',
              help='Pause after replaying frame N.')
@click.option('-si', '--surface-index', default=-1, metavar='N',
              help='Restrict rendering to Nth surface object.')
@click.option('-sfa', '--skip-failed-allocations', is_flag=True,
              help='Skip failed allocations during capture.')
@click.option('-opc', '--omit-pipeline-cache', is_flag=True,
              help='Omit pipeline cache data.')
def replay(trace_name, pause_frame, surface_index,
        skip_failed_allocations, omit_pipeline_cache):
    """Replay TRACE_NAME on device.

    \b
    TRACE_NAME supports 3 types of inputs:
    1. ? => select package and trace file name subsequently.
    2. package_name => select trace file name from menu.
    3. trace_file_name

    \b
    >> Example 1: Replay trace from selections.
    $ vk replay ?

    \b
    >> Example 2: Replay selected trace from repo of com.foo.bar.
    $ vk replay com.foo.bar

    \b
    >> Example 3: Replay trace with explicit name.
    $ vk replay com.foo.bar-test.gfxr
    """

    replayer_name = 'com.lunarg.gfxreconstruct.replay'
    replayer_activity = f'{replayer_name}/android.app.NativeActivity'
    utils.stop_app(replayer_name)

    if trace_name == '?':
        app_name = utils.get_valid_app_name(trace_name)
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
    if skip_failed_allocations:
        args.append('--sfa')
    if omit_pipeline_cache:
        args.append('--opcd')

    args.append(trace_path)
    extras = "--es 'args' '{}'".format(' '.join(args))
    result = utils.start_app_activity(replayer_activity, extras)

    if 'Error:' in result:
        click.echo(result)


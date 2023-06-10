import click
import datetime
import functools
import re
import shlex
import subprocess as sp
import sys

_VERBOSE = False
_IS_WIN = 'win' in sys.platform

def set_verbosity(value):
    global _VERBOSE
    _VERBOSE = value

def is_verbose():
    return _VERBOSE

def log_error(msg):
    click.echo(f'Error: {msg}')

class FrameRange(click.ParamType):
    name = 'FrameRange'

    def convert(self, value, param, ctx):
        print(value, type(param), ctx)
        match_obj = re.match(r'([*])|(\d+)(?:-(\d+))?$', value)
        if not match_obj:
            self.fail(f'incorrect format {value}, should be (*|start[-end])')

        wildcard, start, end = match_obj.groups()
        if wildcard:
            return (-1, -1)

        start_idx = int(start)
        end_idx = int(end) if end else start_idx + 1
        if end_idx <= start_idx:
            self.fail(f'end index {end} is less than start index {start}!')

        return (start_idx, end_idx)


class ConfirmSession:

    def __init__(self, overwrite):
        self.overwrite = overwrite

    def force_overwrite(self):
        return self.overwrite

    def confirm(self, msg):
        if self.overwrite:
            return True

        value = click.prompt(msg, type=click.Choice(['y', 'n', 'all']), default='n')
        self.overwrite = (value == 'all')
        return value != 'n'


def adb_cmd(split_result=False, separator=None):
    def wrapper(func):
        @functools.wraps(func)
        def _wrapper(*args, **kwargs):
            cmd_args = func(*args, **kwargs)
            cmd = f'adb {cmd_args}'

            if _VERBOSE:
                click.echo(f'>> {cmd}')

            try:
                result = sp.check_output(shlex.split(cmd, posix='win' not in sys.platform), stderr=sp.STDOUT)
                result = result.decode('utf-8').strip('\r\n')
                if not result and split_result:
                    # When result is '' and split by separator.
                    return []
                return result.split(separator) if split_result and result else result
            except sp.CalledProcessError as e:
                msg = 'Execution failure [exit status: {}]: {}\n{}'.format(
                    e.returncode, cmd, e.output.decode('utf-8').strip('\r\n'))
                raise RuntimeError(msg)
        return _wrapper
    return wrapper

@adb_cmd()
def adb_exec(cmd):
    return cmd

@adb_cmd()
def adb_setprop(option, value):
    return f'shell setprop {option} {value}'

@adb_cmd()
def start_app_activity(app_activity, extras):
    cmd = f'am start -n {app_activity} -a android.intent.action.MAIN -c android.intent.category.LAUNCHER {extras}'
    return f'shell {cmd}' if _IS_WIN else f'shell "{cmd}"'
    # return f'shell am start -n {app_activity} -a android.intent.action.MAIN -c android.intent.category.LAUNCHER {extras}'

@adb_cmd()
def start_app(app_name):
    return f'shell monkey -p {app_name} -c android.intent.category.LAUNCHER 1'

@adb_cmd()
def stop_app(app_name):
    return f'shell am force-stop {app_name}'

@adb_cmd()
def wait_until_app_exit(app_name):
    return f'shell while [ $(pidof {app_name}) ]; do (sleep 1); done'

@adb_cmd()
def wait_until_app_launch(app_name):
    return f'shell while [ ! $(pidof {app_name}) ]; do (sleep 1); done'

@adb_cmd()
def install_apk(filepath):
    return f'install -t {filepath}'

@adb_cmd()
def adb_push(src_path, dst_path):
    dst_path = dst_path.replace('\\', '/')
    return f'push {src_path} {dst_path}'

@adb_cmd()
def adb_pull(src_path, dst_path):
    src_path = src_path.replace('\\', '/')
    return f'pull {src_path} {dst_path}'

@adb_cmd()
def copy_layer_file_to_app_folder(app_name, filename):
    return f'shell run-as {app_name} cp /data/local/tmp/{filename} .'

def check_layer_in_app_folder(app_name, filename):
    try:
        adb_exec(f'shell run-as {app_name} ls {filename}')
        return True
    except RuntimeError as e:
        return False

@adb_cmd()
def create_folder_if_not_exists(folder_path):
    return f'shell if [ ! -d {folder_path} ]; then mkdir -p {folder_path}; fi'

@adb_cmd()
def check_file_existence(filepath):
    return f'shell if [ -f {filepath} ]; then echo True; fi'

@adb_cmd(split_result=True)
def get_package_list(only_debuggable=False):
    """Return list of 3rd packages."""

    post_cmd = ''
    cmd = 'pm list packages -3 | sort | sed \'s/^package://\'{post_cmd}'

    if only_debuggable:
        # This post command is executing slowly. Can we do any better?
        post_cmd = ' | xargs -n1 sh -c \'if run-as $0 true; then echo $0; fi\' 2> /dev/null'

    cmd = cmd.format(post_cmd=post_cmd)
    return f'shell {cmd}' if _IS_WIN else f'shell "{cmd}"'

@adb_cmd(split_result=True)
def list_dir(folder_path):
    return f'shell if [ -d {folder_path} ]; then ls {folder_path}; fi'

@adb_cmd()
def set_debug_vulkan_layers(layer_names=None):
    if not layer_names:
        layer_names = []

    cmd = 'setprop debug.vulkan.layers \'{}\''.format(':'.join(layer_names))
    return f'shell {cmd}' if _IS_WIN else f'shell "{cmd}"'

@adb_cmd(split_result=True, separator=':')
def get_debug_vulkan_layers():
    return 'shell getprop debug.vulkan.layers'

@adb_cmd()
def get_debug_vulkan_layers_value():
    return 'shell getprop debug.vulkan.layers'

@adb_cmd()
def get_enable_gpu_debug_layers():
    return 'shell settings get global enable_gpu_debug_layers'

@adb_cmd()
def enable_gpu_debug_layers(enable : bool):
    return 'shell settings put global enable_gpu_debug_layers {}'.format(int(enable))

@adb_cmd()
def set_gpu_debug_app(app_name : str):
    cmd = f'settings put global gpu_debug_app \'{app_name}\''
    return f'shell {cmd}' if _IS_WIN else f'shell "{cmd}"'

@adb_cmd()
def get_gpu_debug_app():
    return f'shell settings get global gpu_debug_app'

@adb_cmd()
def set_gpu_debug_layers(layer_names=None):
    if not layer_names:
        layer_names = []

    cmd = 'settings put global gpu_debug_layers \'{}\''.format(':'.join(layer_names))
    return f'shell {cmd}' if _IS_WIN else f'shell "{cmd}"'

@adb_cmd(split_result=True, separator=':')
def get_gpu_debug_layers():
    return 'shell settings get global gpu_debug_layers'

@adb_cmd()
def get_gpu_debug_layers_value():
    return 'shell settings get global gpu_debug_layers'


def get_selected_package_name(app_list=None):
    """Prompt menu and get selected item."""
    if not app_list:
        app_list = get_package_list()

    click.echo('  No.  App')
    click.echo('─' * 80)
    for idx, pkg in enumerate(app_list, 1):
        click.echo(f'{idx: 5}  {pkg}')

    app_list_size = len(app_list)
    app_idx = -1
    while not (0 < app_idx <= app_list_size):
        app_idx = click.prompt('Please choose app package (ctrl+c to abort)', type=int)
        if not (0 < app_idx <= app_list_size):
            log_error(f'Selected index {app_idx} is out-of-range!')
        click.echo('')

    return app_list[app_idx - 1]


def get_valid_app_name(app_name: str) -> str:
    """Return valid app name.

    When app_name is '?', it will prompt a menu for selection.
    """
    app_list = get_package_list(only_debuggable=(app_name == '?'))

    if app_name == '?':
        app_name = get_selected_package_name(app_list)
    elif app_name not in app_list:
        raise click.BadParameter(f'can not find package "{app_name}" on device')

    return app_name


def get_selected_item(item_list, list_description, inquiry_message, extra_attr_list=None):
    """"Create prompt menu for item selection."""

    click.echo(list_description)
    for idx, item in enumerate(item_list, 1):
        if extra_attr_list:
            click.echo(f'{idx:02} {item} {extra_attr_list[idx - 1]}')
        else:
            click.echo(f'{idx:02} {item}')

    list_size = len(item_list)
    selected_idx = -1
    while not (0 < selected_idx <= list_size):
        selected_idx = click.prompt(inquiry_message, type=int)
        if not (0 < selected_idx <= list_size):
            click.echo(f'Selected index {selected_idx} is out-of-range!')

    return item_list[selected_idx - 1]


def get_time_str(time=None):
    if not time:
        time = datetime.datetime.now()
    return time.strftime('%m%d_%H%M%S')


def get_bak_filepath(filepath):
    return '{}.{}.bak'.format(filepath, get_time_str())


def extract_package_name(name: str) -> str:
    """Extract first four tokens as package ID.

    The package name can't contain '-'.
    """
    match_obj = re.match('^((?:[a-zA-Z]\w*[.]){1,3}[A-Za-z]\w*)', name)
    return match_obj.group(0) if match_obj else ''


def extract_trace_name(name: str) -> str:
    search_obj = re.search('-([\w.-]+)', name)
    return search_obj.group(1) if search_obj else ''
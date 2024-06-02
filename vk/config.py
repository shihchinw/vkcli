import click
import json
import os

from pkg_resources import resource_filename

import vk.utils as utils

class Settings:

    def __init__(self):
        super().__init__()
        self.filepath = resource_filename('vk', 'data/config.json')

        if os.path.exists(self.filepath):
            with open(self.filepath) as f:
                self.data = json.load(f)
        else:
            folder_path = os.path.dirname(self.filepath)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)

            self.data = {
                'app_name': None,
                'trace_name': None,
                'layerset' : {
                },
            }

        self.layer_presets = self.data.get('layerset', {})
        self.last_app_name = self.data.get('app_name', None)
        self.last_trace_name = self.data.get('trace_name', None)

    def __store(self):
        with open(self.filepath, 'w') as f:
            json.dump(self.data, f)

    def get_last_app_name(self):
        return self.last_app_name

    def set_last_app_name(self, app_name):
        self.data['app_name'] = app_name
        self.__store()

    def get_last_trace_name(self):
        return self.last_trace_name

    def set_last_trace_name(self, trace_name):
        self.data['trace_name'] = trace_name
        self.__store()

    def get_layer_preset_names(self):
        return list(self.layer_presets.keys())

    def get_layer_preset_items(self):
        return self.layer_presets.items()

    def has_layer_preset(self, name: str):
        return name in self.layer_presets

    def get_layer_preset(self, name: str):
        if name in self.layer_presets:
            return self.layer_presets[name]
        else:
            return (None, None, None)

    def set_layer_preset(self, name: str, global_layers_value: str, app_name=None, app_layers_value=''):
        self.layer_presets[name] = (global_layers_value, app_name, app_layers_value)
        self.__store()

    def delete_layer_preset(self, name: str):
        if name in self.layer_presets:
            del self.layer_presets[name]
            self.__store()
        else:
            raise click.BadParameter(f'Cannot find preset named "{name}"')

    def show_layers(self, show_indices=True):
        name_col_width = 10
        app_col_width = 10

        # Compute the column width.
        for preset_name, (_, app_name, _) in self.layer_presets.items():
            name_col_width = max(len(preset_name), name_col_width)
            if app_name:
                app_col_width = max(len(app_name), app_col_width)

        index_column = '  No. ' if show_indices else ''
        click.echo(f'{index_column}{"Name": <{name_col_width}}  {"App": <{app_col_width}}  Layers')
        click.echo('─' * 80)
        for idx, (preset_name, preset_value) in enumerate(self.layer_presets.items(), 1):
            global_layers_value, app_name, app_layers_value = preset_value
            index_column = f'{idx: 5}  ' if show_indices else ''
            click.echo(f'{index_column}{preset_name: <{name_col_width}}  {"*": <{app_col_width}}  {global_layers_value}')
            if app_name:
                name_col_spaces = ' ' * name_col_width
                index_column_spaces = ' ' * 7 if show_indices else ''
                click.echo(f'{index_column_spaces}{name_col_spaces}  {app_name: <{app_col_width}}  {app_layers_value}')

class GfxrConfigSettings:

    root_trace_folder = '/sdcard/vk_trace_repo'
    root_snap_folder = '/sdcard/vk_snap_repo'

    @classmethod
    def get_root_trace_folder(cls):
        return cls.root_trace_folder

    def __init__(self, app_name) -> None:
        self.app_name = app_name

        self.trace_folder = f'{self.root_trace_folder}/{app_name}'
        self.trace_path = None
        self.log_path = None

    def resolve_trace_path_on_device(self, filename):
        # Since package name can't contain '-', we use it to separate package name and filename.
        return f'{self.trace_folder}/{self.app_name}-{filename}'

    def get_temp_snap_folder_on_device(self):
        time_str = utils.get_time_str()
        return f'{self.root_snap_folder}/{time_str}'

    def get_trace_path_on_device(self, filename):
        return f'{self.trace_folder}/{filename}'

    def get_trace_folder_on_device(self):
        return self.trace_folder

    def extract_trace_capture_tag(self, filepath):
        """Extract capture tag from trace name.

        Let <trace_name> be <app_name>-<capture_tag>.
        If <trace_name> is 'com.khronos.vulkan_samples-test1-tag.gfxr', then the <capture_tag> is 'test1-tag.gfxr'.
        """
        filename = os.path.basename(filepath)
        return utils.extract_trace_capture_tag(filename)

    def get_temp_filepath_on_device(self, name, ext):
        time_str = utils.get_time_str()
        return f'/sdcard/{name}_{time_str}{ext}'

    def set_capture_options(self, filename, frames=None, enable_log=False):
        filepath_on_device = self.resolve_trace_path_on_device(filename)
        if utils.check_file_existence(filepath_on_device):
            if not click.confirm(f'Override existent trace {filepath_on_device}?'):
                raise click.Abort

        self.trace_path = filepath_on_device
        utils.adb_setprop('debug.gfxrecon.capture_file', filepath_on_device)

        # We use '-' to separate prefix package name from filename. When we enable timestamp,
        # the timestamp would make output filename violate our naming convention. Thus we disable
        # adding timestamp to filename.
        utils.adb_setprop('debug.gfxrecon.capture_file_timestamp', False)

        if frames:
            utils.adb_setprop('debug.gfxrecon.capture_frames', frames)

        if enable_log:
            self.log_path = f'{filepath_on_device}.log'
            utils.adb_setprop('debug.gfxrecon.log_file', self.log_path)


def get_valid_app_name(app_name: str):
    settings = Settings()

    if app_name == '!':
        last_app_name = settings.get_last_app_name()
        app_name = last_app_name if last_app_name else '?'

    app_name = utils.get_valid_app_name(app_name)
    settings.set_last_app_name(app_name)
    click.echo(f'Valid app name: {app_name}')
    return app_name

def get_last_trace_name():
    settings = Settings()
    trace_name = settings.get_last_trace_name()
    if not trace_name:
        raise click.BadParameter('Can not find last used trace_name')

    return trace_name

def set_last_trace_name(trace_name: str):
    settings = Settings()
    settings.set_last_trace_name(trace_name)
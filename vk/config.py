import click
import json
import os
import re

from click.exceptions import Abort, BadArgumentUsage, BadParameter

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
            self.data = {
                'layerset' : {
                }
            }

        self.layer_presets = self.data['layerset']

    def __store(self):
        with open(self.filepath, 'w') as f:
            json.dump(self.data, f)

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
            raise BadParameter(f'Cannot find preset named "{name}"')

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
        self.snap_folder = f'{self.root_snap_folder}/{app_name}'
        self.trace_path = None
        self.log_path = None

    def resolve_trace_path_on_device(self, filename):
        # Since package name can't contain '-', we use it to sepearate package name and filename.
        return f'{self.trace_folder}/{self.app_name}-{filename}'

    def get_trace_path_on_device(self, filename):
        return f'{self.trace_folder}/{filename}'

    def get_trace_folder_on_device(self):
        return self.trace_folder

    def extract_trace_filename(self, filepath):
        filename = os.path.basename(filepath)
        return utils.extract_trace_name(filename)

    def set_capture_options(self, filename, frames=None, enable_log=False):
        filepath_on_device = self.resolve_trace_path_on_device(filename)
        if utils.check_file_existence(filepath_on_device):
            if not click.confirm(f'Override existent trace {filepath_on_device}?'):
                raise Abort

        self.trace_path = filepath_on_device
        utils.adb_setprop('debug.gfxrecon.capture_file', filepath_on_device)

        # We use '-' to sepearate prefix package name from fileaname. When we enable timestamp,
        # the timestamp would make output filename violate our naming convention. Thus we disable
        # adding timestamp to filename.
        utils.adb_setprop('debug.gfxrecon.capture_file_timestamp', False)

        if frames:
            utils.adb_setprop('debug.gfxrecon.capture_frames', frames)

        if enable_log:
            self.log_path = f'{filepath_on_device}.log'
            utils.adb_setprop('debug.gfxrecon.log_file', self.log_path)

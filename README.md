# vkcli

![layer_config](/docs/images/layer_config.gif)

## Introduction
vkcli is a handy command line interface for Vulkan configuration on Android. It allows you easily configure Vulkan layer settings and define your own layer presets. Additionally, it also provides commands to record/replay/push/pull API traces.

## Usage

```
Usage: vk [OPTIONS] COMMAND [ARGS]...

Commands:
  dump-api  Dump API log with VK_LAYER_LUNARG_api_dump.
  install   Install layers to device.
  layer     Configure active layer settings.
  layerset  Customize layer presets.
  pull      Pull traces from device.
  push      Push traces to device.
  query     Query device info related to apps, traces, layers, etc.
  record    Record API trace of APP_NAME.
  replay    Replay TRACE_NAME on device.
```

To query detailed description of each command (i.e. install, layer, etc.), please append `--help` option:

```
$ vk command --help
```

## Documentation

See the [tutorial](docs/tutorial.md) for setup and usage instructions.

## Develop

1. Clone repository and create a virtual environment for development.

    ```
    $ git clone https://github.com/shihchinw/vkcli.git
    $ cd vkcli
    $ python -m venv vkcli-env
    ```

2. Activate virtual environment on Windows:

    ```
    $ vkcli-env\Scripts\activate.bat
    ```

    on Linux or MacOS:

    ```
    $ source vkcli-env/bin/activate
    ```

3. Install required packages.

   ```
   $ pip install -r requirements.txt
   ```

4. Install project in develop mode.

    ```
    $ pip install -e .
    ```

The implementation of each comand is located in **vk/commands**. You can easily examine the corresponding implementation details from each script.


## Test

Before executing all test cases, please ensure your phone is connected and USB debugging is enabled. Then launch `pytest` to execute all **tests/test_*.py**

```
$ pytest
```

## Build

vkcli is distributed as a wheel by executing build.bat or:

```
$ python setup.py bdist_wheel
```

Then you will see `vkcli-x.x.x-py3-none-any.whl` in **dist** folder.

# Prerequisites

* [Python 3.x](https://www.python.org/downloads/)
* [GFXReconstruct](https://github.com/LunarG/gfxreconstruct/releases) for `record`, `replay`
* [LunarG/VulkanTools](https://github.com/LunarG/VulkanTools): VK_LAYER_LUNARG_api_dump, VK_LAYER_LUNARG_screenshot for `dump-api`, `dump-img`
* [Vulkan-ValidationLayers](https://github.com/KhronosGroup/Vulkan-ValidationLayers): VK_LAYER_KHRONOS_validation for `validate`

# Installation

## vkcli

Download pre-built package [here](https://github.com/shihchinw/vkcli/releases), and install with `pip`:

```
pip install vkcli-x.x.x-py3-none-any.whl
```

## Layers

vkcli uses **GFXReconstruct** to record and replay API traces. The easiest way for setup is to download pre-built android tools **gfxreconstruct-vx.x.x-android.zip** from the [release page](https://github.com/LunarG/gfxreconstruct/releases) of GFXReconstruct, and use `vk install --app ?` to select target package base directory for layer installation.

```
$ cd <gfxreconstruct-vx.x.x>
$ adb install tools\replay-debug.apk

$ vk install --app ? layer\arm64-v8a
Found layers:
.\layer\arm64-v8a\libVkLayer_gfxreconstruct.so

  No.  App
────────────────────────────────────────────────────────────────────────────────
    1  com.khronos.vulkan_samples
    2  com.lunarg.gfxreconstruct.replay
Please choose app package (ctrl+c to abort): 1

Valid app name: com.khronos.vulkan_samples
Install layers to 'com.khronos.vulkan_samples' successfully.
```

Likewise, before using dump commands, we need to install VK_LAYER_LUNARG_api_dump and VK_LAYER_LUNARG_screenshot layers. We could [build from source](https://github.com/LunarG/VulkanTools/blob/main/BUILD.md) or download pre-built *.so from [release page](https://github.com/shihchinw/vkcli/releases) of vkcli.

```
$ vk install --app ? <folder_of_layers>
Found layers:
<folder_of_layers>\libVkLayer_api_dump.so
<folder_of_layers>\libVkLayer_screenshot.so

  No.  App
────────────────────────────────────────────────────────────────────────────────
    1  com.khronos.vulkan_samples
    2  com.lunarg.gfxreconstruct.replay
Please choose app package (ctrl+c to abort): 1

Valid app name: com.khronos.vulkan_samples
Install layers to 'com.khronos.vulkan_samples' successfully.
```

> For other useful layers, please refer to [LunarG/VulkanTools.](https://github.com/LunarG/VulkanTools)

# General Tips
## Alias for Application Name (?, !)

To save keystrokes for specifying application name, we could use:
* `?` to select entity from installed packages
* `!` for last specified app name

# Record API Trace

To record a trace from application `com.foo.bar` and save file as `test.gfxr` is straightforward as follows:

```
$ vk record -f test.gfxr com.foo.bar
```

You can also specify `?` for application name, it will prompt a menu for app selection.

```
$ vk record -f test.gfxr ?

  No.  App
────────────────────────────────────────────────────────────────────────────────
    1  com.khronos.vulkan_samples
    2  com.lunarg.gfxreconstruct.replay
Please choose app package (ctrl+c to abort): 1
# Launch com.khronos.vulkan_samples for API recording.

Start recording com.khronos.vulkan_samples...

# Just interact with the application and close it when finishing.

Finish recording /sdcard/vk_trace_repo/com.khronos.vulkan_samples/com.khronos.vulkan_samples-test.gfxr
```

## Trace Repository on Device: `/sdcard/vk_trace_repo/<package_name>`

The naming convention of each trace file is `<package_name>-<trace_name>.gfxr`. This is designed for deriving respective package name from each trace name, and then store the trace file in `/sdcard/vk_trace_repo/<package_name>` on device.

### Push Trace File

Unsurprisingly, when we use `vk push <trace_name>` to push a trace file to device, the `<trace_name>` should follow the `<package_name>-<trace_name>.gfxr` naming convention.

```
$ vk push com.khronos.vulkan_samples-test.gfxr
```

### Pull Trace File(s)

To pull a trace from connected device, you could easily select the trace file from a prompt menu by using `?`:

```
$ vk pull ?
 No.  App
────────────────────────────────────────────────────────────────────────────────
    1  com.khronos.vulkan_samples
    2  com.lunarg.gfxreconstruct.replay
Please choose app package (ctrl+c to abort): 1    # First, select the package.

Trace files:
01 com.khronos.vulkan_samples-capture.gfxr
02 com.khronos.vulkan_samples-test.gfxr
Please select a trace: 2    # Secondly, select a trace recorded from specified package.

Copying /sdcard/vk_trace_repo/com.khronos.vulkan_samples/com.khronos.vulkan_samples-test.gfxr to ./output
```

You can also pull **all** traces recorded from `com.foo.bar` on device at once:

```
$ vk pull com.foo.bar
```

# Replay API Trace

The simplest way for trace replay is to use `?` to invoke option menu:

```
$ vk replay ?
  No.  App
────────────────────────────────────────────────────────────────────────────────
    1  com.khronos.vulkan_samples
    2  com.lunarg.gfxreconstruct.replay
Please choose app package (ctrl+c to abort): 1    # First, select the package.
Available traces:
01 com.khronos.vulkan_samples-capture.gfxr
02 com.khronos.vulkan_samples-test.gfxr
Please choose a trace (ctrl+c to abort): 2        # Second, select a trace from package's trace repo.
```

Definitely, you could explicitly specify the package name:

```
$ vk replay com.khronos.vulkan_samples
Available traces:
01 com.khronos.vulkan_samples-capture.gfxr
02 com.khronos.vulkan_samples-test.gfxr
Please choose a trace (ctrl+c to abort): 2
```

or the full trace name:

```
$ vk replay com.khronos.vulkan_samples-test.gfxr
```

# Configure Layer Settings

Vulkan layers could be enabled **per-app or globally** outside the application [on Android](https://developer.android.com/ndk/guides/graphics/validation-layer#enable-layers-outside-app). However, it is a little tedious to configure layer settings through a couple of adb shell settings each time. With `vk layer`, you could easily add/remove layers to per-app or global settings. Moreover, you could even define your own layer presets with `vk layerset` and switch preset in one shot.

## Query Active Layer States

Current layer configuration could be queried by:

```
$ vk query --layer
VK_LAYER_foo (global)
VK_LAYER_bar (com.khronos.vulkan_samples)
```

If you want to query detailed settings, just append `--detailed` option:

```
$ vk query --layer --detailed
debug.vulkan.layers: VK_LAYER_foo
enable_gpu_debug_layers: 1
gpu_debug_app: com.khronos.vulkan_samples
gpu_debug_layers: VK_LAYER_bar
```

## Add, Remove, and Clear Layers

Layer list for add and remove instructions should be specified as `layer1:layer2:layerN`. For example, here is how to add/remove layers globally:

```
$ vk layer --add VK_LAYER_foo:VK_LAYER_bar
Successfully update active layers:
VK_LAYER_foo:VK_LAYER_bar (global)
none ()

$ vk layer --remove VK_LAYER_foo
Successfully update active layers:
VK_LAYER_bar (global)
none ()
```

To manipulate per-app layer settings, just append `--app` option:

```
$ vk layer --add VK_LAYER_foo --app ?
 No.  App
────────────────────────────────────────────────────────────────────────────────
    1  com.khronos.vulkan_samples
    2  com.lunarg.gfxreconstruct.replay
Please choose app package (ctrl+c to abort): 1    # Select from app menu

Successfully update active layers:
VK_LAYER_bar (global)
VK_LAYER_foo (com.khronos.vulkan_samples)
```

> Per-app settings **persist** across reboots, while global properties are **cleared** on reboot.

Finally, it's straightforward to clear all (per-app and global) layer settings by using `--clear` option (which can **not** be used with `--add` simultaneously.)

## Utilize Layer Presets

Current per-app and global layer settings could be saved to a preset with `vk layerset --save`:

```
$ vk layerset --save foobar
Save preset 'foobar' successfully.
VK_LAYER_foo:VK_LAYER_bar (global)
none ()
```

> Layer presets are saved in `<vkcli_package_folder>/vk/data/config.json`.

By contrast, `vk layerset --load foobar` applies preset to current layer configuration and `vk query --layerset` shows all presets stored on local host:

```
$ vk query --layerset
  No. Name        App                         Layers
────────────────────────────────────────────────────────────────────────────────
    1  foobar      *                           VK_LAYER_foo:VK_LAYER_bar
    2  snap        *
                   com.khronos.vulkan_samples  VK_LAYER_screenshot
```

# Dump API Log or Screenshots

API log and screenshots are very useful for application debugging. To make VK_LAYER_LUNARG_api_dump, VK_LAYER_LUNARG_screenshot layers easy to use via command line, `dump-api` and `dump-img` would properly setup layer and pull results from device at the end of execution.

```
$ vk dump-api --app !  # Use alias of last specified app_name.
Valid app name: com.khronos.vulkan_samples
Start dumping API (range=0-0) to /sdcard/Android/vk_apidump_0611_081722.log
Want to Stop or Stop-and-Pull (s/sp)? sp

Copying /sdcard/Android/vk_apidump_0611_081722.log to ./output
/sdcard/Android/vk_apidump_0611_081722.log has been deleted on device.
```

It's quite similarly for `dump-img` to dump screenshots. Here we show how to specify `--range 10-5-3` to
* start at frame 10
* dump 5 screenshots
* every 3 frames

```
$ vk dump-img --app ! --range 10-5-3  # Use alias of last specified app_name.
Valid app name: com.khronos.vulkan_samples
Start dumping screenshots (range [start-count-step]=10-5-3) to /sdcard/Android/vkcli/screenshot_0611_082749
Want to Stop or Stop-and-Pull (s/sp)? sp  # Once we are done, key in sp to pull results.

Copying /sdcard/Android/vkcli/screenshot_0611_082749 to ./output
/sdcard/Android/vkcli/screenshot_0611_082749 has been deleted on device.

$ ls ./output/screenshot_0611_082749
10.ppm  13.ppm
```

# Validate APP

[VK_LAYER_KHRONOS_validation](https://vulkan.lunarg.com/doc/view/latest/windows/khronos_validation_layer.html) is a great tool to check incorrect API usage, synchronization hazards, and find out common misuse of API which might hurt performance. However, it's tedious and error-prone to configure layer options on Android. With `validate`, we could easily apply following validations:
* Regular validation
* Synchronization validation
* Arm best-practices validation

```
$ vk validate --app com.foo.bar  # Launch com.foo.bar and then execute regular validation.

$ vk validate --app com.foo.bar --check-sync # Launch com.foo.bar and apply synchronization validation.

$ vk validate --app com.foo.bar --check-bp # Launch app and apply Arm best-practices validation.
```

## Troubleshooting: Layer Not Found

If vkcli found there is no installed layer for corresponding dump command, it would prompt `layer not found` error. Please follow the [instructions](#layers) of layer installation to resolve the error.

```
$ vk dump-api --app ? --range 10-5-3
  No.  App
────────────────────────────────────────────────────────────────────────────────
    1  com.khronos.vulkan_samples
    2  com.foo.bar
Please choose app package (ctrl+c to abort): 2

Valid app name: com.foo.bar
Error: Can not find 'libVkLayer_api_dump.so' installed for com.foo.bar.
Please install the layer for the app first.
```

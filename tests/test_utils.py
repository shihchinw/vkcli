import vk.utils as utils

def test_extract_package_name():
    name = 'com.khronos.vulkan_samples-test1-tag.gfxr'
    app_name = utils.extract_package_name(name)
    assert app_name == 'com.khronos.vulkan_samples'

def test_extract_trace_name():
    name = 'com.khronos.vulkan_samples-test1-tag.gfxr'
    trace_name = utils.extract_trace_name(name)
    assert trace_name == 'test1-tag.gfxr'
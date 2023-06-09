from subprocess import run
from click.testing import CliRunner

from vk.commands.push import push
from vk.commands.query import query
from vk.commands.layer import layer, layerset

import pytest

@pytest.fixture(scope="module")
def runner():
    return CliRunner()


def test_query(runner):
    result = runner.invoke(query, ['--app'])
    assert result.exit_code == 0


def test_layer_manipulation(runner):
    result = runner.invoke(layer, ['--clear'])
    assert result.exit_code == 0

    result = runner.invoke(query, ['--layer'])
    truth = 'none (global)\nnone ()\n'
    assert result.output == truth

    result = runner.invoke(layer, ['--add', 'VK_LAYER_foo:VK_LAYER_bar'])
    assert result.exit_code == 0

    result = runner.invoke(query, ['--layer'])
    truth = 'VK_LAYER_foo:VK_LAYER_bar (global)\nnone ()\n'
    assert result.output == truth

    result = runner.invoke(layer, ['--remove', 'VK_LAYER_foo'])
    assert result.exit_code == 0

    result = runner.invoke(query, ['--layer'])
    truth = 'VK_LAYER_bar (global)\nnone ()\n'
    assert result.output == truth

    result = runner.invoke(layer, ['--set', 'VK_LAYER_foobar'])
    assert result.exit_code == 0

    result = runner.invoke(query, ['--layer'])
    truth = 'VK_LAYER_foobar (global)\nnone ()\n'
    assert result.output == truth


def test_layer_preset(runner):
    result = runner.invoke(layer, ['--clear'])
    assert result.exit_code == 0

    result = runner.invoke(layer, ['--add', 'VK_LAYER_foo:VK_LAYER_bar'])
    assert result.exit_code == 0

    result = runner.invoke(layerset, ['--save', 'test'])
    assert result.exit_code == 0

    runner.invoke(layer, ['--clear'])
    result = runner.invoke(layerset, ['--load', 'test'])
    assert result.exit_code == 0

    result = runner.invoke(query, ['--layer'])
    truth = 'VK_LAYER_foo:VK_LAYER_bar (global)\nnone ()\n'
    assert result.output == truth

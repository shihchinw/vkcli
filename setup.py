from setuptools import setup, find_packages

setup(
    name='vkcli',
    version='0.2.4',
    description='Command line tool for Vulkan configuration on Android',
    author='Shih-Chin Weng',
    author_email='shihchin.weng@gmail.com',
    py_modules=['vk'],
    install_requires=[
        'Click',
    ],
    packages=find_packages(include=['vk', 'vk.*']),
    entry_points={
        'console_scripts': [
            'vk = vk.cli:main',
        ],
    },
)
from setuptools import setup, find_packages
import os

# 读取版本信息
about = {}
with open(os.path.join('src', '__init__.py'), 'r', encoding='utf-8') as f:
    exec(f.read(), about)

setup(
    name=about['__app_name__'],
    version=about['__version__'],
    packages=find_packages(),
    install_requires=[
        "opencv-python",
        "numpy",
        "PyQt5",
        "mss",
        "keyboard",
        "pywin32",
    ],
    python_requires=">=3.7",
    author=about['__author__'],
    author_email=about['__email__'],
    description=about['__app_name__'],
    url=about['__github__'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: Windows",
    ],
    entry_points={
        'console_scripts': [
            f'{about["__app_name__"]}=src.main:main',
        ],
    },
)
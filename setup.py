from setuptools import setup, find_packages

setup(
    name="Logitech_Assistant",
    version="1.0.0",
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
    author="DTer1999",
    description="PUBG Assistant",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: Windows",
    ],
    entry_points={
        'console_scripts': [
            'pubg_assistant=src.main:main',
        ],
    },
)
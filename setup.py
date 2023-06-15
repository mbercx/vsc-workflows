from setuptools import setup, find_packages

setup(
    name="vsc_workflows",
    version="0.1.0",
    author="Marnik Bercx",
    packages=find_packages(where=".", exclude="docs"),
    install_requires=[
        "numpy",
        "pymatgen",
        "custodian",
        "fireworks",
        "atomate",
        "dnspython",
        "click",
        "monty",
        "tabulate"
    ],
    entry_points='''
        [console_scripts]
        vsc=vscworkflows.cli:main
    '''
)

from setuptools import setup, find_packages

setup(
    name='aras',
    version='0.1',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'flask',
        'flask_sqlalchemy',
        'flask_mail',
        'flask_celery',
        'redis',
        'mariadb+mariadbconnector',
        'python-dotenv',
        'logging',
    ],
    entry_points={
        'console_scripts': [
            'aras = arasCore.lib.bin:main',
        ],
    },
)

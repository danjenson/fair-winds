import setuptools

setuptools.setup(
    name='fair-winds',
    version='0.0.1',
    author='Daniel Jenson',
    author_email='daniel.a.jenson@gmail.com',
    description='software for sailing',
    license='GNU GPLv3',
    platform='OS Independent',
    url='https://github.com/danjenson/fair-winds',
    packages=setuptools.find_packages(),
    package_data={
        'wifi_selector': ['*', 'static/*', 'templates/*'],
    },
    scripts=[
        'scripts/wifi-selector',
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.9',
    install_requires=[
        'Jinja2==3.0.1',
        'aiofiles==0.7.0',
        'fastapi==0.68.2',
        'python-dotenv==0.19.0',
        'python-multipart==0.0.5',
        'python-networkmanager==2.2',
        'uvicorn==0.15.0',
    ],
)

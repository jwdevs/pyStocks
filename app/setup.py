from setuptools import setup, find_packages

setup(
    name='pyStocks',
    version='0.1.0',
    package_dir={'':'src'},
    packages=find_packages(where='./src'),
    url='',
    license='',
    author='jwozniak',
    author_email='jakubwozniak@gmail.com',
    description='',
    install_requires=['backtrader>=1.9.54.122', 'requests', 'matplotlib'],
    entry_points={
        'console_scripts': [
            'pyStocks = run:run'
        ]
    }
)
    
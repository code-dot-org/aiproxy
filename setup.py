from setuptools import setup, find_packages

setup(
    name='aiproxy',
    version='0.1',
    packages=find_packages(),
    install_requires=[line.strip() for line in open('requirements.txt')],
    entry_points={
        'console_scripts': [
          'rubric_tester=aiproxy.assessment.rubric_tester:main',
          'aiproxy=aiproxy.app:create_app',
        ]
    },
)

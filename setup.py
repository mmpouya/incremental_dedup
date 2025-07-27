from setuptools import setup, find_packages

setup(
    name='incremental_dedup',
    version='0.1.02',
    packages=find_packages(),
    install_requires=open('requirements.txt').read().splitlines(),
    author='Givechi',
    author_email='mmpouya.github.com',
    description='Incremental Deduplication using Clustering and Vector Operations.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://git.t.etratnet.ir/AI/incremental_dedup',
)
from setuptools import setup

setup(name='ooc',
      version='0.1',
      description='Out of control: Simplify probabilistic models by control-state reduction',
      url='http://github.com/towink/out-of-control',
      author='Tobias Winkler',
      author_email='tobias.winkler@cs.rwth-aachen.de',
      license='',
      packages=[
            'ooc',
            'ooc.benchmarks',
            'ooc.datastructures',
            'ooc.interactive',
            'ooc.models',
            'ooc.tests'
      ],
      include_package_data=True,
      zip_safe=False)

from setuptools import find_packages, setup


setup(
  name='RuestViewer',
  version='1.0.0',
  description='GUI to view the RuestMatrix',
  url='https://github.com/nejox/OberAGui',
  author='Jochen Schmidt',
  author_email='schmidtjochen@gmx.net',
  package_data={  # Optional
        'data': ['exampleData.csv'],
        'settings':['settings.json', 'defaultValues.csv'],
    },
  packages=setuptools.find_packages(where="src"),
  install_requires=[
    'matplotlib',
    'numpy',
    'pandas',
    'PySimpleGUI'
  ]
)
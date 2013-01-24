from setuptools import setup
import wpsutils

setup(
    name = "wpsutils",
    version = wpsutils.__version__,
    description = open("README", 'r').read(),
    url = "",
    author="Roberto Bampi",
    author_email="robampi@fbk.eu",
    packages = [
        "wpsutils"
    ],
    classifiers = [
        'Programming Language :: Python',
        #'License :: OSI Approved :: GPL License',
        'Operating System :: OS Indipendent',
        'Framework :: Django',
    ],
    requires = [
        'jsonfield',
        'pytz',
    ],
    dependency_links = [
        'https://github.com/davidek/django-tojson.git#egg=tojson',
    ]
)



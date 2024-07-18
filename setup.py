import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pymolekule",
    version="0.0.2",
    author="Anthony Da Mota",
    author_email="anthony@damota.me",
    description="Unofficial Molekule API Python library",
    license="https://www.fsf.org/licensing/licenses/agpl-3.0.html",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/AkdM/PyMolekule",
    project_urls={
        "Bug Tracker": "https://github.com/AkdM/PyMolekule/issues"
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Operating System :: OS Independent"
    ],
    install_requires=[
        'requests',
        'boto3',
        'pycognito',
        'loguru',
        'pyjwt',
        'pydantic'
    ],
    packages=setuptools.find_packages(exclude=["test*"]),
    python_requires=">=3.6"
)

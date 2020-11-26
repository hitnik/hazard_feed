import setuptools
try: # for pip >= 10
    from pip._internal.req import parse_requirements
except ImportError: # for pip <= 9.0.3
    from pip.req import parse_requirements


with open("README.md", "r") as fh:
    long_description = fh.read()

install_reqs = parse_requirements('./requirements.txt', session='hack')


try:
    reqs = [str(ir.req) for ir in install_reqs]
except:
    reqs = [str(ir.requirement) for ir in install_reqs]

setuptools.setup(
    name="hazard-feed",
    version="0.1.7.1",
    author="Aleksandr Nikitin",
    author_email="hitnik@gmail.com",
    description="pogoda.by storm warning rss parser",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hitnik/hazard_feed",
    packages=setuptools.find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
    install_requires=reqs,
)
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
import os.path

setup(
    version = "1.1.3",
    name = "keepTrace",
    author = "Jason Dixon",
    packages = ["keepTrace"],
    author_email = "jason.dixon.email@gmail.com",
    long_description_content_type = "text/markdown",
    url = "https://github.com/internetimagery/keepTrace",
    description = "Pickle traceback support. Featuring debuggable restored tracebacks.",
    long_description = open(os.path.join(os.path.dirname(__file__), "README.md")).read())

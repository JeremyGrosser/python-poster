from setuptools import setup, find_packages
from distutils.cmd import Command
import poster

# To update version number, edit:
# poster/__init__.py
# docs/index.rst
version = ".".join(str(x) for x in poster.version)

class sphinx_command(Command):
    description = "rebuild sphinx docs"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import sphinx, shutil, os
        if os.path.exists("docs/build/html"):
            shutil.rmtree("docs/build/html")

        self.mkpath("docs/build/html")

        sphinx.main(["-E", "docs", "docs/build/html"])

setup(name='poster',
      version=version,
      description="Streaming HTTP uploads and multipart/form-data encoding",
      long_description="""\
The modules in the Python standard library don't provide a way to upload large
files via HTTP without having to load the entire file into memory first.

poster provides support for both streaming POST requests as well as
multipart/form-data encoding of string or file parameters""",
      classifiers=[
          "Intended Audience :: Developers",
          "License :: OSI Approved :: MIT License",
          "Natural Language :: English",
          "Programming Language :: Python",
          "Topic :: Internet :: WWW/HTTP",
          "Topic :: Software Development :: Libraries :: Python Modules",
          ],
      keywords='python http post multipart/form-data file upload',
      author='Chris AtLee',
      author_email='chris@atlee.ca',
      url='http://atlee.ca/software/poster',
      download_url='http://atlee.ca/software/poster/dist/%s' % version,
      license='MIT',
      packages=find_packages(exclude='tests'),
      include_package_data=True,
      zip_safe=True,
      extras_require = {'poster': ["buildutils", "sphinx"]},
      tests_require = ["nose", "webob", "paste"],
      test_suite = 'nose.collector',
      #entry_points="",
      cmdclass={'sphinx': sphinx_command},
      )

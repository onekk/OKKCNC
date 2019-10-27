from setuptools import setup, find_packages

print("Running OKKCNC setup...")

with open("README.md", "r") as fh:
	long_description = fh.read()

setup(
	name = "OKKCNC",
	version = "0.0.9.00",
	license="GPLv2",
	description='Swiss army knife for all your CNC/g-code needs',
	long_description=long_description,
	long_description_content_type="text/markdown",
	packages = find_packages(),
	author = 'Carlo Dormeletti',
	author_email='carlo.dormeletti@gmail.com',
	url="https://github.com/onekk/OKKCNC",
	include_package_data=True,
	python_requires="<3.0",
	install_requires = [
		"pyserial ; sys_platform != 'win32'",	#Windows XP can't handle pyserial newer than 3.0.1 (it can be installed, but does not work)
		"pyserial<=3.0.1 ; sys_platform == 'win32'",
		'numpy>=1.12',
		'Pillow>=4.0',
		'opencv-python>=2.4 ; ("arm" not in platform_machine) and ("aarch64" not in platform_machine)',	#Note there are no PyPI OpenCV packages for ARM (Raspberry PI, Orange PI, etc...)
	],

	entry_points = {
		'console_scripts': [
			#'OKKCNC = {package}.{module}:{main_function}',
			#'OKKCNC = OKKCNC.OKKCNC:main',
			'OKKCNC = OKKCNC.__main__:main',
		]
	},

	classifiers=[
		"Development Status :: 4 - Beta",
		"License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
		"Operating System :: OS Independent",
		"Topic :: Multimedia :: Graphics :: 3D Modeling",
		"Topic :: Multimedia :: Graphics :: Capture",
		"Topic :: Multimedia :: Graphics :: Editors :: Vector-Based",
		"Topic :: Multimedia :: Graphics :: Graphics Conversion",
		"Topic :: Multimedia :: Graphics :: Viewers",
		"Topic :: Scientific/Engineering",
		"Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)",
		"Topic :: Terminals :: Serial",
		"Natural Language :: English",
		"Natural Language :: Italian",
	]
)

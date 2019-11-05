#!/usr/bin/python2

import os
import sys

def delete_py(path, subfolder):
    try:
        for root, dirs, files in os.walk(path):
            if subfolder in root.split(os.sep):
                # has subfolder as a directory name in the path, delete .py files here
                for file in files:
                    if file == '__init__.py':
                        continue
                    if file.endswith(('.pyc')):
                        os.unlink(os.path.join(root, file))
    except:
        print('Unable to delete files')


if __name__ == "__main__":
    current = os.getcwd()
    delete_py(current, 'OKKCNC')

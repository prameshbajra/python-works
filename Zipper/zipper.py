import sys
import os
import zipfile

if len(sys.argv) > 1:
    folder_name = sys.argv[1]
    folder_path = os.path.realpath(folder_name)
    print("Folder selected :: " + folder_name)
    print("Path of the folder :: " + folder_path)
    zipfile_name = ""
    if len(sys.argv) > 2:
        zipfile_name = sys.argv[2]
        print("Zipped folder name :: " + zipfile_name)

    if len(zipfile_name) > 0:
        zipfilehandler = zipfile.ZipFile(zipfile_name + ".zip", "w")
    else:
        zipfilehandler = zipfile.ZipFile(
            "Zipped_" + folder_name + ".zip", "w")
    for root_files, dirs, files in os.walk(folder_name):
        zipfilehandler.write(root_files)
        for file in files:
            zipfilehandler.write(os.path.join(root_files,  file))

    zipfilehandler.close()

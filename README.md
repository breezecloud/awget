# awget
usage: awget.py [-h] [-o OUTPUT] [-d DIRECTORY] [-u USER] [-p PASSWORD] [-s] [-v] url

Pure python download utility,refer to https://pypi.org/project/wget/. The difference is this script can batch download
of files listed based on a certain URL,also can download single file. "awget -h" for usage. You can press Ctrl+C break
download.
# usage
positional arguments:
  url                   URL
options:
  -h, --help   show this help message and exit
  -o OUTPUT, --output OUTPUT Save the file as OUTPUT
  -d DIRECTORY, --directory DIRECTORY Save the file to the directory DIRECTORY/
  -u USER, --user USER  http Authentication username
  -p PASSWORD, --password PASSWORD    http Authenticate Password
  -s, --skip      Skip file if it already exists in the target directory跳过文件如果目标目录已经存在该文件
  -v, --version    version
# Third party libraries
all os:requests,PyQuery
windows os:win32api,win32con

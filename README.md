# awget
usage: awget.py [-h] [-o OUTPUT] [-d DIRECTORY] [-u USER] [-p PASSWORD] [-s] [-v] url<br/>
Pure python download utility,refer to https://pypi.org/project/wget/. The difference is this script can batch download of files listed based on a certain URL,also can download single file. "awget -h" for usage. You can press Ctrl+C break download.<br/>
In addition, you can create an ignore.txt file. When you need to ignore some files that need to be downloaded, you can list the files in ignore.txt, with one line for each file. In this way, the download program will ignore downloading these files.<br/>

# usage
positional arguments:<br/>
  url                   URL<br/>
options:<br/>
  -h, --help   show this help message and exit<br/>
  -o OUTPUT, --output OUTPUT Save the file as OUTPUT<br/>
  -d DIRECTORY, --directory DIRECTORY Save the file to the directory DIRECTORY/<br/>
  -u USER, --user USER  http Authentication username<br/>
  -p PASSWORD, --password PASSWORD    http Authenticate Password<br/>
  -s, --skip      Skip file if it already exists in the target directory<br/>
  -v, --version    version<br/>
<br/>
for example:<br/>
python -m awget https://mirrors.aliyun.com/openwrt/releases/17.01.1/packages/aarch64_armv8-a/base/<br/>

# Third party libraries and install
all os:requests,pyquery<br/>
pip install requests,pyquery<br/>
windows os: [pywin32](https://github.com/mhammond/pywin32)<br/>
pip install pywin32 or pip install pywin32==306<br/>
in china can install by a mirror like 'pip install pywin32==306 -i https://pypi.tuna.tsinghua.edu.cn/simple'


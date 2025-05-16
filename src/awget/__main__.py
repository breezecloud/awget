# awget/__main__.py
#!/usr/bin/env python
r'''
reference:
https://www.osgeo.cn/requests/
https://blog.csdn.net/qq_36894974/article/details/104121817
https://blog.csdn.net/weixin_43927148/article/details/124030364
https://docs.pingcode.com/ask/175932.html
'''
'''
TODO:在被用户中断ctrl+c之后,好像日志没有记录该事件
version log:
0.0.1 第一个版本
0.0.2 增加了ignore功能 2024-10-11
0.0.7 修改为适合上传pypi并使用python -m执行
'''

import sys,argparse
from awget import main_download

__version__ = "0.0.9"
__description__ = '''
Pure python download utility,refer to https://pypi.org/project/wget/. 
The difference is this script can batch download of files listed based on a certain URL,also can download single file.
"awget -h" for usage.
You can press Ctrl+C break download.
'''

def main():
    if sys.version_info < (3, 0):
        sys.exit("Need Python version 3")

    # Create the option parser https://docs.python.org/zh-cn/3.12/library/argparse.html
    parser = argparse.ArgumentParser(prog='awget.py',description=__description__)
    parser.add_argument('-o','--output', type=str,help="save file as 'OUTPUT'")
    parser.add_argument('-d','--directory' , type=str, help="save file to directory 'DIRECTORY'/")
    parser.add_argument('-u','--user' , type=str, help="http username")
    parser.add_argument('-p','--password' , type=str, help="http passwd/")
    parser.add_argument('-s','--skip' , action='store_true', help="skip download if file exists")
    parser.add_argument('-v','--version', action='version',version=__version__,help="version" ) 
    parser.add_argument('url', help="URL" ) 
    args = vars(parser.parse_args())
    #print(f"args:{args}")
    main_download(url=args['url'],output=args['output'],directory=args['directory'],user=args['user'],password=args['password'],skip=args['skip'])

if __name__ == "__main__":
    main()


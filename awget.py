#!/usr/bin/env python
import os,sys,logging,signal,math,tempfile,shutil,argparse

# Import third-party modules
try:
    import requests
    from pyquery import PyQuery as pq
    if os.name == 'nt':
        import win32api,win32con
    else:
        signal.signal(signal.SIGINT, handle_sigint)
        signal.signal(signal.SIGTSTP, handler_sigctlz)    
except ModuleNotFoundError as e:
    logger.error(f"E: Cannot load required library {e}")
    logger.error("Please make sure the following Python3 modules are installed: requests pyquery and windows win32api win32con")
    sys.exit(1)

__version__ = "0.1"
__description__ = """
Pure python download utility,refer to https://pypi.org/project/wget/. 
The difference is this script can batch download of files listed based on a certain URL,also can download single file.
"awget -h" for usage.
You can press Ctrl+C break download.
"""

ctrl_c_pressed = False  # 定义一个变量用于判断是否按下了 Ctrl+C
__current_size = 0  # global state variable, which exists solely as a
                    # workaround against Python 3.3.0 regression
                    # http://bugs.python.org/issue16409
                    # fixed in Python 3.3.1

#logging创建一个logger
logger = logging.getLogger('pywget_logger')
logger.setLevel(logging.DEBUG)  # 设置日志级别
# 创建一个handler，用于输出到控制台
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# 创建一个handler，用于输出到文件
fh = logging.FileHandler('awget.log')
fh.setLevel(logging.INFO)
# 定义handler的输出格式
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
fh.setFormatter(formatter)
# 给logger添加handler
logger.addHandler(ch)
logger.addHandler(fh)
# 测试日志
#logger.debug('this is a debug level message')
#logger.info('this is an info level message')
#logger.warning('this is a warning level message')
#logger.error('this is an error level message')
#logger.critical('this is a critical level message')

class DownloadError(Exception):
    def __init__(self, message):
        self.message = message
        logger.error(message)

    def __str__(self):
        return f"MyCustomException: {self.message}"
  
def handler_sigctlz(signal, frame): #ctrl+z
    pass

def handle_sigint(signum, frame): #ctrl+c
    global ctrl_c_pressed
    ctrl_c_pressed = True

def get_console_width():
    """Return width of available window area. Autodetection works for
       Windows and POSIX platforms. Returns 80 for others
       Code from http://bitbucket.org/techtonik/python-pager
    """
    if os.name == 'nt':
        STD_INPUT_HANDLE  = -10
        STD_OUTPUT_HANDLE = -11
        STD_ERROR_HANDLE  = -12

        # get console handle
        from ctypes import windll, Structure, byref
        try:
            from ctypes.wintypes import SHORT, WORD, DWORD
        except ImportError:
            # workaround for missing types in Python 2.5
            from ctypes import (
                c_short as SHORT, c_ushort as WORD, c_ulong as DWORD)
        console_handle = windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)

        # CONSOLE_SCREEN_BUFFER_INFO Structure
        class COORD(Structure):
            _fields_ = [("X", SHORT), ("Y", SHORT)]

        class SMALL_RECT(Structure):
            _fields_ = [("Left", SHORT), ("Top", SHORT),
                        ("Right", SHORT), ("Bottom", SHORT)]

        class CONSOLE_SCREEN_BUFFER_INFO(Structure):
            _fields_ = [("dwSize", COORD),
                        ("dwCursorPosition", COORD),
                        ("wAttributes", WORD),
                        ("srWindow", SMALL_RECT),
                        ("dwMaximumWindowSize", DWORD)]

        sbi = CONSOLE_SCREEN_BUFFER_INFO()
        ret = windll.kernel32.GetConsoleScreenBufferInfo(
            console_handle, byref(sbi))
        if ret == 0:
            return 0
        return sbi.srWindow.Right+1

    elif os.name == 'posix':
        from fcntl import ioctl
        from termios import TIOCGWINSZ
        from array import array

        winsize = array("H", [0] * 4)
        try:
            ioctl(sys.stdout.fileno(), TIOCGWINSZ, winsize)
        except IOError:
            pass
        return (winsize[1], winsize[0])[0]

    return 80

def callback_progress(blocks, block_size, total_size, bar_function):
    """callback function
    called when download 
    """
    global __current_size
 
    width = min(100, get_console_width())
    if sys.version_info[:3] == (3, 3, 0):  # regression workaround
        if blocks == 0:  # first call
            __current_size = 0
        else:
            __current_size += block_size
        current_size = __current_size
    else:
        current_size = min(blocks*block_size, total_size)
    progress = bar_function(__current_size, total_size, width)
    if progress:
        sys.stdout.write("\r" + progress)

def bar_thermometer(current, total, width=80):
    """Return thermometer style progress bar string. `total` argument
    can not be zero. The minimum size of bar returned is 3. Example:

        [..........            ]

    Control and trailing symbols (\r and spaces) are not included.
    See `bar_adaptive` for more information.
    """
    # number of dots on thermometer scale
    avail_dots = width-2
    shaded_dots = int(math.floor(float(current) / total * avail_dots))
    return '[' + '.'*shaded_dots + ' '*(avail_dots-shaded_dots) + ']'

def bar(current, total, width=80):
    """default function return progress string
    """
    # process special case when total size is unknown and return immediately
    if not total or total < 0:
        msg = "%s / unknown" % current
        if len(msg) < width:    # leaves one character to avoid linefeed
            return msg
        if len("%s" % current) < width:
            return "%s" % current
    min_width = {
      'percent': 4,  # 100%
      'bar': 3,      # [.]
      'size': len("%s" % total)*2 + 3, # 'xxxx / yyyy'
    }
    priority = ['percent', 'bar', 'size']

    # select elements to show
    selected = []
    avail = width
    for field in priority:
      if min_width[field] < avail:
        selected.append(field)
        avail -= min_width[field]+1   # +1 is for separator or for reserved space at
                                      # the end of line to avoid linefeed on Windows
    # render
    output = ''
    for field in selected:

      if field == 'percent':
        # fixed size width for percentage
        output += ('%s%%' % (100 * current // total)).rjust(min_width['percent'])
      elif field == 'bar':  # [. ]
        # bar takes its min width + all available space
        output += bar_thermometer(current, total, min_width['bar']+avail)
      elif field == 'size':
        # size field has a constant width (min == max)
        output += ("%s / %s" % (current, total)).rjust(min_width['size'])

      selected = selected[1:]
      if selected:
        output += ' '  # add field separator

    return output        

def filename_fix_existing(filename):
    """Expands name portion of filename with numeric ' (x)' suffix to
    return filename that doesn't exist already.
    """
    dirname = u'.'
    if filename.find('.') == -1:#文件不存在扩展名的情况
        name = filename
        ext = ""
    else:
        name, ext = filename.rsplit('.', 1)  
    names = [x for x in os.listdir(dirname) if x.startswith(name)]
    names = [x.rsplit('.', 1)[0] for x in names]
    suffixes = [x.replace(name, '') for x in names]
    # filter suffixes that match ' (x)' pattern
    suffixes = [x[2:-1] for x in suffixes
                   if x.startswith(' (') and x.endswith(')')]
    indexes  = [int(x) for x in suffixes
                   if set(x) <= set('0123456789')]
    idx = 1
    if indexes:
        idx += sorted(indexes)[-1]
    return '%s (%d).%s' % (name, idx, ext)

def download(url,filename,directory,headers,auth):
    """download function
    url:string download url
    filename:string filename after download
    directory:string save file directory after download
    header:dict http requests header
    auto:tuple authentication http requests
    """
    global __current_size,ctrl_c_pressed

    if headers.get('User-Agent',None) == None:
        headers['User-Agent'] =  'Mozilla/5.0' #设置浏览器       
    headers['Accept-Encoding']='identity' #不执行压缩(为了让Content-length返回真实的文件size)
    #牺牲了效率，在默认情况下，Content-Length返回的是消息体的size，http1.1版本支持压缩，所以消息size和真实的文件size不同，requests接受的是真实的文件size。
    (fd, tmpfile) = tempfile.mkstemp(".tmp", prefix=filename, dir=directory)
    os.close(fd)
    os.unlink(tmpfile)

    file_temp = os.path.join(directory,tmpfile)
    try:
        # 发送HTTP GET请求，启用流式下载
        with requests.get(url,headers=headers,auth=auth,stream=True) as response:
            if response.status_code != requests.codes.ok:
                raise DownloadError('获取文件错误,错误代码:'+str(response.status_code))             
            total_length = response.headers.get('content-length')
            if total_length is None: # 无法获取文件大小
                print("无法获取文件大小，跳过进度提示。")
                response.raise_for_status()
                with open(file_temp, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        if os.name == 'nt':
                            if win32api.GetAsyncKeyState(ord('C')) and win32api.GetAsyncKeyState(win32con.VK_CONTROL):
                                ctrl_c_pressed = True
                        if ctrl_c_pressed:
                            raise DownloadError("捕获到Ctrl+C中断信号")                     
                        if chunk:  # 过滤掉保活新块
                            file.write(chunk) 
            else:
                #print(response.headers)
                # 文件总大小转换为整数
                total_length = int(total_length)
                # 已下载的文件大小
                __current_size = 0
                with open(file_temp, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        if os.name == 'nt':
                            if win32api.GetAsyncKeyState(ord('C')) and win32api.GetAsyncKeyState(win32con.VK_CONTROL):
                                ctrl_c_pressed = True
                        if ctrl_c_pressed:
                            raise DownloadError("捕获到Ctrl+C中断信号")                    
                        callback_progress(int(total_length/8192),8192,total_length,bar_function=bar)
                        file.write(chunk)
                        __current_size += len(chunk)
                    callback_progress(int(total_length/8192),8192,total_length,bar_function=bar)                 
            shutil.move(file_temp, os.path.join(directory,filename))
    except  Exception as e:
        raise DownloadError("文件下载失败"+str(e))

if __name__ == "__main__":
    if sys.version_info < (3, 0):
        sys.exit("Need Python version 3")

    # Create the option parser https://docs.python.org/zh-cn/3.12/library/argparse.html
    parser = argparse.ArgumentParser(prog='awget.py',description=__description__)
    parser.add_argument('-o','--output', type=str,help="将文件保存为OUTPUT")
    parser.add_argument('-d','--directory' , type=str, help="将文件保存到目录 DIRECTORY/")
    parser.add_argument('-u','--user' , type=str, help="http认证用户名")
    parser.add_argument('-p','--password' , type=str, help="http认证密码/")
    parser.add_argument('-s','--skip' , action='store_true', help="跳过文件如果目标目录已经存在该文件")
    parser.add_argument('-v','--version', action='version',version=__version__,help="版本" ) 
    parser.add_argument('url', help="URL" ) 
    args = vars(parser.parse_args())
    #print("args:")
    #print(args)
    url = args['url']
    #url = "https://mirrors.aliyun.com/openwrt/releases/17.01.1/packages/aarch64_armv8-a/base/" 
    #url = "https://chuangtzu.ftp.acc.umu.se/debian-cd/current/amd64/iso-cd/debian-12.7.0-amd64-netinst.iso"
    #url = "http://error.sample/"

    if args['directory'] != None:
        directory = os.path.join(os.getcwd(),args['directory']) 
    else:
        directory = os.getcwd()
    if not os.path.exists(directory):
        try:
            os.mkdir(directory)
        except PermissionError as e :
            logger.error(f'无权限建立目录 {str(e)}')
            sys.exit(1)
        except Exception as e:
            logger.error(f'建立目录异常 {str(e)}')
            sys.exit(1)
    else:
        if args['directory'] != None:
            logger.warning(f'目录已经存在:{directory}')

    headers = {}    
    #auth = ('silex', 'luping')  
    auth = (args['user'],args['password'])# 设置HTTP认证信息    
    try:
        with requests.get(url ,auth=auth,stream=True) as r:
            if r.status_code != requests.codes.ok:
                raise DownloadError(f'获取文件错误,错误代码:{str(r.status_code)}')    
            Content_Type_header = r.headers['Content-Type']
    except Exception as e:
            logger.error(f'连接服务器失败 {str(e)}')
            sys.exit(1)        

    filenames = []    
    if Content_Type_header[0:9] == 'text/html':
        if args['output'] != None:
            logger.error('批量下载不能指定文件名')
            sys.exit(1)
        doc = pq(url=url,encoding="utf-8")
        files=doc("tbody .link a")
        for file in files:
            filename = file.attrib['href']
            if filename != '../':
                filenames.append(filename)
    else:
        filenames.append(url.split('/')[-1])
    
    logger.info(f'开始下载，一共发现{len(filenames)}个文件,你可以Ctrl+C中断下载任务')
    for index,filename in enumerate(filenames):
        logger.info(f'开始下载文件{index+1}/{len(filenames)}:{filename}')    
        try:
            if os.path.exists(os.path.join(directory,filename)) and args['skip'] == True:
                logger.warning(f"{filename}文件已经存在,跳过该文件")  
                continue
            if Content_Type_header[0:9] == 'text/html':
                if url[-1] != '/': 
                    file_url = url + "/" + filename # 要下载的文件的URL
                else:
                    file_url = url + filename
            else:
                file_url = url
            if args['output'] != None:
                filename = args['output']
            download(file_url,filename,directory,headers=headers,auth=auth)
            print("")
            logger.info(f'{filename} 下载完成！')  
        except Exception as e:
            logger.error(f'{filename}下载失败，状态码：{e}')
            sys.exit(1)

    print("\nDone!")
    sys.exit(0)

    r'''
    reference:
    https://www.osgeo.cn/requests/
    https://blog.csdn.net/qq_36894974/article/details/104121817
    https://blog.csdn.net/weixin_43927148/article/details/124030364
    https://docs.pingcode.com/ask/175932.html
    '''

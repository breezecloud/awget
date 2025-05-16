import os,sys,logging,signal,math,tempfile,shutil,time

def handler_sigctlz(signal, frame): #ctrl+z
    pass

def handle_sigint(signum, frame): #ctrl+c
    global ctrl_c_pressed
    ctrl_c_pressed = True

# Import third-party modules
try:
    import requests
    from pyquery import PyQuery as pq
    if os.name == 'nt':
        import win32api,win32con,win32gui
    else:
        signal.signal(signal.SIGINT, handle_sigint)
        signal.signal(signal.SIGTSTP, handler_sigctlz)    
except ModuleNotFoundError as e:
    print(f"E: Cannot load required library {e}")
    print("Please make sure the following Python3 modules are installed: requests pyquery and  pywin32 in windows")
    print("install modules:pip3 install requests pyquery")
    print("in windows 'pip3 install pywin32' or 'pip3 install pywin32==306' after python version 3.8") #pip install pywin32==306 -i https://pypi.tuna.tsinghua.edu.cn/simple
    sys.exit(1)
        
ctrl_c_pressed = False  # 定义一个变量用于判断是否按下了 Ctrl+C
__current_size = 0  # global state variable, which exists solely as a
                    # workaround against Python 3.3.0 regression
                    # http://bugs.python.org/issue16409
                    # fixed in Python 3.3.1

ignore_file = [] #忽略下载文件列表
if os.path.exists("ignore.txt"):
    with open('ignore.txt', 'rt') as file:
        for line in file:
          ignore_file.append(line.replace("\n", ""))

active_handle = win32gui.GetForegroundWindow() #courrent window handle

class DownloadError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return f"MyCustomException: {self.message}"

#logging创建一个logger
logger = logging.getLogger('awget_logger')
logger.setLevel(logging.DEBUG)  # 设置日志级别
# 创建一个handler，用于输出到控制台
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# 创建一个handler，用于输出到文件
fh = logging.FileHandler('awget.log',encoding='utf-8')
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
    global __current_size , ctrl_c_pressed,active_handle

    if headers.get('User-Agent',None) == None:
        headers['User-Agent'] =  'Mozilla/5.0' #设置浏览器       
    headers['Accept-Encoding']='identity' #不执行压缩(为了让Content-length返回真实的文件size)
    #牺牲了效率，在默认情况下，Content-Length返回的是消息体的size，http1.1版本支持压缩，所以消息size和真实的文件size不同，requests接受的是真实的文件size。
    (fd, tmpfile) = tempfile.mkstemp(".tmp", prefix=filename, dir=directory)
    os.close(fd)
    os.unlink(tmpfile)

    file_temp = os.path.join(directory,tmpfile)  
    with requests.get(url,headers=headers,auth=auth,stream=True) as response:# 发送HTTP GET请求，启用流式下载
        try:
            response.raise_for_status() #检查响应的状态码
            total_length = response.headers.get('content-length')
            if total_length is None: # 无法获取文件大小
                logger.warning(f"{filename}Unable to retrieve file size, skip progress prompt")
            else:
                total_length = int(total_length)
            __current_size = 0
            with open(file_temp, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):  
                    if total_length is not None:
                        callback_progress(int(total_length/8192),8192,total_length,bar_function=bar)             
                    if os.name == 'nt':
                        if win32api.GetAsyncKeyState(ord('C')) and win32api.GetAsyncKeyState(win32con.VK_CONTROL):
                            if active_handle == win32gui.GetForegroundWindow(): #windows环境所有consol窗口均收到键盘消息，要判断是当前窗口，Linux环境未验证！！！
                                ctrl_c_pressed = True
                    if ctrl_c_pressed:
                        raise DownloadError("Capture Ctrl+C interrupt signal")                     
                    if chunk:  # 过滤掉保活新块
                        file.write(chunk)
                    __current_size += len(chunk)
                    if total_length is not None:
                        callback_progress(int(total_length/8192),8192,total_length,bar_function=bar) 
            if total_length is None or (__current_size == total_length): 
                shutil.move(file_temp, os.path.join(directory,filename))            
            else:
               raise DownloadError("\nThere is a difference in file length")
        except requests.exceptions.HTTPError as http_err:
            raise DownloadError(f"HTTP error occurred: {http_err}")    
        except requests.exceptions.RequestException as req_err:
            # 这里可以捕获其他类型的请求异常，如连接错误、超时等
            raise DownloadError(f"Request exception: {req_err}")
        except  Exception as e:
            raise DownloadError("unknown exception"+str(e))    

def find_ignore_file(filename): 
    """
        查询是否属于被忽略的文件
        返回:Ture 存在
        返回:False 不存在
    """
    global ignore_file
    if filename in ignore_file:
        with open("ignore.log","a") as file:
            localtime = time.asctime(time.localtime(time.time()))
            file.write(filename+"---"+str(localtime)+"\n") #记录忽略的文件名和当前时间
        return True
    else:
        return False

def main_download(url,output=None,directory=None,user=None,password=None,skip=False):
    '''
    下载
    output:string #filename
    directory:string #savei directory
    user:string #username
    password:string #password
    skip:boolean #skip flag
    '''
    #url = "https://mirrors.aliyun.com/openwrt/releases/17.01.1/packages/aarch64_armv8-a/base/" 
    #url = "https://chuangtzu.ftp.acc.umu.se/debian-cd/current/amd64/iso-cd/debian-12.7.0-amd64-netinst.iso"
    #url = "http://error.sample/"
    logger.info("---START---")
    if directory != None:
        directory = os.path.join(os.getcwd(),directory) 
    else:
        directory = os.getcwd()
    if not os.path.exists(directory):
        try:
            os.mkdir(directory)
        except PermissionError as e :
            logger.error(f'No permission to create directory {str(e)}')
            sys.exit(1)
        except Exception as e:
            logger.error(f'Create directory exception {str(e)}')
            sys.exit(1)
    else:
        if directory != None:
            logger.warning(f'directory already exists:{directory}')

    headers = {}    
    auth = (user,password)# 设置HTTP认证信息    
    try:
        with requests.get(url ,auth=auth,stream=True) as r:
            if r.status_code != requests.codes.ok:
                raise DownloadError(f'File retrieval error, error code:{str(r.status_code)}')    
            Content_Type_header = r.headers['Content-Type']
    except Exception as e:
            logger.error(f'Failed to connect to server {str(e)}')
            sys.exit(1)        

    filenames = []    
    if Content_Type_header[0:9] == 'text/html': #url是一个html文件，获取所有文件名
        if output != None:
            logger.error('Batch download cannot specify file name')
            sys.exit(1)
        doc = pq(url=url,encoding="utf-8")
        files=doc("tbody .link a")
        for file in files:
            filename = file.attrib['href']
            if filename != '../':
                filenames.append(filename)
    else:
        filenames.append(url.split('/')[-1])
    
    logger.info(f'Starting the download, a total of {len (filename)} files were found. You can interrupt the download task by pressing Ctrl+C. Batch download cannot specify file names')
    for index,filename in enumerate(filenames):
        logger.info(f'Start downloading files{index+1}/{len(filenames)}  {filename}')    
        try:
            if (os.path.exists(os.path.join(directory,filename))) and (skip == True):
                logger.warning(f"{filename}The file already exists, skip the file")  
                continue
            if find_ignore_file(filename):
                logger.warning(f"{filename}The file is ignoring the list and skipping it")  
                continue            
            if Content_Type_header[0:9] == 'text/html': #url是一个html文件，修正url
                if url[-1] != '/': 
                    file_url = url + "/" + filename # 要下载的文件的URL
                else:
                    file_url = url + filename
            else:
                file_url = url
            if output != None:
                filename = output
            download(file_url,filename,directory,headers=headers,auth=auth)
            print("")
            logger.info(f'{filename} Download completed!')  
        except Exception as e:
            logger.error(f'{filename}Download failed! status code:{e}')
            sys.exit(1)

    print("\nDone!")
    sys.exit(0)


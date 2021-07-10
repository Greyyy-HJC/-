import hashlib
import os
import sys
import inspect
import ctypes
import threading

def _async_raise(tid, exctype):
    """raises the exception, performs cleanup if needed"""
    tid = ctypes.c_long(tid)
    if not inspect.isclass(exctype):
        exctype = type(exctype)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        # """if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")
def stop_thread(thread):
    if not thread.ident:
        sys.exit()
    _async_raise(thread.ident, SystemExit)





import execjs





def exec_js(js_str='', js_path=False):
    """
    exec js
    :param js_str: 执行js 源码
    :param js_path: 执行js文件
    :return:
    """
    if js_path:
        assert (js_path and os.path.exists(js_path)), Exception("js 文件不存在")
        js_str = ''
        with open(js_path, 'r') as f:
            js_lines = f.readlines()
        for line in js_lines:
            js_str += line
    assert js_str, Exception("必须传入js")
    js_cxt = execjs.compile(js_str)
    return js_cxt

def get_id(params_str):
    jsstr = get_js()
    ctx = execjs.compile(jsstr)
    return ctx.call('u', str(params_str))
def get_js():
    f = open("jsstr.js")
    line = f.readline()
    htmlstr = ''
    while line:
        htmlstr = htmlstr + line
        line = f.readline()
    return htmlstr



def unique_uid(*args, **kwargs):
    """
    generator only uid
    生成唯一识别符
    """
    str_tmp = ''
    if args:
        str_tmp = ''.join('%s' % i for i in args)  # 拼接多个
    if kwargs:
        str_tmp = ''.join('%s' % b for a, b in kwargs.items())  # 拼接多个的值b
    # print(str_tmp)
    md5_str = hashlib.md5(str_tmp.encode()).hexdigest()
    return md5_str


if __name__ == '__main__':
    # print(get_id())
    print(unique_uid('111'))


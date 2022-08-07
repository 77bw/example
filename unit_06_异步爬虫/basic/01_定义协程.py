"""
调用协程的三种基本方法
"""
import asyncio

#第一种方法

# async     定义协程方法
async def excute(x):
    print("Number:",x)

coroutine = excute(1)   #调用协程方法没有立即执行而是返回了一个协程对象
print('Coroutine:',coroutine)
print("After calling execute")

loop = asyncio.get_event_loop()  # get_event_loop方法 创建了事件循环并赋值给loop
loop.run_until_complete(coroutine)  #调用loop的run_until_complete方法将协程对象注册到了事件循环中来，接着启动
print('After callling loop')

"""
总结 ：
    由此可见async 定义的方法会变成一个无法执行的协程对象，必须将此对象注册到事件循环中才可以执行；/
"""

#第二种方法利用了task
#task:它是对协程对象的进一步封装，比协程对象多了运行状态，例如running,finished
#前面使用这个方法的时候loop.run_until_complete(coroutine) 实际上它进行了一个操作，就是将coroutine封装成task对象。

async def excute1(x):
    print("Number:",x)
    return x

coroutine = excute1(2)
print('Coroutine:',coroutine)
print("After calling execute")

loop = asyncio.get_event_loop()
task = loop.create_task(coroutine)   #将协程对象转换为task对象
print("Task:",task)             #task 为待执行状态
loop.run_until_complete(task)    #将task对象添加到事件循环中执行，并启动
print("Task:",task)                #task 为已完成状态
print('After callling loop')


#第三种方法   定义task对象的另一种方式，就是直接调用asyncio包的ensure_future方法，返回结果也是task对象


async def excute2(x):
    print("Number:",x)
    return x

coroutine = excute2(3)
print('Coroutine:',coroutine)
print("After calling execute")

loop = asyncio.get_event_loop()
task = asyncio.ensure_future(coroutine)   #将协程对象转换为task对象
print("Task:",task)             #task 为待执行状态
loop.run_until_complete(task)    #将task对象添加到事件循环中执行，并启动
print("Task:",task)                #task 为已完成状态
print('After callling loop')
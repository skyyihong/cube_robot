from machine import Pin, I2C
from tcs34725 import TCS34725  # 导入颜色识别模块驱动
import time, utime, json
from wifi import connect  # 导入自定义的wifi连接模块
import socket

# 定义
hand1 = Pin(12, Pin.OUT)
hand1_dir = Pin(14, Pin.OUT)
hand2 = Pin(27, Pin.OUT)
hand2_dir = Pin(26, Pin.OUT)
hand3 = Pin(25, Pin.OUT)
hand3_dir = Pin(33, Pin.OUT)
led1 = Pin(17, Pin.OUT, value=0)
led2 = Pin(5, Pin.OUT, value=0)

# 设置电机的转动的时间，最小值为45。
durtion_time = 65
durtion_rotate_time = 65

senor1 = I2C(1, scl=Pin(18), sda=Pin(19), freq=400_000)
senor2 = I2C(0, scl=Pin(22), sda=Pin(21), freq=400_000)

color1 = TCS34725(senor1, 0x29)
color2 = TCS34725(senor2, 0x29)

ip = connect()
reciever_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
local_addr = (ip, 80)
reciever_udp.bind(local_addr)

FLAG = False
current_size_list = ["F", "R", "B", "L"]
cube_colors = {}


def start_end(*args):
    global FLAG
    FLAG = True


def interrupt(*args):
    global FLAG
    FLAG = False
    raise Exception("end!")
    print("init_hands_finish")


button1 = Pin(4, Pin.IN, Pin.PULL_UP)
button2 = Pin(16, Pin.IN, Pin.PULL_UP)
button1.irq(trigger=Pin.IRQ_FALLING, handler=start_end)
button2.irq(trigger=Pin.IRQ_FALLING, handler=interrupt)

color_map = {
    'R1': [(50, 69.9999), (4, 13), (2, 8)],
    'R2': [(70, 79.9999), (5.763148, 11.96308), (2.7, 6.848065)],
    'L1': [(70, 88), (4.2, 5.99999), (1, 1.99999)],
    'L2': [(78, 80), (4.2, 6.9), (2, 2.69999)],
    'L3': [(80, 88), (4.2, 10), (1, 5)],
    'D1': [(0.1, 3), (19, 32), (15, 44)],
    'U1': [(1, 5), (51, 70), (2.5, 9)],
    'B1': [(7, 15), (21, 32.999999), (5, 12)],
    'F1': [(7, 18), (33, 49), (0.5, 4.999999)]
}
color_map = {
    'R': [(85, 130), (2, 5.4), (1, 4)],
    'L': [(63, 91), (4.561579, 10), (0.1, 3)],
    'D': [(0.1, 4), (16, 27), (31, 49)],
    'U': [(1, 7), (50, 73), (2, 6)],
    'B': [(8, 15), (22, 33), (4.1, 11)],
    'F': [(13.6, 24), (26, 40), (0.5, 4.09999)]
}


def led_switch(status):
    if status == "on":
        led1.value(1)
        led2.value(1)
    else:
        led1.value(0)
        led2.value(0)


def sizeUD_rotate(degree, collections=None):
    global cube_colors
    # 13 为极限，最慢90
    # 旋转 630碰到弹簧 
    durtion = durtion_time if collections else durtion_rotate_time
    hand1_dir.value(0)
    hand2_dir.value(1)
    total_steps = 800 * degree
    for step in range(total_steps):
        hand1.value(1)
        hand2.value(1)
        utime.sleep_us(durtion)
        hand1.value(0)
        hand2.value(0)
        utime.sleep_us(durtion)
        if collections is not None and step % 400 == 0:
            index = step // 400
            num1, num2 = collections[index]
            if (num1 + num2) != 0:
                data1 = color1.read(True)
                data2 = color2.read(True)
                cube_colors[num1] = color1.html_rgb(data1)
                cube_colors[num2] = color2.html_rgb(data2)
    if collections is None:
        return
    num1, num2 = collections[-1]
    if (num1 + num2) != 0:
        data1 = color1.read(True)
        data2 = color2.read(True)
        cube_colors[num1] = color1.html_rgb(data1)
        cube_colors[num2] = color2.html_rgb(data2)


def color2str():
    global cube_colors, color_map
    cube_str = {}
    center_str = {
        49: "B",
        40: "L",
        31: "D",
        22: "F",
        13: "R",
        4: "U",
    }
    for i in cube_colors:
        cube_str[i] = cube_colors[i]
        for size in color_map:
            count = 0
            for k in range(3):
                small, big = color_map[size][k]
                if (small <= cube_colors[i][k]) and (cube_colors[i][k] <= big):
                    count = count + 1
            if count == 3:
                cube_str[i] = size[0]
                break
    cube_str.update(center_str)
    print("cube_str:", cube_str)
    try:
        cube_str_array = [cube_str.get(l) for l in range(54)]
        print("cube_str_array:", cube_str_array)
        join_str = "".join(cube_str_array)
    except Exception as e:
        # 如果尤其只有一种颜色没有识别不出来，使用程序自动不齐。如果是有两种以上颜色没有识别出来，放弃处理
        print("发现有部分颜色没有识别出...")
        count = 0
        str_count = {}
        num_list = []
        for i in cube_str:
            size = cube_str[i]
            if len(size) == 3:
                num_list.append(i)
                count += 1
            else:
                str_count[size] = str_count.get(size, 0) + 1
        for i in str_count:
            reset = 9 - count
            if str_count[i] == reset:
                for k in num_list:
                    cube_str[k] = i
        cube_str_array = [cube_str.get(l) for l in range(54)]
        print("cube_str_array:", cube_str_array)
        join_str = "".join(cube_str_array)
    finally:
        return join_str


def sizeFRBL_rotate(degree, size=None):
    global current_size_list
    durtion = durtion_rotate_time if size else durtion_time
    if size:
        index = current_size_list.index(size)
        start = current_size_list[0:index]
        end = current_size_list[index:]
        current_size_list = end + start
        sizeUD_rotate(index)
    hand3_dir.value(1 if degree > 0 else 0)
    for i in range(800 * abs(degree) + 230):
        hand3.value(1)
        utime.sleep_us(durtion)
        hand3.value(0)
        utime.sleep_us(durtion)
    hand3_dir.value(0 if degree > 0 else 1)
    for i in range(230):
        hand3.value(1)
        utime.sleep_us(durtion)
        hand3.value(0)
        utime.sleep_us(durtion)


def sizeU_rotate(degree):
    durtion = durtion_rotate_time
    if degree < 0:
        new_degree = abs(degree)
    else:
        if degree == 1:
            new_degree = 3
        else:
            new_degree = 2
    hand2_dir.value(0)
    total_steps = 800 * new_degree
    over_step = 40
    for step in range(total_steps + over_step):
        hand2.value(1)
        utime.sleep_us(durtion)
        hand2.value(0)
        utime.sleep_us(durtion)
    hand2_dir.value(1)
    for step in range(over_step):
        hand2.value(1)
        utime.sleep_us(durtion)
        hand2.value(0)
        utime.sleep_us(durtion)


def sizeD_rotate(degree):
    durtion = durtion_rotate_time
    if degree > 0:
        new_degree = abs(degree)
    else:
        new_degree = 3
    hand1_dir.value(1)
    total_steps = 800 * new_degree
    over_step = 40
    for step in range(total_steps + over_step):
        hand1.value(1)
        utime.sleep_us(durtion)
        hand1.value(0)
        utime.sleep_us(durtion)
    hand1_dir.value(0)
    for step in range(over_step):
        hand1.value(1)
        utime.sleep_us(durtion)
        hand1.value(0)
        utime.sleep_us(durtion)


def robot_exec_handle(slove_list):
    robot_exec_list = []
    for size in slove_list:
        if len(size) == 1:
            robot_exec_list.append((size, 1))
        else:
            if "'" in size:
                robot_exec_list.append((size[0], -1))
            else:
                robot_exec_list.append((size[0], 2))
    for exec_step in robot_exec_list:
        size, degree = exec_step
        if size == "U":
            sizeU_rotate(degree)
        elif size == "D":
            sizeD_rotate(degree)
        else:
            sizeFRBL_rotate(degree, size)
    print(robot_exec_list)


def color_collection():
    global led1, led2, FLAG, current_size_list
    current_size_list = ["F", "R", "B", "L"]
    collect_color_map = [
        [3, [(36, 42), (23, 48), (38, 44), (10, 43), (9, 15), (50, 21), (11, 17)]],
        [2, [(0, 0), (37, 16), (33, 27), (19, 52), (0, 6)]],
        [3, [(0, 0), (0, 0), (29, 35), (46, 25), (8, 2), (0, 0), (0, 0)]],
        [2, [(0, 0), (0, 0), (18, 51), (12, 41), (47, 26)]],
        [3, [(0, 0), (0, 0), (45, 24), (39, 14), (20, 53), (0, 0), (0, 0)]],
        [2, [(0, 0), (0, 0), (0, 0), (5, 32), (0, 0)]],
        [1, [(0, 0), (0, 0), (0, 0)]],
        [2, [(0, 0), (3, 30), (0, 0), (7, 28), (0, 0)]],
        [2, [(0, 0), (0, 0), (0, 0), (1, 34), (0, 0)]]
    ]
    try:
        led_switch("on")
        for num, colors in enumerate(collect_color_map):
            degree, collections = colors
            sizeUD_rotate(degree, collections)
            if num != 8:
                sizeFRBL_rotate(1)
        led_switch("off")
        print("cube_colors:", cube_colors)
        cube_str = color2str()
        buffer = json.dumps(cube_str).encode()
        reciever_udp.sendto(buffer, ("10.255.255.199", 9000))
        recv_data = reciever_udp.recvfrom(9000)
        msg = json.loads(recv_data[0].decode())
        if msg:
            slove_list = msg.split(" ")
            print("slove_list:", len(slove_list), slove_list)
            robot_exec_handle(slove_list)
        else:
            print("魔方数据解法出错")
    finally:
        led_switch("off")
        FLAG = False


def main():
    print("ready.....")
    while True:
        try:
            if FLAG:
                start = time.ticks_ms()
                color_collection()
                delta = time.ticks_diff(time.ticks_ms(), start)
                print("总执行时间为:", delta / 1000)
            time.sleep(0.1)
        except Exception as e:
            print(e)


if __name__ == "__main__":
    main()

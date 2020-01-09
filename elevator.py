import numpy as np
import wx
import threading
from pubsub import pub
import time
import matplotlib.pyplot as plt

max_floor = 20
sum_time = 0
finished_p = 0
time_count = 0


class Passenger:

    count = 0
    global time_count

    def __init__(self, req_floor=0, arr_floor=0, req_time=0):
        Passenger.count += 1
        self.id = self.count
        self.req_time = req_time
        self.ser_time = 0
        self.arr_time = 0
        self.req_floor = req_floor
        self.arr_floor = arr_floor
        self.direction = self.set_direction()

    def get_total_time(self):
        return self.arr_time - self.req_time

    def get_serve_time(self):
        return self.arr_time - self.ser_time

    def set_direction(self):
        if self.req_floor > self.arr_floor:
            return -1
        else:
            return 1


class Elevator:
    def __init__(self):
        self.max_floor = max_floor
        self.req_que = []
        self.cur_floor = 1.0
        # 速度为每时间步上升/下降多少层
        self.speed = 0.2
        self.wait = 0
        self.height_per_floor = 3
        self.door = True
        self.avail = True
        self.tar_floor = None
        self.direction = 0
        self.carried = []

    def down(self):
        self.cur_floor = round(self.cur_floor - self.speed, 10)
        print('电梯下行...')

    def up(self):
        self.cur_floor = round(self.cur_floor + self.speed, 10)
        print('电梯上行...')

    def arr(self):
        print('电梯到达...')
        self.open_door()
        # 更新tar_floor
        self.check_passengers()
        if self.set_target_floor():
            if self.set_direction():
                self.check_passengers()
                self.set_target_floor()
        self.wait += 1

    def open_door(self):
        print('开门')
        if self.door:
            self.door = False

    def close_door(self):
        print('关门')
        self.door = True
        self.wait = 0

    # 检查电梯需求列表，有没有人上，有没有人下
    def check_passengers(self):
        global sum_time
        global finished_p
        global time_count
        print('检查乘客状态')
        print('请求列表：', [p.id for p in self.req_que])
        print('电梯乘客：', [p.id for p in self.carried])
        for p in self.carried[:]:
            if p.arr_floor == self.cur_floor:
                print('{0}号乘客下电梯'.format(p.id))
                p.arr_time = time_count
                sum_time = sum_time + p.arr_time - p.req_time
                finished_p += 1
                self.carried.remove(p)
        for p in self.req_que[:]:
            if p.req_floor == self.cur_floor:
                if self.direction != 0:
                    if p.direction == self.direction:
                        print('{0}号乘客上电梯'.format(p.id))
                        self.req_que.remove(p)
                        self.carried.append(p)
                    elif not self.carried:
                        print('{0}号乘客上电梯'.format(p.id))
                        self.req_que.remove(p)
                        self.carried.append(p)
                else:
                    print('{0}号乘客上电梯'.format(p.id))
                    self.req_que.remove(p)
                    self.carried.append(p)

    # 检查需求，设定目标楼层
    def set_target_floor(self):
        print('寻找目标楼层，当前电梯方向:{}'.format(self.direction))
        self.tar_floor = None
        min_req_dis = None
        min_arr_dis = None

        # 检查电梯外部请求
        req_dis_list = []
        req_que_select = []
        if self.req_que[:]:
            for p in self.req_que:
                if p.req_floor == self.cur_floor and self.carried:
                    continue
                else:
                    req_que_select.append(p)
                    req_dis_list.append(self.alloc_cost(p.req_floor, p.direction))
                min_req_dis = min(req_dis_list)
        # 检查电梯内部请求
        if self.carried:
            arr_dis_list = [self.get_distance(p.arr_floor) for p in self.carried]
            min_arr_dis = min(arr_dis_list)

        # 获取最近的需求层
        if min_arr_dis is not None and min_req_dis is not None:
            if min_arr_dis < min_req_dis:
                self.tar_floor = self.carried[arr_dis_list.index(min_arr_dis)].arr_floor
                print('目标楼层：{}'.format(self.tar_floor))
            else:
                self.tar_floor = req_que_select[req_dis_list.index(min_req_dis)].req_floor
                print('目标楼层：{}'.format(self.tar_floor))
            return True
        elif min_arr_dis is not None:
            self.tar_floor = self.carried[arr_dis_list.index(min_arr_dis)].arr_floor
            print('目标楼层：{}'.format(self.tar_floor))
            return True
        elif min_req_dis is not None:
            self.tar_floor = req_que_select[req_dis_list.index(min_req_dis)].req_floor
            print('目标楼层：{}'.format(self.tar_floor))
            return True
        else:
            print('no target')
            return False

    # 计算请求楼层和当前楼层的距离
    def get_distance(self, req_floor):
        if self.direction == 1:
            if self.cur_floor > req_floor:
                return self.max_floor - self.cur_floor + self.max_floor - req_floor
            else:
                return req_floor - self.cur_floor
        elif self.direction == -1:
            if self.cur_floor > req_floor:
                return self.cur_floor - req_floor
            else:
                return self.cur_floor - 1 + req_floor - 1
        else:
            return abs(self.cur_floor - req_floor)

    def set_direction(self):
        old_direction = self.direction
        if self.tar_floor:
            if self.tar_floor > self.cur_floor:
                self.direction = 1
            elif self.tar_floor < self.cur_floor:
                self.direction = -1
            elif not self.carried:
                self.direction = 0
        else:
            self.direction = 0
        if self.direction != old_direction:
            print('方向改变：{}'.format(self.direction))
            return True
        else:
            return False

    # 计算电梯分配成本
    def alloc_cost(self, req_floor, direction):
        if self.direction == 1:
            if self.cur_floor > req_floor or direction == -1:
                return self.max_floor - self.cur_floor + self.max_floor - req_floor
            else:
                return req_floor - self.cur_floor
        elif self.direction == -1:
            if self.cur_floor < req_floor or direction == 1:
                return self.cur_floor - 1 + req_floor - 1
            else:
                return self.cur_floor - req_floor
        else:
            return abs(self.cur_floor - req_floor)


# 检查电梯执行动作
def check_elevator(elevator):
    # 开门
    if elevator.wait == 0:
        if elevator.tar_floor > elevator.cur_floor:
            elevator.up()
        elif elevator.tar_floor < elevator.cur_floor:
            elevator.down()
        else:
            elevator.arr()
    else:
        elevator.wait += 1
    if elevator.wait == 4:
        elevator.close_door()


# 产生乘客需求
def make_request(elevators, clock, pro):
    if np.random.rand() < pro:
        req_floor = np.random.randint(1, max_floor + 1)
        arr_floor = np.random.randint(1, max_floor + 1)
        # 当如果请求到达楼层和当前所在楼层相同时，重新产生乘客请求
        while arr_floor == req_floor:
            arr_floor = np.random.randint(1, max_floor + 1)
        p = Passenger(req_floor, arr_floor, clock)

        dis_list = [ele.alloc_cost(p.req_floor, p.direction) for ele in elevators]
        print(dis_list)
        print('控制台信息：{0}楼用户请求使用{1}号电梯到达{2}楼，ID: {3}'.format(req_floor, dis_list.index(min(dis_list)), arr_floor, p.id))
        elevators[dis_list.index(min(dis_list))].req_que.append(p)
        print("-----------------------")
        print("{}号电梯重新搜索请求".format(dis_list.index(min(dis_list))))
        elevators[dis_list.index(min(dis_list))].set_target_floor()
        elevators[dis_list.index(min(dis_list))].set_direction()


def draw_elevator(elevators, ax):
    ax.axis('off')
    ax.add_patch(plt.Rectangle((0, elevators[0].cur_floor / max_floor - 1.0 / max_floor), 0.1, 0.1, fill=elevators[0].door, edgecolor='blue'))
    ax.add_patch(plt.Rectangle((0.1, elevators[0].cur_floor / max_floor - 1.0 / max_floor), 0.1, 0.1, fill=elevators[0].door, edgecolor='blue'))

    ax.add_patch(plt.Rectangle((0.4, elevators[1].cur_floor / max_floor - 1.0 / max_floor), 0.1, 0.1, fill=elevators[1].door, edgecolor='blue'))
    ax.add_patch(plt.Rectangle((0.5, elevators[1].cur_floor / max_floor - 1.0 / max_floor), 0.1, 0.1, fill=elevators[1].door, edgecolor='blue'))

    ax.add_patch(plt.Rectangle((0.8, elevators[2].cur_floor / max_floor - 1.0 / max_floor), 0.1, 0.1, fill=elevators[2].door, edgecolor='blue'))
    ax.add_patch(plt.Rectangle((0.9, elevators[2].cur_floor / max_floor - 1.0 / max_floor), 0.1, 0.1, fill=elevators[2].door, edgecolor='blue'))

    plt.savefig("elevator.png")
    # plt.show()
    plt.cla()


class WorkThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def run(self):
        # ele = Elevator()
        elevators = [Elevator(), Elevator(), Elevator()]
        global time_count
        _fig, ax = plt.subplots(figsize=(5, 5))

        for i in range(1000):

            if self._stop_event.isSet():
                break

            time.sleep(0.4)

            # 统计时间
            time_count += 0.4

            make_request(elevators, time_count, 0.1)

            for j, ele in enumerate(elevators):
                print("@@@@@@@@@@@@@@@@@@@@@@")
                print("{}号电梯".format(j + 1))
                print("**********************")
                print('当前楼层：{}'.format(ele.cur_floor))

                if ele.tar_floor is None:
                    ele.set_target_floor()
                    ele.set_direction()
                    if ele.tar_floor is None:
                        print('电梯空闲')
                        if ele.wait != 0:
                            ele.wait += 1
                        if ele.wait == 4:
                            ele.close_door()
                    else:
                        check_elevator(ele)
                else:
                    check_elevator(ele)
            draw_elevator(elevators, ax)
            wx.CallAfter(pub.sendMessage, 'change_elevator', elevators=elevators)


class ElevatorFrame(wx.Frame):
    """
    A Frame that says Hello World
    """

    def __init__(self, *args, **kw):
        # ensure the parent's __init__ is called
        super(ElevatorFrame, self).__init__(*args, **kw)

        self.thread = None
        self.floor = 1

        self.max_floor = 10
        self.r_time = 0

        pub.subscribe(self.update_elevator, 'change_elevator')

        _fig, ax = plt.subplots(figsize=(5, 5))
        ax.axis('off')
        ax.add_patch(plt.Rectangle((0, 0), 0.1, 0.1))
        ax.add_patch(plt.Rectangle((0.1, 0), 0.1, 0.1))

        ax.add_patch(plt.Rectangle((0.4, 0), 0.1, 0.1))
        ax.add_patch(plt.Rectangle((0.5, 0), 0.1, 0.1))

        ax.add_patch(plt.Rectangle((0.8, 0), 0.1, 0.1))
        ax.add_patch(plt.Rectangle((0.9, 0), 0.1, 0.1))

        plt.savefig("elevator.png")
        # plt.show()
        plt.cla()

        # create a panel in the frame
        self.pnl = wx.Panel(self)
        bt_start = wx.Button(self.pnl, label="Start")
        self.Bind(wx.EVT_BUTTON, self.onStartButton, bt_start)
        bt_stop = wx.Button(self.pnl, label="Stop")
        self.Bind(wx.EVT_BUTTON, self.onStopButton, bt_stop)
        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        buttonSizer.Add(bt_start)
        buttonSizer.Add(bt_stop)
        bodySizer = wx.BoxSizer(wx.HORIZONTAL)
        image = wx.Image('elevator.png', wx.BITMAP_TYPE_PNG)
        temp = image.ConvertToBitmap()
        self.bmp = wx.StaticBitmap(parent=self.pnl, bitmap=temp)
        self.split_line = "****************************"
        status_label = self.split_line + "\n当前楼层\n" + self.split_line + "\n当前电梯上乘客\n" + self.split_line + "\n当前乘客需求\n"
        self.time_text = wx.StaticText(self.pnl, label="当前平均周转时间: 无")
        self.status1 = wx.StaticText(self.pnl, label="{}号电梯\n".format(1) + status_label)
        self.status2 = wx.StaticText(self.pnl, label="{}号电梯\n".format(2) + status_label)
        self.status3 = wx.StaticText(self.pnl, label="{}号电梯\n".format(3) + status_label)
        self.status_list = [self.status1, self.status2, self.status3]
        font = self.status1.GetFont()
        font.PointSize += 2
        self.time_text.SetFont(font)
        self.status1.SetFont(font)
        self.status2.SetFont(font)
        self.status3.SetFont(font)
        bodySizer.Add(self.bmp)
        bodySizer.Add(self.status1, 0, wx.LEFT, 10)
        bodySizer.Add(self.status2, 0, wx.LEFT, 10)
        bodySizer.Add(self.status3, 0, wx.LEFT, 10)
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(buttonSizer, 0, wx.ALIGN_CENTER | wx.RIGHT, 100)
        mainSizer.Add(self.time_text, 0, wx.ALIGN_CENTER | wx.RIGHT, 100)
        mainSizer.Add(bodySizer, 0, wx.RIGHT, 100)
        self.pnl.SetSizer(mainSizer)
        self.pnl.Fit()

    def update_elevator(self, elevators):
        global sum_time
        global finished_p
        image = wx.Image('elevator.png', wx.BITMAP_TYPE_PNG)
        temp = image.ConvertToBitmap()
        self.bmp.SetBitmap(temp)
        if finished_p > 0:
            self.time_text.SetLabel("当前平均周转时间: {}".format(round(sum_time/finished_p, 10)))
        for i, elevator in enumerate(elevators):
            status_label = self.split_line + "\n当前楼层\n{}\n".format(round(elevator.cur_floor))
            status_label += self.split_line + "\n当前电梯上乘客\n"
            if elevator.carried:
                for p in elevator.carried:
                    status_label += "ID:{}, R_floor:{}, A_floor:{}\n".format(p.id, p.req_floor, p.arr_floor)
            status_label += self.split_line + "\n当前乘客需求\n"
            if elevator.req_que:
                for p in elevator.req_que:
                    status_label += "ID:{}, R_floor:{}, A_floor:{}\n".format(p.id, p.req_floor, p.arr_floor)
            self.status_list[i].SetLabel("{}号电梯\n".format(i + 1) + status_label)

    def onStartButton(self, evt):
        self.thread = WorkThread()
        self.thread.start()

    def onStopButton(self, evt):
        self.thread.stop()

if __name__ == '__main__':
    app = wx.App()
    frm = ElevatorFrame(None, title='电梯调度模拟')
    frm.Fit()
    frm.Show()
    app.MainLoop()

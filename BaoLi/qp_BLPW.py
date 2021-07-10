import hashlib
import sys
import time
import threading
import requests
import json

from datetime import datetime

from utils import stop_thread


def get_token(s):
    """md5"""
    md5str = s
    m1 = hashlib.md5()
    m1.update(md5str.encode("utf-8"))
    token = m1.hexdigest()
    return token


class Rmzm(object):
    def __init__(self, cookies):
        self.showId = ''
        self.showTime = ''
        self.productId = ''
        self.session = requests.session()
        self.session.cookies = requests.utils.cookiejar_from_dict(cookies)

    def search_info(self, searchInfo):
        time_stamp = str(int(time.time() * 1000))  # 1617671776625
        url = 'https://platformpcgateway.polyt.cn/api/1.0/search/searchTheater'
        search_str = '{"cityId":"","dateInterval":null,"keyWords":"' + searchInfo + '",' \
                                                                                    '"priceZone":"0","requestModel":{"applicationCode":"plat_pc","applicationSource":"plat_pc",' \
                                                                                    '"atgc":"atoken","current":1,"size":10,"timestamp":' + time_stamp + ',"utgc":"utoken"},' \
                                                                                                                                                        '"shelfChannel":"","showTypeId":"","sortType":"sortByTime","timeType":"0"}plat_pc'
        data = {"cityId": "",
                "requestModel": {"applicationSource": "plat_pc", "current": 1, "size": 10,
                                 "atgc": get_token(search_str), "utgc": "utoken",
                                 "timestamp": int(time_stamp), "applicationCode": "plat_pc"}, "dateInterval": None,
                "keyWords": searchInfo, "priceZone": "0", "shelfChannel": "", "showTypeId": "",
                "sortType": "sortByTime", "timeType": "0"}
        res = self.session.post(url, cookies=cookies, data=json.dumps(data),
                                headers={'Content-Type': 'application/json;charset=UTF-8'})
        print(res.text)
        productId = str(res.json().get('data').get('records')[0].get('productId'))
        projectId = str(res.json().get('data').get('records')[0].get('projectId'))
        return productId, projectId

    def get_show_info(self, product_id, project_id):
        time_stamp = str(int(time.time() * 1000))  # 1617671776625
        info_str = '{"productId":"' + product_id + '","projectId":"' + project_id + '","requestModel":{"applicationCode' \
                                                                                    '":"plat_pc",' \
                                                                                    '"applicationSource":"plat_pc","atgc":"atoken","current":1,"size":10,' \
                                                                                    '"timestamp":' + time_stamp + ',"utgc":"utoken"},"theaterId":""}plat_pc'
        url = 'https://platformpcgateway.polyt.cn/api/1.0/show/getShowInfoDetail'
        data = {"productId": product_id, "projectId": project_id, "theaterId": "",
                "requestModel": {"applicationSource": "plat_pc", "current": 1, "size": 10,
                                 "atgc": get_token(info_str), "utgc": "utoken",
                                 "timestamp": int(time_stamp), "applicationCode": "plat_pc"}}
        res = self.session.post(url, cookies=cookies, data=json.dumps(data),
                                headers={'Content-Type': 'application/json;charset=UTF-8'})
        show_info_list = res.json().get('data').get('platShowInfoDetailVOList')
        result_list = []
        try:
            for show_info in show_info_list:
                base_dict = {
                    show_info.get('showTime'): {
                        'showId': str(show_info.get('showId')),
                        'sectionId': str(show_info.get('sectionId')),
                    }
                }
                result_list.append(base_dict)
        except:
            print('获取全部场次出错（showId，sectionId，showTime）')
        return result_list

    def execute_get_empty_seats(self, projectId, sectionId, showId):
        """
        执行获取空座位信息
        :param projectId:
        :param sectionId:
        :param showId:
        :return:dict
        """
        time_stamp = str(int(time.time() * 1000))  # 1617671776625
        # get seat info
        s = '{"projectId":"' + projectId + '","requestModel":{"applicationCode":"plat_pc",' \
                                           '"applicationSource":"plat_pc","atgc":"atoken","current":1,"size":10,' \
                                           '"timestamp":' + time_stamp + ',"utgc":"utoken"},"sectionId":"' + sectionId + '","showId":' + showId + '}'
        add_str = 'plat_pc'
        atgc = get_token(s + add_str)
        url = 'https://platformpcgateway.polyt.cn/api/1.0/seat/getSeatInfo'
        data = {"sectionId": sectionId, "showId": int(showId), "projectId": projectId,
                "requestModel": {"applicationSource": "plat_pc", "current": 1, "size": 10,
                                 "atgc": atgc,
                                 "utgc": "utoken", "timestamp": int(time_stamp), "applicationCode": "plat_pc"}}
        res = self.session.post(url, cookies=cookies, data=json.dumps(data),
                                headers={'Content-Type': 'application/json;charset=UTF-8'})
        print(res.text)
        self.showTime = res.json().get('data').get('showTime')
        self.showId = str(res.json().get('data').get('showMap').get('showId'))
        self.productId = str(res.json().get('data').get('productId'))
        # 获取未售seat+pid
        seatLists = res.json().get('data').get('seatList')
        empty_seat_info = []
        if seatLists:
            for single_seat in seatLists:
                if single_seat.get('statusStr') == '未售':
                    # 把未出售的作为列表做分布式    /  直接break
                    priceId = str(single_seat.get('pid'))
                    seat = str(single_seat.get('sid'))
                    empty_seat_info.append({'priceId': priceId, 'seat': seat})
        return empty_seat_info

    def execute_qp(self, priceId, seat):
        """
        执行抢票
        :param priceId:
        :param seat:
        :return:
        """
        global run_flag
        time_stamp = str(int(time.time() * 1000))  # 1617671776625  1618211492898
        first_tg = '{"channelId":"","priceList":[{"count":1,"freeTicketCount":1,"priceId":' + priceId + ',"seat":' + seat + '}],' \
                                                                                                                            '"projectId":' + self.productId + ',"requestModel":{"applicationCode":"plat_pc","applicationSource":"plat_pc",' \
                                                                                                                                                              '"atgc":"atoken","current":1,"size":10,"timestamp":' + time_stamp + ',"utgc":"utoken"},"seriesId":"",' \
                                                                                                                                                                                                                                  '"showId":"' + self.showId + '","showTime":"' + self.showTime + '"}plat_pc'
        url = 'https://platformpcgateway.polyt.cn/api/1.0/platformOrder/commitOrderOnSeat'
        atgc = get_token(first_tg)
        data = {"channelId": "",
                "priceList": [{"count": 1, "priceId": int(priceId), "seat": int(seat), "freeTicketCount": 1}],
                "projectId": int(self.productId),
                "seriesId": "", "showId": self.showId, "showTime": self.showTime,
                # "checkModel": {
                #     "token": "FFFF0N00000000009D3A:nc_login_h5:1620976469449:0.8165598905050986",
                #     "sessionId": "01wks8yoZBYT5e1noB57MJxqXoNfYixhQ4q8ZlO-WU54FHGwShDtckru4dpXAvvhFCOz-9eDuOH0-6UOyjkEfRSxmQnwnz-yx3HmQ2Ie_PfP1TvQyWMop3wzPzpncbNU9XgUogcxGXazfr80Vhmi_Kt9RN06Rz7CFXeXksVXV3lel75vRxHM5y4YebdTZ_MyrbbK6eWorVK14UI93g2-dKOqiTpln6usAMd5kgJHVo1Lw",
                #     "sig": "05XqrtZ0EaFgmmqIQes-s-CHVDFzDLtfaCZLZRQLtAYyWWIwbN8ZZNvsQvNGwIbjXwjsYb7gasfWkkE8YbC1i8k7Pi-yKh_xdmy1IvV_dG52P5jqBJeAjId25iyVKy_WdV_NFsXrmsPl5Gj8zIPv0xxnSnTKKNuAnFb2Ru7tL2dUFaJN1Gc9vnaYQeNm6xJq0voImOLG43tMyx7jOydVYHR--Sjz3kqGY_vtdXq0tQGeLXXP2L4giAWeflvkHGplpRDzeq59Mt2biziz8VvWYKouL8V1N8Teg5JzxXTpStK1MDObuFxu28qROgwSTmsweKitLnTzOBsmnyEA36GxSsA2vowaE-fSBOmhjXX87l7XRfIq7UNMMGU9CSxydqVcMuJpcdRnWtWPvfLbpqQlDqa1R9pCBUn6iZTWkwYkUrG2xDHgLdBqfqYM5VETjn4tUWHuWPk8wQLtowh3CU9F4ZqXj-KaWJPhHqpebPAmqdJCRnsnRnM4Ivhvp4AeJ1Y8S6nuYl2f243KbqJkHg50ei7Q"
                # },
                "requestModel": {"applicationSource": "plat_pc", "current": 1, "size": 10,
                                 "atgc": atgc, "utgc": "utoken", "timestamp": int(time_stamp),
                                 "applicationCode": "plat_pc"}}
        html = self.session.post(url, data=json.dumps(data), cookies=cookies,
                                 headers={'Content-Type': 'application/json;charset=UTF-8'})
        print(html.text)
        if html.json().get('code') != 200:
            raise ValueError(html)
        uuid = html.json().get('data')
        # 获取 观影人参数
        time_stamp = str(int(time.time() * 1000))  # 1617671776625  1618211492898
        gyr_str = '{"requestModel":{"applicationCode":"plat_pc","applicationSource":"plat_pc",' \
                  '"atgc":"atoken","current":1,"size":10,"timestamp":' + time_stamp + ',"utgc":"utoken"}}plat_pc'
        url = 'https://platformpcgateway.polyt.cn/api/1.0/member/getObserverList'
        data = {"requestModel": {"applicationSource": "plat_pc", "current": 1, "size": 10,
                                 "atgc": get_token(gyr_str),
                                 "utgc": "utoken", "timestamp": int(time_stamp), "applicationCode": "plat_pc"}}
        html = self.session.post(url, data=json.dumps(data), cookies=cookies,
                                 headers={'Content-Type': 'application/json;charset=UTF-8'})
        gyr_info = html.json().get('data')[0]
        name = str(gyr_info.get('name'))
        memberId = str(gyr_info.get('id'))
        # # submit
        time_stamp = str(int(time.time() * 1000))  # 1617671776625
        sub_tg = '{"channelId":null,"consignee":"' + name + '","consigneePhonr":"17857338163","deliveryWay":"01","movieIds":"' + memberId + '",' \
                                                                                                                                            '"orderFreightAmt":0,"payWayCode":"06","requestModel":{"applicationCode":"plat_pc",' \
                                                                                                                                            '"applicationSource":"plat_pc","atgc":"atoken","current":1,"size":10,' \
                                                                                                                                            '"timestamp":' + time_stamp + ',"utgc":"utoken"},"seriesId":"",' \
                                                                                                                                                                          '"uuid":"' + uuid + '"}plat_pc'
        url = 'https://platformpcgateway.polyt.cn/api/1.0/platformOrder/createOrder'
        atgc = get_token(sub_tg)
        data = {"channelId": None, "consignee": name, "consigneePhonr": "17857338163",
                "deliveryWay": "01", "payWayCode": "06",
                "movieIds": memberId, "seriesId": "", "orderFreightAmt": 0, "uuid": uuid,
                "requestModel": {"applicationSource": "plat_pc", "current": 1, "size": 10,
                                 "atgc": atgc, "utgc": "utoken",
                                 "timestamp": int(time_stamp), "applicationCode": "plat_pc"}}
        response = self.session.post(url, data=json.dumps(data), cookies=cookies,
                                     headers={'Content-Type': 'application/json;charset=UTF-8'})
        response_code = str(response.json().get('code'))
        print(response.text)
        if response_code == '200':
            end_time = datetime.now()
            # sys.exit()
            run_flag = 0

    def do_qp_task(self, **kwargs):
        show_time = list(kwargs.keys())[0]
        show_id = kwargs.get(show_time).get('showId')
        section_id = kwargs.get(show_time).get('sectionId')
        empty_seat_infos = s.execute_get_empty_seats(projectId=project_id, sectionId=section_id, showId=show_id)
        print(f'{show_time}获取未售座位成功, 总数:{len(empty_seat_infos)}>>>{empty_seat_infos}')
        # 再起多线程抢票
        for empty_seat_info in empty_seat_infos[:3]:  ### empty_seat_infos可用来指定前排座位
            tt = threading.Thread(target=s.execute_qp, kwargs=empty_seat_info)
            if run_flag == 0:
                end_time = datetime.now()
                print('抢票成功alltime:%s!!!!!!' % (str(end_time - start_time)))
            tt.start()


if __name__ == '__main__':
    # https://www.polyt.cn/search?keyWord=%E4%BF%9D%E5%88%A9%C2%B7%E5%A4%AE%E5%8D%8E%E2%80%9C%E7%A5%9E%E5%B7%9E%E4%B9%9D%E5%9F%8E%EF%BC%8C%E5%85%B1%E4%BA%AB%E6%98%8E%E5%A4%A9%E2%80%9D2021%E6%BC%94%E5%87%BA%E8%A1%8C%E5%8A%A8%20%E5%A4%AE%E5%8D%8E%E7%89%88%E3%80%8A%E5%A6%82%E6%A2%A6%E4%B9%8B%E6%A2%A6%E3%80%8B%E6%AD%A6%E6%B1%89%E7%AB%99
    # 需保证页面上能搜索到
    # 不同账号不同场次同一观影人可买？？？
    searchInfo = '孟京辉经典戏剧作品摇滚音乐剧《空中花园谋杀案》呼和浩特站'    ### 改成你要抢的演出的名称

    cookies = {'Hm_lvt_0cb4627679a11906d6bf0ced685dc014': '1625920613,1625920872',   ### 用你自己账号的cookie 
               'loginSession': '840a5eb28fe9208071becf422e13ad73&&7383efef343f83fb7befa00fe3c9d124',
               'Hm_lpvt_0cb4627679a11906d6bf0ced685dc014': '1625920948'}
              


    s = Rmzm(cookies)
    execute_time_m = 45
    #----------------------------------------
    # while 1:
    #     # logger.info(f'waiting, {datetime.now().minute}:{datetime.now().second}')
    #     if datetime.now().minute == execute_time_m and datetime.now().second == 58:
    start_time = datetime.now()
    # logger.info(f'start_time:{start_time}')
    # product_id, project_id = s.search_info(searchInfo)
    # print('product_id:%s, project_id:%s' % (product_id, project_id))
    # all_show_info_list = s.get_show_info(product_id=product_id, project_id=project_id)
    # product_id = '30551'
    # project_id = '594121812962119680'
    # all_show_info_list = [{'2021-05-28 星期五 14:00': {'showId': '46955', 'sectionId': '46846'}},
    #                       {'2021-05-28 星期五 19:30': {'showId': '47426', 'sectionId': '47296'}},
    #                       {'2021-05-29 星期六 14:00': {'showId': '47427', 'sectionId': '47297'}},
    #                       {'2021-05-29 星期六 19:30': {'showId': '47428', 'sectionId': '47298'}},
    #                       {'2021-05-30 星期日 14:00': {'showId': '47429', 'sectionId': '47299'}},
    #                       {'2021-05-30 星期日 19:30': {'showId': '47430', 'sectionId': '47300'}}]
    # # logger.info(f'总场次数：{len(all_show_info_list)}，场次信息：{all_show_info_list}')
    # # 分布式去抢所有场次的票
    # for single_show_info in all_show_info_list:
    #     run_flag = 1
    #     t = threading.Thread(target=s.do_qp_task, kwargs=single_show_info)
    #     t.start()
    #     # 抢票成功alltime
    #     # 您有待支付的订单
    #-------------------------------------------


    # 查询
    # start_time = datetime.now()
    # logger.info(f'start_time:{start_time}')
    # product_id, project_id = s.search_info(searchInfo)
    # print('product_id:%s, project_id:%s' % (product_id, project_id))
    # all_show_info_list = s.get_show_info(product_id=product_id, project_id=project_id)
    # logger.info(f'总场次数：{len(all_show_info_list)}，场次信息：{all_show_info_list}')


    # single qp test
    # start_time = datetime.now()
    # logger.info(f'start_time:{start_time}')
    product_id, project_id = s.search_info(searchInfo)
    print('product_id:%s, project_id:%s' % (product_id, project_id))
    all_show_info_list = s.get_show_info(product_id=product_id, project_id=project_id)
    # logger.info(f'总场次数：{len(all_show_info_list)}，场次信息：{all_show_info_list}')
    # 分布式去抢所有场次的票
    for single_show_info in all_show_info_list[:10]:  ### 指定某个或某几个场次
        run_flag = 1
        t = threading.Thread(target=s.do_qp_task, kwargs=single_show_info)
        t.start()
    #     # 抢票成功alltime
    #     # 您有待支付的订单
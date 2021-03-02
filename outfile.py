import json
from loguru import logger


class query:
    """易校园查询类
            内部参数:
                headers  -  HTTP协议头\n
                code  -  getCodeV2接口\n
                cookies  -  用户Cookies\n
                areaId  -  学校定位\n
                buildList  -  宿舍列表\n
    """
    def __init__(self, unionId, schoolCode, appId):
        """

        :param unionId: APP学号
        :param schoolCode: 学校代号
        :param appId: appId
        """
        import requests as http
        self.http = http.session()
        logger.debug("Setting session Enabled")
        self.http.headers = {
            "Upgrade-Insecure-Requests": "1",
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
            "User-Agent": "Mozilla/5.0 (Linux; Android 9; Pixel Build/PPR2.181005.003.A1; wv) " \
                          "AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 " \
                          "Chrome/86.0.4240.198 Mobile Safari/537.36 Html5Plus/1.0 " \
                          "(Immersed/24.0)/1.7.6/first " \
                          "ZJYXYwebviewbroswer ZJYXYAndroid tourCustomer /yunmaapp.NET/1.7.6/028c429e110ad45d5dc663b3a182ec51"
        }
        self.unionId = unionId
        logger.debug("Setting unionId: {0}".format(self.unionId))
        self.schoolCode = schoolCode
        logger.debug("Setting schoolCode: {0}".format(self.schoolCode))
        self.appId = appId
        logger.debug("Setting appId: {0}".format(self.appId))
        self.code = self._getcode()
        logger.debug("Setting code: {0}".format(self.code))
        self.http.cookies = self._getUser4Authorize()
        logger.debug("Setting cookies: {0}".format(self.http.cookies))
        self.areaId = self._queryArea()
        logger.debug("Setting areaId: {0}".format(self.areaId))
        self.buildList = self._queryBuilding()
        logger.debug("Setting buildList: {0}".format(str(self.buildList.keys())))

        logger.success("All initializations are ready")

    def _mTextMid(self, sources="", leftStr="", rightStr=""):
        """取中间的文本"""
        index1 = -1
        index2 = -1
        if leftStr != "" and rightStr != "":
            index1 = sources.find(leftStr) + len(leftStr)
            index2 = index1 + sources[index1:].find(rightStr)
            rStr = sources[index1:index2]
        return rStr

    def _getcode(self):
        """
        :return:code
        """
        url = "https://auth-dxid11.xiaofubao.com/authoriz/getCodeV2?bindSkip=1&authType=2&appid={" \
              "0}&callbackUrl=https%3A%2F%2Fapplication.xiaofubao.com%2F%23%2FpayWaterFee%3Ftype%3D1%26schoolCode%3D{" \
              "1}%26unionid%3D{2}%26platform%3DYUNMA_APP&unionid={3}&schoolCode={4}".format(self.appId,
                                                                                            self.schoolCode,
                                                                                            self.unionId,
                                                                                            self.unionId,
                                                                                            self.schoolCode)
        res = self.http.get(url=url)
        logger.debug("HttpCode: {0}".format(str(res.status_code)))
        if res.status_code != 200:
            exit(1)
        rStrs = res.text
        code = self._mTextMid(rStrs, leftStr="var code = \"", rightStr="\";")
        return code

    def _getUser4Authorize(self):
        """
        :return:Cookies
        """
        url = "https://application.xiaofubao.com/app/login/getUser4Authorize"
        data = "code={0}&userId=&schoolCode=&platform=YUNMA_APP".format(self.code)
        self.http.headers["deviceId"], self.http.headers["OSVersion"], self.http.headers["timestamp"], self.http.headers["userId"], self.http.headers["signature"], self.http.headers[
            "appId"], self.http.headers["token"] = "", "", "", "", "", "", ""
        self.http.headers["Referer"] = "https://application.xiaofubao.com/"
        res = self.http.post(url=url, data=data)
        logger.debug("HttpCode: {0}".format(str(res.status_code)))
        if res.status_code != 200:
            exit(1)
        return res.cookies

    def _queryArea(self):
        """
        :return: 学校Code
        """
        url = "https://application.xiaofubao.com/app/electric/queryArea"
        data = "type=1&areaCode=&platform=YUNMA_APP"
        res = self.http.post(url=url, data=data)
        logger.debug("HttpCode: {0}".format(str(res.status_code)))
        if res.status_code != 200:
            exit(1)
        jsr = json.loads(res.text)
        try:
            ret = jsr["rows"][0]["id"]
        except KeyError:
            logger.error("KeyError: Incorrectly parse message")
            exit(1)
        return ret

    def _queryBuilding(self):
        """
        :return: 宿舍列表
        """
        url = "https://application.xiaofubao.com/app/electric/queryBuilding"
        data = "areaId={0}&platform=YUNMA_APP".format(self.areaId)
        res = self.http.post(url=url, data=data)
        logger.debug("HttpCode: {0}".format(str(res.status_code)))
        if res.status_code != 200:
            exit(0)
        ret = res.text
        lists = {}
        jsr = json.loads(ret)
        for data in jsr["rows"]:
            lists[data["buildingName"]] = data["buildingCode"]
        return lists

    def _queryFloor(self, buildName):
        """
        :param buildName: 学生公寓的序号  如 :01 ,11 ,13
        :return: 楼层信息
        """
        url = "https://application.xiaofubao.com/app/electric/queryFloor"
        try:
            self.buildCode = self.buildList["学生公寓{0}".format(buildName)]  # 匹配buildCode(The buildName format: 03)
            data = "areaId={0}&buildingCode={1}&platform=YUNMA_APP".format(self.areaId, self.buildCode)
        except KeyError:
            logger.error("UnKnownError: Incorrectly parse buildName")
            exit(1)
        res = self.http.post(url=url, data=data)
        logger.debug("HttpCode: {0}".format(str(res.status_code)))
        if res.status_code != 200:
            exit(1)
        ret = res.text
        lists = {}
        jsr = json.loads(ret)
        for data in jsr["rows"]:
            lists[data["floorName"]] = data["floorCode"]
        self.floorList = lists

    def _queryRoom(self, floorName):
        """
        :param floorName: 楼层序号
        :return: 房间号列表
        """
        url = "https://application.xiaofubao.com/app/electric/queryRoom"
        try:
            self.floorCode = self.floorList[floorName + "层"]  # 匹配floorCode(The floorName format: 2)
            data = "areaId={0}&buildingCode={1}&floorCode={2}&platform=YUNMA_APP".format(self.areaId, self.buildCode,
                                                                                         self.floorCode)
        except KeyError:
            logger.error("UnKnownError: Incorrectly parse floorName")
            exit(0)
        res = self.http.post(url=url, data=data)
        logger.debug("HttpCode: {0}".format(str(res.status_code)))
        if res.status_code != 200:
            exit(0)
        ret = res.text
        lists = {}
        jsr = json.loads(ret)
        for data in jsr["rows"]:
            lists[data["roomName"]] = data["roomCode"]
        self.roomList = lists

    def _queryRoomSurplus(self, roomName):
        """
        :param roomName: 房间序号
        :return: 电费余额
        """
        url = "https://application.xiaofubao.com/app/electric/queryRoomSurplus"
        try:
            self.roomCode = self.roomList[roomName]  # 匹配roomCode(The roomName format: 101)
            data = "areaId={0}&buildingCode={1}&floorCode={2}&roomCode={3}" \
                   "&areaCode=&platform=YUNMA_APP".format(self.areaId, self.buildCode, self.floorCode, self.roomCode)
        except KeyError:
            logger.error("UnKnownError: Incorrectly parse roomName")
            exit(0)
        res = self.http.post(url=url, data=data)
        logger.debug("HttpCode: {0}".format(str(res.status_code)))
        if res.status_code != 200:
            exit(0)
        ret = res.text
        lists = {}
        jsr = json.loads(ret)
        try:
            surplusBill = jsr["data"]["surplus"]
        except KeyError:
            logger.error("KeyError: Incorrectly parse surplus")
            exit(0)
        return surplusBill

    def queryRoomSurplus(self, buildName, floorName, roomName):
        """
        :param buildName: 学生公寓序号
        :param floorName: 楼层
        :param roomName: 房间号
        :return: 电费余额
        """
        self._queryFloor(buildName)
        self._queryRoom(floorName)
        surplusBill = self._queryRoomSurplus(roomName)
        return surplusBill


# 必要参数-----------------------
unionId = ""
schoolCode = ""
appId = ""
#   END-------------------------
qy = query(unionId, schoolCode, appId)
queryTable = input("\033[1;36m  Format of input : [buildName-roomName]\n  Example : 11-307\n    \033[0m")
args = queryTable.split("-")
if len(args) != 2 or len(args[0]) != 2 or len(args[1]) != 3:
    logger.error("The content you entered is incorrectly formatted")
    exit(1)
buildName = args[0]
floorName = args[1][:1]
roomName = args[1]
surplus = qy.queryRoomSurplus(buildName, floorName, roomName)
logger.success("SOC : {0}°".format(str(surplus)))

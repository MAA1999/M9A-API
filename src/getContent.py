import re
import json
import requests


CN_CONTENT_URL = "https://notice.sl916.com/noticecp/client/query"
OTHER_URL = "https://re1999.bluepoch.com/activity/official/websites/information/query"

def getContent(resource:str):
    if resource == "cn":
        pattern = r'(\d+\.\d+)\s*「([^」]+)」版本活动一览'
        data = json.loads(requests.get(url=CN_CONTENT_URL,params={"gameId": 50001, "channelId": 100, "subChannelId": 1009, "serverType": 4}).text)
        if data['msg'] == "成功":
            data = data['data']
        for item in data:
            item = item["contentMap"]["zh-CN"]
            title, content = item['title'], item['content']
            match = re.search(pattern, title)
            if match:
                version = match.group(1)
                version_name = match.group(2)
                return True, (version, version_name, content)
    elif resource == "en":
        pattern = r'Ver\.\s+(\d+\.\d+)\s+\[([^\]]+)\]\s+Preview'
        data = json.loads(requests.post(url=OTHER_URL,json={"informationType": 2, "current": 1, "pageSize": 5, "gameId": 60001}).text)
        if data['msg'] == "成功":
            data = data['data']['pageData']
        for item in data:
            title, content = item['title'], item['content']
            match = re.search(pattern, title)
            if match:
                version = match.group(1)
                version_name = match.group(2)
                return True, (version, version_name, content)
    elif resource == "jp":
        pattern = r'Ver\.\s+(\d+\.\d+)\s*「([^」]+)」情報一覧'
        data = json.loads(requests.post(url=OTHER_URL,json={"informationType": 2, "current": 1, "pageSize": 5, "gameId": 70001}).text)
        if data['msg'] == "成功":
            data = data['data']['pageData']
        for item in data:
            title, content = item['title'], item['content']
            match = re.search(pattern, title)
            if match:
                version = match.group(1)
                version_name = match.group(2)
                return True, (version, version_name, content)

    return False, None

if __name__ == "__main__":
    data0 = getContent("cn")
    data1 = getContent("en")
    data2 = getContent("jp")

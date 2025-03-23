import re
import json
import requests


CN_CONTENT_URL = "https://notice.sl916.com/noticecp/client/query"
OTHER_URL = "https://re1999.bluepoch.com/activity/official/websites/information/query"

PATTERNS = {
    "cn": r'(\d+\.\d+)\s*「([^」]+)」版本活动一览',
    "en": r'Ver\.\s+(\d+\.\d+)\s+\[([^\]]+)\]\s+Preview',
    "jp": r'Ver\.\s+(\d+\.\d+)\s*「([^」]+)」情報一覧'
}   

GAME_IDS = {
    "cn": 50001,
    "en": 60001,
    "jp": 70001
}

def getContent(resource:str):
    if resource == "cn":
        data = json.loads(requests.get(url=CN_CONTENT_URL,params={"gameId": 50001, "channelId": 100, "subChannelId": 1009, "serverType": 4}).text)
        if data['msg'] == "成功":
            data = data['data']
            for item in data:
                item = item["contentMap"]["zh-CN"]
                title, content = item['title'], item['content']
                match = re.search(PATTERNS["cn"], title)
                if match:
                    return True, (resource, match.group(1), match.group(2), content)
    elif resource in ["en", "jp"]:
        data = json.loads(requests.post(url=OTHER_URL,json={"informationType": 2, "current": 1, "pageSize": 5, "gameId": GAME_IDS[resource]}).text)
        if data['msg'] == "成功":
            data = data['data']['pageData']
            for item in data:
                title, content = item['title'], item['content']
                match = re.search(PATTERNS["en"], title)
                if match:
                    return True, (resource, match.group(1), match.group(2), content)
    return False, None

if __name__ == "__main__":
    data0 = getContent("cn")
    data1 = getContent("en")
    data2 = getContent("jp")

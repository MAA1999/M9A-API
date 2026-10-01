#!/usr/bin/env python3
"""
Generate M9A/api/version/stable.json — 聚合 M9A 最新 Release 的信息。

站点（1999.fan）不直连 api.github.com：GitHub API 有 60 次/小时/IP 的匿名限流，
且在国内网络下经常不可达。这里在构建期把 releases/latest 抓下来、裁剪成稳定的
schema，随 Pages 一起发布：

    https://api.1999.fan/api/version/stable.json

schema 只保留站点真正要用的字段，因此上游 GitHub 改变响应结构时，站点不受影响。
每个 asset 预留 mirrors 字段，用于将来挂镜像/加速直链（Mirror酱 需要 CDK，
无法在这里生成直链，站点仍以带参数的项目页链接作为加速入口）。

内容无变化时不写文件，避免定时任务产生无意义的提交。
"""

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = "MAA1999/M9A"
API_URL = f"https://api.github.com/repos/{REPO}/releases/latest"
OUTPUT = (
    Path(__file__).resolve().parent.parent / "M9A" / "api" / "version" / "stable.json"
)


def fetch_release() -> dict:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "M9A-API-generate-version",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(API_URL, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def to_stable(release: dict) -> dict:
    return {
        "version": release["tag_name"],
        "name": release.get("name") or release["tag_name"],
        "published_at": release["published_at"],
        "html_url": release["html_url"],
        "assets": [
            {
                "name": asset["name"],
                "size": asset["size"],
                "url": asset["browser_download_url"],
                "mirrors": [],
            }
            for asset in release.get("assets", [])
        ],
        "updated": int(datetime.now(timezone.utc).timestamp() * 1000),
    }


def without_timestamp(data: dict) -> dict:
    return {key: value for key, value in data.items() if key != "updated"}


def main() -> int:
    try:
        release = fetch_release()
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as error:
        print(f"Error: 获取 {API_URL} 失败：{error}", file=sys.stderr)
        return 1

    stable = to_stable(release)

    if OUTPUT.exists():
        with open(OUTPUT, "r", encoding="utf-8") as f:
            existing = json.load(f)
        if without_timestamp(existing) == without_timestamp(stable):
            print(f"[skip] 无变化，保持 {OUTPUT}")
            return 0

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(stable, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"[ok] Generated: {OUTPUT} ({stable['version']}, {len(stable['assets'])} assets)")
    return 0


if __name__ == "__main__":
    exit(main())

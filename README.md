# SwClass 行业分类服务

这个小服务会定期下载申万行业分类压缩包，解压后读取
`最新个股申万行业分类(完整版-截至7月末).xlsx`，生成三级行业到股票代码列表的 JSON，并通过带 token 的 HTTP 接口提供数据。

## 初始化

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

RAR 解压通过 Python 包 `rarfile` 处理归档条目，并使用 `unar` 作为 RAR5 解码后端。解压后会校验目标 xlsx 是否存在，避免空解压被当成成功。

## 手动刷新数据

```bash
. .venv/bin/activate
python -m swclass_app refresh
```

输出文件：

```text
data/swclass_industry_stocks.json
data/swclass_refresh_state.json
```

JSON 结构：

```json
[
  {
    "name": "一级行业名",
    "children": [
      {
        "name": "二级行业名",
        "children": [
          {
            "name": "三级行业名",
            "codes": ["个股代码1", "个股代码2"]
          }
        ]
      }
    ]
  }
]
```

## 启动接口

```bash
. .venv/bin/activate
export SWCLASS_API_TOKEN="your-token"
python -m swclass_app serve --host 0.0.0.0 --port 5000
```

接口：

```bash
curl -H "Authorization: Bearer your-token" \
  http://127.0.0.1:5000/api/swclass
```

健康检查：

```bash
curl http://127.0.0.1:5000/health
```

`/health` 会返回最近一次下载检查时间 `last_checked_at`、最近一次 xlsx 内容实际变化时间
`last_updated_at`，以及当前 xlsx 的 `xlsx_md5`、`xlsx_sha256` 和文件大小。刷新时会用
xlsx 哈希和上一轮记录对比；哈希不变时，`last_checked_at` 会更新，`last_updated_at` 保持不变。

服务启动后会开启后台线程，按服务器本地时间每天 07:00 刷新一次。刷新失败时不会删除旧 JSON。
如果启动时发现 `data/swclass_industry_stocks.json` 不存在，服务会先自动尝试刷新一次；
如果这次刷新失败，服务仍会启动，数据接口继续返回 `503 data_not_ready`，等待后续手动或定时刷新成功。

## Docker Compose 部署

基础镜像：

```text
swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/library/python:3.13-slim-bookworm
```

这个镜像对应 Docker Hub 的 `python:3.13-slim-bookworm`。构建时会安装 Debian 包 `unar`、`tzdata`、`ca-certificates`。

如果要临时换成其他镜像源：

```bash
export PYTHON_BASE_IMAGE="你的镜像源/python:3.13-slim-bookworm"
```

启动：

```bash
export SWCLASS_API_TOKEN="your-token"
export TZ="Asia/Shanghai"
docker compose up -d --build
```

Podman Compose：

```bash
export SWCLASS_API_TOKEN="your-token"
export TZ="Asia/Shanghai"
podman compose up -d --build
```

`podman compose` 需要本机安装 compose provider，例如 `podman-compose` 或 Docker Compose 插件。只安装 Podman CLI 时，`podman compose` 可能会报找不到 provider。

访问：

```bash
curl -H "Authorization: Bearer your-token" \
  http://127.0.0.1:5000/api/swclass
```

服务会加入外部网络 `swclass_industry_api_network`。启动前需要先确保网络存在：

```bash
podman network create swclass_industry_api_network
```

数据会通过 Compose volume `swclass_industry_api_data` 绑定到宿主机 `/opt/docker-data/swclass-industry-api/`，容器内路径是 `/app/data`。启动前需要确保宿主机目录存在：

```bash
mkdir -p /opt/docker-data/swclass-industry-api
```

## 测试

```bash
. .venv/bin/activate
pytest
```

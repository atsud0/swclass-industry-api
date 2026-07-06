# SwClass 行业分类服务

这个小服务会定期下载申万行业分类压缩包，解压后读取
`最新个股申万行业分类(完整版-截至7月末).xlsx`，生成三级行业到股票代码列表的 JSON，并通过带 token 的 HTTP 接口提供数据。

## 初始化

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

RAR 解压通过 Python 包 `libarchive-c` 调用系统 `libarchive` 完成，不再直接调用 `7z`、`unrar` 等命令。运行环境需要可加载的 `libarchive` 动态库。

## 手动刷新数据

```bash
. .venv/bin/activate
python -m swclass_app refresh
```

输出文件：

```text
data/swclass_industry_stocks.json
```

JSON 结构：

```json
[
  {"三级行业名": ["个股代码1", "个股代码2"]}
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

服务启动后会开启后台线程，按服务器本地时间每天 07:00 刷新一次。刷新失败时不会删除旧 JSON。

## Docker Compose 部署

基础镜像：

```text
swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/library/python:3.13-slim-bookworm
```

这个镜像对应 Docker Hub 的 `python:3.13-slim-bookworm`。构建时会安装 Debian 包 `libarchive13`、`tzdata`、`ca-certificates`。

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

数据会持久化在 Compose volume `swclass-data` 中。

## 测试

```bash
. .venv/bin/activate
pytest
```

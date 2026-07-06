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

## 测试

```bash
. .venv/bin/activate
pytest
```

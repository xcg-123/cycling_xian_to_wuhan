# 真实 OSM 道路几何测试成果

本目录保存 2026-11-10 获取的公共道路样本，2026-11-12 故障恢复后经原始 XML 重新提取复核。不是私人行程、实骑 GPS 记录或经过安全审查的骑行导航路线。

- 来源：OpenStreetMap API，完整请求 URL、UTC 获取时间、原始响应 SHA-256 见 `osm-acquisition.json`。
- 对象：兴庆路三个顺序相接的 way：263609699 → 763969650 → 763969656；按原始节点方向提取，不用直线补缺口。
- `osm-road-sample.json`：25 点、3 段，椭球几何距离 2791.911 m；含道路 ID、节点 ID、原始版本、道路更新时间及必要标签，不含贡献者用户名或 uid。
- `TEST_ONLY-osm-road-geometry.gpx`：原生 OSM WGS84 经纬度原样写入 GPX，保留分段、来源、获取时间和许可；没有从高德 GCJ-02 转换。完整轨迹坐标逐点与提取结果一致。
- 几何核查只说明数据链条一致，不能证明实际位置精度、路面适配、自行车合法通行或当天路况。仅第一段有 bicycle=yes 标签，其余两段未知。无高程、无独立路由距离、无实地测量校验；未完成官方 GPX XSD 校验、行者导入和设备实测。
- `connectivity.json`：当时匿名网络连通性观察，源站 HTTP 200 不等于高德鉴权成功。第三方页面/贡献者正文已从公开记录中省略。
- 原始 OSM XML、官方文档快照和带凭据调用后的响应留在 Git 忽略的 `data/private/`，没有提交原始响应或凭据。

## 数据许可

© OpenStreetMap contributors。OSM 路网及本目录抽取的数据部分沿用 [Open Database License 1.0](https://opendatacommons.org/licenses/odbl/1-0/)，署名和使用说明见 https://www.openstreetmap.org/copyright 。公开抽取保留完整坐标与相关道路属性，供复核；上述许可不意味着数据正确、道路可通行或获官方安全认证，也不用于给本仓库其他来源的文件重新授权。

## 从本地保留的原始文件复现

在仓库根目录执行，使用新的输出位置以避免覆盖已保存证据：

```bash
.venv/bin/python scripts/extract_osm_sample.py data/private/osm-sample.xml \
  --ways 263609699 763969650 763969656 \
  --source-url 'https://api.openstreetmap.org/api/0.6/map?bbox=108.975,34.245,108.985,34.255' \
  --retrieved-at '2026-11-10T15:10:12.148974+00:00' \
  --output /tmp/osm-recheck.json --gpx /tmp/TEST_ONLY-osm-recheck.gpx
```

这里的获取时间只属于已保留的原始响应。重新联网取数必须记录新的时间和哈希，不可复用旧时间；道路版本也可能变化。GitHub 使用者无需原始私有快照即可对公开 JSON/GPX 运行 23 项现有测试，但无法据此重新核对未公开完整响应的哈希。

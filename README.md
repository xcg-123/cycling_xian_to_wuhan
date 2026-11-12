# 西安—武汉公路车骑行规划

研究开始：2026-11-10；最近恢复复核：2026-11-12；计划出行：2027 年 7—8 月。

最新进展：[真实地图数据接入验证报告](docs/真实地图数据接入验证报告.md)顶部为 **2026-11-12 故障恢复记录**。原工作区未提交成果已恢复并备份，23 项测试复跑通过（2 项真实 OSM 数据测试，21 项合成/程序行为测试）。

已保留[兴庆路 2.792 km 道路几何及测试 GPX](data/evidence/phase4/README.md)，25 点、3 段，原生 WGS84。**这是公共路网几何样本，未获自行车全程通行、路面适配或安全验证，不能用作最终路书。** 高德鉴权仍待纠正 HTTP 密钥目标域名 `resapi.amap.com` → `restapi.amap.com`；网络白名单已含正确域名。未验证 GCJ-02→WGS84 转换，也未生成高德真实路线 GPX。

原始 XML、接口响应和文档快照留在忽略的 `data/private/`；受限备份在 `/workspace/recovery-backups/20261112T063529Z/`。私有数据尚无已验证的异地副本，更换实例前应安全保存。以下七份报告保留第一阶段的历史证据状态。

## 阅读入口
1. [项目目标与已知条件](docs/项目目标与已知条件.md)
2. [技术可行性验证报告](docs/技术可行性验证报告.md)
3. [候选骑行走廊研究](docs/候选骑行走廊研究.md)
4. [秦岭及其他特殊路段初步分析](docs/秦岭及其他特殊路段初步分析.md)
5. [数据来源与可信度记录](docs/数据来源与可信度记录.md)
6. [跨层级风险与遗漏审查](docs/跨层级风险与遗漏审查.md)
7. [下一阶段执行方案](docs/下一阶段执行方案.md)

建议优先核实 A：蓝田—商洛—南阳—随州方向，以及 B：宁陕—安康—十堰—襄阳方向。C：潼关—豫西方向保留为绕行研究。三者都未证明全程可执行；桥隧、旧路、路面和汉阳进城是优先核查项。

## 复现
使用现有 checkout，不需要创建 worktree。Python 3.12，当前无后台服务。
```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
.venv/bin/python -m unittest discover -s tests -v
python3 scripts/probe_sources.py
python3 scripts/probe_sources.py --software
.venv/bin/python scripts/analyze_gpx.py /path/to/authorized-wgs84-track.gpx
```
依赖已锁版本，但未锁 wheel 哈希或承诺跨平台完全一致；安装保留 TLS 验证。测试数据仅在内存中合成，不代表实际道路。

- `scripts/probe_sources.py`：小规模公开 URL 访问检查，4 并发、22 秒超时，保存响应/错误/时间/哈希。默认覆盖旧记录，历史研究应先归档 evidence。
- `scripts/amap_probe.py`：v5 骑行短段实验工具（当前字段适配待真实响应复核），必须安全配置 `AMAP_API_KEY` 后运行。只输出原始 JSON，不转换坐标、不导出 GPX。输入服务要求的坐标，以 `--help` 查看参数。未完成真实成功调用。
- `scripts/analyze_gpx.py`：WGS84 轨迹分段距离、缺失高程和稀疏边诊断。不会证明路线合法或适合公路车，原始爬升不等于可信爬升。
- `data/evidence/`：实测记录和第三方来源快照；来源 URL、抓取时间及 SHA-256 在 JSON 中。
- `data/network_requirements.json`：待按需添加的域名，不是已应用的网络配置。

密钥放环境安全配置，禁止提交到 Git。公开第三方快照前复核源许可证；收到的个人 GPX 默认先放仓库外。第一阶段提交已推送；后续保存状态见 Git 日志和最新报告。

新增工具：`diagnose_network.py --output <新文件>` 做匿名代表性探测；`route_pipeline.py --help` 查看响应审查/GPX 输出；`verify_repository.py` 检查历史哈希和明显凭据。高德客户端需显式 `--input-crs GCJ-02`；禁止将 GCJ-02 坐标直接导出为 WGS84 GPX。

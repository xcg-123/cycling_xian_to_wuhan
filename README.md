# 西安—武汉公路车骑行规划：第一阶段

研究日期：2026-11-10；计划出行：2027 年 7—8 月。

**当前成果是技术验证与候选走廊研究，不是可出发路书。** 已运行本地分析工具及 7 项测试，20 项地图/气象等站点请求被云代理拒绝，5 份官方开源文档/配置读取成功。尚无真实路线或 DEM；未生成 GPX，没有最终路线里程。

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
- `scripts/amap_probe.py`：待官方当前文档复核的 v4 骑行短段实验工具，必须安全配置 `AMAP_API_KEY` 后运行。只输出原始 JSON，不转换坐标、不导出 GPX。输入服务要求的坐标，以 `--help` 查看参数。未完成真实成功调用。
- `scripts/analyze_gpx.py`：WGS84 轨迹分段距离、缺失高程和稀疏边诊断。不会证明路线合法或适合公路车，原始爬升不等于可信爬升。
- `data/evidence/`：实测记录和第三方来源快照；来源 URL、抓取时间及 SHA-256 在 JSON 中。
- `data/network_requirements.json`：待按需添加的域名，不是已应用的网络配置。

密钥放环境安全配置，禁止提交到 Git。公开第三方快照前复核源许可证；收到的个人 GPX 默认先放仓库外。当前文件未提交或推送到 GitHub。

# git-archaeology

本地 CLI。顺着 Git 历史看代码是从哪一次提交开始变差的，并写出 Markdown 和 HTML 报告。

报告按代码维度分成三块：

- **多类演化**：同一次提交里，两个及以上类的圈复杂度一起变化
- **单类演化**：每个类自己的复杂度曲线、起点、现状、最大跳变和提交人
- **模块**：按仓库顶层目录归类，带提交人、变化前后和幅度

类名来自 `Class::method`。没有挂在类上的自由函数不会进入前两块。

## 环境

- Python 3.10+
- Git ≥ 2.30
- 语言：Python、JavaScript、TypeScript、Java

## 安装

在本仓库根目录：

```bash
pip install -e ".[dev]"
```

`git-arch` 若未进 PATH，用模块入口：

```bash
python -m git_arch --help
```

## 使用

在目标 Git 仓库里：

```bash
git-arch init
git-arch analyze
```

分析别的仓库：

```bash
python -m git_arch analyze --repo G:\code\aurora --format both,json
```

默认写出：

- `archaeology-report.md`
- `archaeology-report.html`

HTML 顶部可在「多类演化 / 单类演化 / 模块」之间切换。打开 HTML 看曲线和对比条，Markdown 是同一套数据的表格。

## 命令

| 命令 | 作用 |
|---|---|
| `init` | 写入 `.git-arch.yml`，并提示忽略 `.git-arch/` |
| `analyze` | 扫描历史、算指标、检测拐点、写报告 |
| `explain <commit>` | 解释某次提交上的拐点（需已有 `archaeology-report.json`） |
| `hotspots` | 只列热点文件 |
| `timeline` | 在终端打印拐点时间线 |
| `version` | 打印版本 |

`analyze` 常用参数：

| 参数 | 说明 |
|---|---|
| `--repo` | Git 仓库路径，默认当前目录 |
| `--path` | 只分析该路径下的文件 |
| `--since` / `--until` | 时间范围 |
| `--branch` | 分支，默认当前 |
| `--max-commits` | 只保留最近 N 个相关提交 |
| `--metrics` | `complexity,churn_complexity,ownership_fragmentation` |
| `--sensitivity` | `low` / `medium` / `high` |
| `--format` | `both`（md+html）、`md`、`html`、`json`，可逗号组合，如 `both,json` |
| `--output` / `-o` | 输出基名或文件路径，默认 `archaeology-report` |
| `--incremental` | 只接上次运行之后的新提交 |
| `--no-cache` | 不读缓存 |

## 指标

| 指标 | 含义 |
|---|---|
| `complexity` | 文件圈复杂度（lizard），并按类拆成 `Class::method` |
| `churn_complexity` | 累计改动次数 × 当前复杂度 |
| `ownership_fragmentation` | blame 贡献者分布的归一化熵 |

变点默认用 PELT。序列短于 20 个点时，改用滑动窗口阈值。同一提交上的多个跳变会合并成一个腐化事件。

只跟踪仍然活在当前 HEAD 上的文件（`git log --follow`），已删除文件不进热点。

## 配置

`git-arch init` 生成 `.git-arch.yml`。命令行覆盖配置文件。可关指标、调敏感度、改忽略路径（如 `vendor/**`、`**/*.min.js`）。

复杂度结果按 blob hash 缓存在 `.git-arch/cache/`。工具版本或指标配置变了会重新计算。

## 开发

```bash
pytest -q
```

设计说明见 [技术方案.md](./技术方案.md)。

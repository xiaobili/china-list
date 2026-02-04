# China List Config Converter

将 [Loyalsoldier/v2ray-rules-dat](https://github.com/Loyalsoldier/v2ray-rules-dat) 配置文件自动转换为 AdGuard Home 兼容格式的自动化脚本工具。

## 功能特性

- 🔧 **自动化处理**: 一键下载、转换、合并配置文件
- 🌐 **双源支持**: 支持国内(Apple、Google、通用)和国外代理域名分类
- ⚙️ **灵活配置**: 可分别为国内外域名指定不同的DNS服务器
- 🔄 **智能重试**: 内置网络重试机制，提高下载成功率
- 📝 **格式转换**: 将纯域名列表自动转换为 AdGuard Home 兼容格式
- 🛡️ **安全保障**: 自动添加推荐的安全DNS上游服务器
- ♻️ **智能去重**: 自动去除重复域名配置，避免冲突
- 📁 **分层目录**: 采用清晰的目录结构组织文件

## 脚本版本

本项目提供两个版本的转换脚本：

### Python版本 (推荐)
文件: `adguardhome_dns.py`
- 更好的跨平台兼容性
- 更清晰的错误处理
- 更详细的进度反馈
- 支持更多自定义选项
- **新增**: 智能去重功能，避免重复域名配置
- **新增**: 分层目录结构，便于文件管理

### Shell版本 (传统)
文件: `dnsmasq_to_adg.sh`
- 轻量级，无需额外依赖
- 适合Linux/macOS环境
- 经过充分测试的稳定版本

## 工作原理

脚本会自动执行以下步骤：

1. 从 [Loyalsoldier/v2ray-rules-dat](https://github.com/Loyalsoldier/v2ray-rules-dat) 获取最新release
2. 下载国内域名列表：`apple-cn.txt`, `google-cn.txt`, `china-list.txt`
3. 下载国外代理域名列表：`proxy-list.txt`, `gfw.txt`, `greatfire.txt`
4. 将纯域名格式转换为 AdGuard Home 的 `[/domain/]dns_server` 格式
5. 支持为国内外域名分别配置不同的DNS服务器
6. **智能去重**: 自动检测并去除重复的域名配置
7. 合并所有配置文件并添加推荐的上游DNS服务器
8. **分层输出**: 原始和转换文件保存在 `configs/` 子目录，合并文件保存在根目录

## 目录结构

执行脚本后会生成以下目录结构：

```
[指定的输出目录]/
├── chinalist-for-adguard.txt     # 最终合并的AdGuard Home配置文件（已去重）
└── configs/                      # 原始文件和转换文件存放目录
    ├── apple-cn.txt              # Apple国内域名原始列表
    ├── google-cn.txt             # Google国内域名原始列表
    ├── china-list.txt            # 通用国内域名原始列表
    ├── proxy-list.txt            # 国外代理域名原始列表
    ├── gfw.txt                   # GFW列表原始文件
    ├── greatfire.txt             # GreatFire列表原始文件
    ├── apple-cn.adg.txt          # Apple国内域名AdGuard格式
    ├── google-cn.adg.txt         # Google国内域名AdGuard格式
    ├── china-list.adg.txt        # 通用国内域名AdGuard格式
    ├── proxy-list.adg.txt        # 国外代理域名AdGuard格式
    ├── gfw.adg.txt               # GFW列表AdGuard格式
    └── greatfire.adg.txt         # GreatFire列表AdGuard格式
```

## 去重功能说明

### 为什么需要去重？
- 不同来源的域名列表可能存在重复项
- 重复的域名配置可能导致解析冲突
- 减少配置文件大小，提高AdGuard Home性能

### 去重规则
- 按域名进行去重（不区分DNS服务器）
- 保留首次出现的域名配置
- 在统计信息中显示去重结果

### 去重示例
```
原始配置：
[/google.com/]114.114.114.114  # 国内配置
[/google.com/]8.8.8.8          # 国外配置（重复）
[/baidu.com/]114.114.114.114   # 国内配置
[/baidu.com/]114.114.114.114   # 国内配置（重复）

去重后：
[/google.com/]114.114.114.114  # 保留首次出现的配置
[/baidu.com/]114.114.114.114   # 保留首次出现的配置
```

## 使用方法

### Python版本使用 (推荐)

```bash
# 使用默认DNS服务器配置和默认输出目录
python3 adguardhome_dns.py

# 指定统一的DNS服务器（国内外都使用相同DNS）
python3 adguardhome_dns.py 114.114.114.114

# 指定多个统一DNS服务器
python3 adguardhome_dns.py 114.114.114.114 223.5.5.5

# 分别指定国内外DNS服务器
python3 adguardhome_dns.py 114.114.114.114 --foreign 8.8.8.8

# 指定多个国内外DNS服务器
python3 adguardhome_dns.py 114.114.114.114 223.5.5.5 --foreign 8.8.8.8 1.1.1.1

# 只指定国外DNS（国内使用默认）
python3 adguardhome_dns.py --foreign 8.8.8.8

# 指定自定义输出目录
python3 adguardhome_dns.py --output /path/to/my/configs

# 同时指定DNS服务器和输出目录
python3 adguardhome_dns.py 114.114.114.114 --output ./my-adguard-configs

# 完整示例：指定DNS服务器和自定义输出目录
python3 adguardhome_dns.py 114.114.114.114 223.5.5.5 --foreign 8.8.8.8 1.1.1.1 --output /home/user/adguard-configs

# 查看帮助
python3 adguardhome_dns.py --help
```

### Shell版本使用

```bash
# 使用默认DNS服务器配置
./dnsmasq_to_adg.sh

# 指定统一的DNS服务器（国内外都使用相同DNS）
./dnsmasq_to_adg.sh 114.114.114.114

# 指定多个统一DNS服务器
./dnsmasq_to_adg.sh 114.114.114.114 223.5.5.5

# 分别指定国内外DNS服务器
./dnsmasq_to_adg.sh 114.114.114.114 --foreign 8.8.8.8

# 指定多个国内外DNS服务器
./dnsmasq_to_adg.sh 114.114.114.114 223.5.5.5 --foreign 8.8.8.8 1.1.1.1

# 只指定国外DNS（国内使用默认）
./dnsmasq_to_adg.sh --foreign 8.8.8.8

# 查看帮助
./dnsmasq_to_adg.sh --help
```

## 配置示例

生成的 `chinalist-for-adguard.txt` 文件格式如下：

```
# AdGuard Home 中国域名列表配置
# 生成时间: Mon Feb 4 11:46:59 CST 2026
# 注意: 已自动去除重复域名配置

# 推荐的上游安全DNS服务器
tls://dns.alidns.com
tls://dot.pub
tls://dns.google
tls://one.one.one.one

# === 国内域名配置 (使用DNS: 114.114.114.114 223.5.5.5) ===
# 来源: apple-cn.txt
[/icloud.com/]114.114.114.114 223.5.5.5
[/apple.com/]114.114.114.114 223.5.5.5
...

# === 国外域名配置 (使用DNS: 8.8.8.8 1.1.1.1) ===
# 来源: proxy-list.txt
[/google.com/]8.8.8.8 1.1.1.1
[/facebook.com/]8.8.8.8 1.1.1.1
...
```

## 参数说明

| 参数格式                      | 说明                        | 示例                                                    |
| ----------------------------- | --------------------------- | ------------------------------------------------------- |
| `[DNS...]`                    | 国内DNS服务器地址（可多个） | `./dnsmasq_to_adg.sh 114.114.114.114`                   |
| `--foreign`                   | 分隔符，标识国外DNS配置开始 | `./dnsmasq_to_adg.sh --foreign 8.8.8.8`                 |
| `[DNS...] --foreign [DNS...]` | 分别指定国内外DNS           | `./dnsmasq_to_adg.sh 114.114.114.114 --foreign 8.8.8.8` |
| `--output, -o`                | 指定输出根目录              | `./adguardhome_dns.py --output /my/configs`             |

## 默认配置

当未指定参数时，脚本使用以下默认配置：

- **国内DNS服务器**: `114.114.114.114`
- **国外DNS服务器**: `8.8.8.8`
- **输出根目录**: 当前工作目录

## 推荐的上游DNS服务器

脚本默认在合并文件头部添加以下安全DNS服务器：
- `tls://dns.alidns.com` - 阿里DNS (支持DoT/DoH)
- `tls://dot.pub` - 腾讯DNS (支持DoT)
- `tls://dns.google` - Google DNS (支持DoT/DoH)
- `tls://one.one.one.one` - Cloudflare DNS (支持DoT/DoH)

## 系统要求

### Python版本
- Python 3.6+
- 网络连接（需要访问GitHub API）

### Shell版本
- Linux/macOS 系统
- Bash shell 环境
- curl 命令行工具
- 网络连接（需要访问GitHub API）

## 注意事项

- 脚本会自动清理之前的下载文件，确保获取最新配置
- 国内域名使用指定的第一组DNS服务器解析
- 国外域名使用指定的第二组DNS服务器解析
- **新增**: 脚本会自动去除重复域名配置，避免冲突
- **新增**: 采用分层目录结构，便于文件组织和管理
- 建议定期运行以获取最新的域名列表更新
- 转换过程保留原有注释信息，便于追溯

## 故障排除

### GitHub API 速率限制
如果遇到 "rate limit exceeded" 错误：
1. 等待一段时间后再试
2. 使用个人访问令牌增加API限制
3. 考虑使用镜像源或本地缓存

### 网络连接问题
- 检查网络连接状态
- 确认能够访问GitHub
- 尝试使用代理或VPN

### 文件权限问题
- 确保有写入当前目录的权限
- 检查磁盘空间是否充足
- 确保输出目录具有写入权限

## 版本历史

### v3.3.0 (当前版本)
- ✨ **重要变更**: 实现分层目录结构
- ✨ 原始文件和转换文件保存在 `configs/` 子目录
- ✨ 最终合并文件保存在输出根目录
- ✨ 改进文件组织，使目录结构更加清晰

### v3.2.1
- ✨ 所有文件保存到统一的输出目录中

### v3.2.0
- ✨ 添加自定义输出目录功能 (`--output` 参数)

### v3.1.0
- ✨ 添加智能去重功能
- ✨ 在合并文件中显示去重统计信息
- ✨ 优化域名处理逻辑

### v3.0.0
- ✨ 添加Python版本脚本 (`adguardhome_dns.py`)
- ✨ 改进的错误处理和用户反馈
- ✨ 更好的跨平台兼容性
- ✨ 支持更详细的日志输出

### v2.0.0
- ✨ 切换数据源至 Loyalsoldier/v2ray-rules-dat
- ✨ 支持国内外域名分别配置DNS服务器
- ✨ 通过GitHub API自动获取最新release
- ✨ 改进的参数解析和错误处理

### v1.0.0
- 🎯 基于 dnsmasq-china-list 的初始版本
- 🔄 支持基本的格式转换功能

## 许可证

MIT License

## 相关项目

- [Loyalsoldier/v2ray-rules-dat](https://github.com/Loyalsoldier/v2ray-rules-dat) - 原始配置文件来源
- [AdGuard Home](https://github.com/AdguardTeam/AdGuardHome) - 广告拦截DNS服务器
- [dnsmasq-china-list](https://github.com/felixonmars/dnsmasq-china-list) - 旧版数据源（v1.0）
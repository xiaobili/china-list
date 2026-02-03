# China List Config Converter

将 [dnsmasq-china-list](https://github.com/felixonmars/dnsmasq-china-list) 配置文件自动转换为 AdGuard Home 兼容格式的自动化脚本工具。

## 功能特性

- 🔧 **自动化处理**: 一键下载、转换、合并配置文件
- 🌐 **多源支持**: 支持加速域名、Apple、Google 三类配置文件
- ⚙️ **灵活配置**: 可自定义DNS服务器地址
- 🔄 **智能重试**: 内置网络重试机制，提高下载成功率
- 📝 **格式转换**: 将 dnsmasq 格式自动转换为 AdGuard Home 兼容格式

## 工作原理

脚本会自动执行以下步骤：

1. 从 [dnsmasq-china-list](https://github.com/felixonmars/dnsmasq-china-list) 下载最新的配置文件
2. 将原始的 `server=/domain/ip` 格式转换为 AdGuard Home 的 `[/domain/]ip` 格式
3. 支持自定义DNS服务器地址配置
4. 合并所有配置文件并添加推荐的上游DNS服务器

## 使用方法

### 基本使用

```bash
# 使用默认DNS服务器 (114.114.114.114)
./dnsmasq_to_adg.sh

# 使用自定义DNS服务器
./dnsmasq_to_adg.sh 8.8.8.8

# 使用多个DNS服务器
./dnsmasq_to_adg.sh 8.8.8.8 114.114.114.114 223.5.5.5
```

### 输出文件

脚本执行后会在当前目录下生成以下文件：

- `china-list-config/`: 配置文件存储目录
  - `accelerated-domains.china.conf`: 原始加速域名配置
  - `apple.china.conf`: 原始Apple域名配置  
  - `google.china.conf`: 原始Google域名配置
  - `accelerated-domains.china.txt`: 转换后的加速域名配置
  - `apple.china.txt`: 转换后的Apple域名配置
  - `google.china.txt`: 转换后的Google域名配置
- `chinalist-for-adguard.txt`: 最终合并的AdGuard Home配置文件

## 配置示例

生成的 `chinalist-for-adguard.txt` 文件格式如下：

```
tls://dns.alidns.com
tls://dot.pub
tls://dns.google
tls://one.one.one.one
[/baidu.com/]8.8.8.8 114.114.114.114
[/qq.com/]8.8.8.8 114.114.114.114
...
```

## 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `$1, $2, ...` | 自定义DNS服务器地址 | `./dnsmasq_to_adg.sh 8.8.8.8 114.114.114.114` |

## 推荐的上游DNS服务器

脚本默认在合并文件头部添加以下安全DNS服务器：
- `tls://dns.alidns.com` - 阿里DNS
- `tls://dot.pub` - 腾讯DNS
- `tls://dns.google` - Google DNS
- `tls://one.one.one.one` - Cloudflare DNS

## 系统要求

- Linux/macOS 系统
- Bash shell 环境
- curl 命令行工具
- 网络连接

## 注意事项

- 脚本会自动清理之前的下载文件，确保获取最新配置
- 转换过程保留原有注释和格式
- 建议定期运行以获取最新的域名列表更新

## 许可证

MIT License

## 相关项目

- [dnsmasq-china-list](https://github.com/felixonmars/dnsmasq-china-list) - 原始配置文件来源
- [AdGuard Home](https://github.com/AdguardTeam/AdGuardHome) - 广告拦截DNS服务器
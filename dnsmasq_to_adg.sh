#!/bin/bash

# v2ray-rules-dat to AdGuardHome 配置转换脚本
# 自动下载 Loyalsoldier/v2ray-rules-dat 的最新配置文件并转换为 AdGuardHome 兼容格式

set -e  # 出错时退出

# 显示帮助信息
show_help() {
    echo "用法: $0 [国内DNS服务器...] [--foreign 国外DNS服务器...]"
    echo ""
    echo "参数说明:"
    echo "  国内DNS服务器    用于国内域名解析的DNS服务器地址（可指定多个）"
    echo "  --foreign        分隔符，后面跟国外DNS服务器地址"
    echo "  国外DNS服务器    用于国外域名解析的DNS服务器地址（可指定多个）"
    echo ""
    echo "示例:"
    echo "  $0 114.114.114.114                          # 只指定国内DNS（国外使用相同DNS）"
    echo "  $0 114.114.114.114 --foreign 8.8.8.8       # 分别指定国内外DNS"
    echo "  $0 114.114.114.114 223.5.5.5 --foreign 8.8.8.8 1.1.1.1"
    echo ""
    echo "默认值:"
    echo "  国内DNS: 114.114.114.114"
    echo "  国外DNS: 8.8.8.8"
    exit 1
}

# 检查是否有帮助参数
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    show_help
fi

# 解析参数
DOMESTIC_DNS=()
FOREIGN_DNS=()
CURRENT_MODE="domestic"  # domestic or foreign

# 默认DNS服务器
DEFAULT_DOMESTIC_DNS="114.114.114.114"
DEFAULT_FOREIGN_DNS="8.8.8.8"

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --foreign)
            CURRENT_MODE="foreign"
            shift
            ;;
        -*)
            echo "未知参数: $1"
            show_help
            ;;
        *)
            if [[ "$CURRENT_MODE" == "domestic" ]]; then
                DOMESTIC_DNS+=("$1")
            else
                FOREIGN_DNS+=("$1")
            fi
            shift
            ;;
    esac
done

# 设置默认值
if [ ${#DOMESTIC_DNS[@]} -eq 0 ]; then
    DOMESTIC_DNS=("$DEFAULT_DOMESTIC_DNS")
fi

if [ ${#FOREIGN_DNS[@]} -eq 0 ]; then
    FOREIGN_DNS=("$DEFAULT_FOREIGN_DNS")
fi

# 将数组转换为字符串
DOMESTIC_DNS_STR="${DOMESTIC_DNS[*]}"
FOREIGN_DNS_STR="${FOREIGN_DNS[*]}"

echo "配置信息:"
echo "  国内DNS服务器: $DOMESTIC_DNS_STR"
echo "  国外DNS服务器: $FOREIGN_DNS_STR"
echo ""

# 定义文件和URL
CONFIG_DIR="china-list-config"
GITHUB_API_URL="https://api.github.com/repos/Loyalsoldier/v2ray-rules-dat/releases/latest"

# 国内分组文件
DOMESTIC_FILES=(
    "apple-cn.txt"
    "google-cn.txt" 
    "china-list.txt"
)

# 国外分组文件
FOREIGN_FILES=(
    "proxy-list.txt"
    "gfw.txt"
    "greatfire.txt"
)

# 创建配置目录
if [ ! -d "$CONFIG_DIR" ]; then
    echo "创建目录: $CONFIG_DIR"
    mkdir "$CONFIG_DIR"
fi

cd "$CONFIG_DIR"

# 获取最新release的下载URL
echo "获取最新 release 信息..."
RELEASE_INFO=$(curl -s -f --retry 3 --retry-delay 2 --connect-timeout 10 "$GITHUB_API_URL")
if [ $? -ne 0 ]; then
    echo "错误: 无法获取 GitHub release 信息"
    exit 1
fi

# 提取下载URL的基础部分
BASE_URL=$(echo "$RELEASE_INFO" | grep -o '"browser_download_url": "[^"]*' | head -1 | sed 's/"browser_download_url": "//' | sed 's/[^/]*$//')

if [ -z "$BASE_URL" ]; then
    echo "错误: 无法提取下载URL"
    exit 1
fi

echo "下载基础URL: $BASE_URL"

# 下载函数，带重试机制
download_with_retry() {
    local filename=$1
    local url="${BASE_URL}${filename}"
    local max_attempts=3
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        echo "下载 $filename (尝试 $attempt/$max_attempts)..."
        if curl -s -f -L --retry 3 --retry-delay 2 --connect-timeout 10 "$url" -o "$filename"; then
            echo "成功下载 $filename"
            return 0
        else
            echo "下载失败，正在重试..."
            ((attempt++))
            sleep 2
        fi
    done
    
    echo "错误: 无法下载 $filename 在 $max_attempts 次尝试后"
    return 1
}

# 下载所有配置文件
echo "开始下载 v2ray-rules-dat 配置文件..."

# 总是重新下载文件，如果存在则先删除
ALL_FILES=("${DOMESTIC_FILES[@]}" "${FOREIGN_FILES[@]}")
for file in "${ALL_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "删除已存在的文件: $file"
        rm "$file"
    fi
done

# 下载国内文件
for file in "${DOMESTIC_FILES[@]}"; do
    download_with_retry "$file"
done

# 下载国外文件
for file in "${FOREIGN_FILES[@]}"; do
    download_with_retry "$file"
done

echo "下载完成！"

# 转换配置文件
echo "开始转换配置文件为 AdGuardHome 兼容格式..."

# 转换函数 - 将域名列表转换为AdGuardHome兼容格式
convert_domains_to_adguard() {
    local input_file="$1"
    local output_file="$2"
    local dns_servers="$3"
    
    {
        # 添加注释说明使用的DNS服务器
        echo "# 使用DNS服务器: $dns_servers"
        echo "# 来源文件: $input_file"
        
        # 处理每个域名行
        while IFS= read -r line || [[ -n "$line" ]]; do
            # 跳过空行和注释行
            if [[ -n "$line" && ! "$line" =~ ^[[:space:]]*# ]]; then
                # 去除首尾空白字符
                line=$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
                # 处理 full: 前缀
                if [[ "$line" =~ ^full:(.*) ]]; then
                    domain="${BASH_REMATCH[1]}"
                else
                    domain="$line"
                fi
                # 转换为AdGuardHome格式
                if [[ -n "$domain" ]]; then
                    echo "[/$domain/]$dns_servers"
                fi
            fi
        done < "$input_file"
    } > "$output_file"
}

# 转换国内文件
for file in "${DOMESTIC_FILES[@]}"; do
    output_file="${file%.txt}.adg.txt"
    echo "转换 $file -> $output_file (使用国内DNS: $DOMESTIC_DNS_STR)"
    convert_domains_to_adguard "$file" "$output_file" "$DOMESTIC_DNS_STR"
done

# 转换国外文件
for file in "${FOREIGN_FILES[@]}"; do
    output_file="${file%.txt}.adg.txt"
    echo "转换 $file -> $output_file (使用国外DNS: $FOREIGN_DNS_STR)"
    convert_domains_to_adguard "$file" "$output_file" "$FOREIGN_DNS_STR"
done

echo "转换完成！"

# 删除旧的合并文件（如果存在）
OUTPUT_FILENAME="../chinalist-for-adguard.txt"
if [ -f "$OUTPUT_FILENAME" ]; then
    echo "删除旧的合并文件: $OUTPUT_FILENAME"
    rm "$OUTPUT_FILENAME"
fi

# 创建合并后的文件
echo "创建合并后的配置文件到: $OUTPUT_FILENAME"

{
    echo "# AdGuard Home 中国域名列表配置"
    echo "# 生成时间: $(date)"
    echo ""
    echo "# 推荐的上游安全DNS服务器"
    echo "tls://dns.alidns.com"
    echo "tls://dot.pub"
    echo "tls://dns.google"
    echo "tls://one.one.one.one"
    echo ""
    
    echo "# === 国内域名配置 (使用DNS: $DOMESTIC_DNS_STR) ==="
    for file in "${DOMESTIC_FILES[@]}"; do
        output_file="${file%.txt}.adg.txt"
        if [ -f "$output_file" ]; then
            echo "# 来源: $file"
            cat "$output_file"
            echo ""
        fi
    done
    
    echo "# === 国外域名配置 (使用DNS: $FOREIGN_DNS_STR) ==="
    for file in "${FOREIGN_FILES[@]}"; do
        output_file="${file%.txt}.adg.txt"
        if [ -f "$output_file" ]; then
            echo "# 来源: $file"
            cat "$output_file"
            echo ""
        fi
    done
    
} > "$OUTPUT_FILENAME"

echo "所有操作已完成！"
echo ""
echo "输出文件列表："
for file in "${DOMESTIC_FILES[@]}" "${FOREIGN_FILES[@]}"; do
    echo "- $file (原始文件)"
    echo "- ${file%.txt}.adg.txt (转换后文件)"
done
echo "- $OUTPUT_FILENAME (合并后的最终文件)"
echo ""
echo "配置摘要："
echo "- 国内域名使用DNS: $DOMESTIC_DNS_STR"
echo "- 国外域名使用DNS: $FOREIGN_DNS_STR"
echo ""
echo "合并后文件的前15行预览："
head -15 "$OUTPUT_FILENAME"
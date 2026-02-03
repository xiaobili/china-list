#!/bin/bash

# dnsmasq-china-list to AdGuardHome 配置转换脚本
# 自动下载最新的 dnsmasq-china-list 配置文件并转换为 AdGuardHome 兼容格式

set -e  # 出错时退出

# 默认DNS服务器地址，如果未指定则使用此默认值
DEFAULT_DNS_SERVER="114.114.114.114"

# 检查是否提供了自定义DNS服务器地址参数
if [ $# -ge 1 ]; then
    # 将所有参数组合成DNS服务器列表
    DNS_SERVER_LIST=("$@")
    DNS_SERVERS=""
    for server in "${DNS_SERVER_LIST[@]}"; do
        if [ -z "$DNS_SERVERS" ]; then
            DNS_SERVERS="$server"
        else
            DNS_SERVERS="$DNS_SERVERS $server"
        fi
    done
    echo "使用提供的DNS服务器地址: $DNS_SERVERS"
else
    DNS_SERVERS="$DEFAULT_DNS_SERVER"
    echo "未提供DNS服务器地址，使用默认值: $DNS_SERVERS"
fi

# 定义文件和URL
CONFIG_DIR="china-list-config"
ACCELERATED_DOMAINS_URL="https://raw.githubusercontent.com/felixonmars/dnsmasq-china-list/master/accelerated-domains.china.conf"
APPLE_URL="https://raw.githubusercontent.com/felixonmars/dnsmasq-china-list/master/apple.china.conf"
GOOGLE_URL="https://raw.githubusercontent.com/felixonmars/dnsmasq-china-list/master/google.china.conf"

ACCELERATED_DOMAINS_CONF="accelerated-domains.china.conf"
APPLE_CONF="apple.china.conf"
GOOGLE_CONF="google.china.conf"

ACCELERATED_DOMAINS_TXT="accelerated-domains.china.txt"
APPLE_TXT="apple.china.txt"
GOOGLE_TXT="google.china.txt"

# 创建配置目录
if [ ! -d "$CONFIG_DIR" ]; then
    echo "创建目录: $CONFIG_DIR"
    mkdir "$CONFIG_DIR"
fi

cd "$CONFIG_DIR"

# 下载配置文件
echo "开始下载 dnsmasq-china-list 配置文件..."

# 总是重新下载文件，如果存在则先删除
for file in "$ACCELERATED_DOMAINS_CONF" "$APPLE_CONF" "$GOOGLE_CONF"; do
    if [ -f "$file" ]; then
        echo "删除已存在的文件: $file"
        rm "$file"
    fi
done

# 下载函数，带重试机制
download_with_retry() {
    local url=$1
    local output_file=$2
    local max_attempts=3
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        echo "下载 $output_file (尝试 $attempt/$max_attempts)..."
        if curl -s -f -L --retry 3 --retry-delay 2 --connect-timeout 10 "$url" -o "$output_file"; then
            echo "成功下载 $output_file"
            return 0
        else
            echo "下载失败，正在重试..."
            ((attempt++))
            sleep 2
        fi
    done
    
    echo "错误: 无法下载 $output_file 在 $max_attempts 次尝试后"
    return 1
}

download_with_retry "$ACCELERATED_DOMAINS_URL" "$ACCELERATED_DOMAINS_CONF"
download_with_retry "$APPLE_URL" "$APPLE_CONF"
download_with_retry "$GOOGLE_URL" "$GOOGLE_CONF"

echo "下载完成！"

# 转换配置文件
echo "开始转换配置文件为 AdGuardHome 兼容格式..."

# 转换函数 - 替换DNS服务器地址并将格式转换为AdGuardHome兼容格式
convert_file() {
    local input_file="$1"
    local output_file="$2"
    
    # 将每行的server=/domain/ip格式转换为[/domain/]多DNS服务器格式
    while IFS= read -r line; do
        if [[ $line =~ ^server=/([^/]+)/(.+)$ ]]; then
            DOMAIN="${BASH_REMATCH[1]}"
            echo "[/$DOMAIN/]$DNS_SERVERS"
        else
            # 如果不是server行，直接输出原内容（如注释行）
            echo "$line"
        fi
    done < "$input_file" > "$output_file"
}

# 转换 accelerated-domains.china.conf
echo "转换 $ACCELERATED_DOMAINS_CONF -> $ACCELERATED_DOMAINS_TXT"
convert_file "$ACCELERATED_DOMAINS_CONF" "$ACCELERATED_DOMAINS_TXT"

# 转换 apple.china.conf
echo "转换 $APPLE_CONF -> $APPLE_TXT"
convert_file "$APPLE_CONF" "$APPLE_TXT"

# 转换 google.china.conf
echo "转换 $GOOGLE_CONF -> $GOOGLE_TXT"
convert_file "$GOOGLE_CONF" "$GOOGLE_TXT"

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
    echo "tls://dns.alidns.com"
    echo "tls://dot.pub" 
    echo "tls://dns.google"
    echo "tls://one.one.one.one"
    cat "$ACCELERATED_DOMAINS_TXT" "$APPLE_TXT" "$GOOGLE_TXT"
} > "$OUTPUT_FILENAME"

echo "所有操作已完成！"
echo ""
echo "输出文件列表："
echo "- $ACCELERATED_DOMAINS_TXT"
echo "- $APPLE_TXT"
echo "- $GOOGLE_TXT"
echo "- $OUTPUT_FILENAME (合并后的文件，使用DNS: $DNS_SERVERS)"
echo ""
echo "合并后文件的前10行预览："
head -10 "$OUTPUT_FILENAME"
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AdGuard Home DNS 配置转换器
将 Loyalsoldier/v2ray-rules-dat 配置文件自动转换为 AdGuard Home 兼容格式

功能特性:
- 自动下载最新配置文件
- 支持国内外域名分别配置DNS服务器
- 智能格式转换
- 自动生成合并配置文件
"""

import argparse
import os
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime
import time


class AdGuardConfigConverter:
    """AdGuard Home 配置转换器主类"""
    
    def __init__(self):
        self.config_dir = Path("china-list-config")
        self.github_api_url = "https://api.github.com/repos/Loyalsoldier/v2ray-rules-dat/releases/latest"
        self.output_filename = "chinalist-for-adguard.txt"
        
        # 国内分组文件
        self.domestic_files = [
            "apple-cn.txt",
            "google-cn.txt", 
            "china-list.txt"
        ]
        
        # 国外分组文件
        self.foreign_files = [
            "proxy-list.txt",
            "gfw.txt",
            "greatfire.txt"
        ]
        
        # 默认DNS服务器
        self.default_domestic_dns = ["114.114.114.114"]
        self.default_foreign_dns = ["8.8.8.8"]
        
    def show_usage(self):
        """显示使用方法"""
        usage_text = """
用法: python3 adguardhome_dns.py [国内DNS服务器...] [--foreign 国外DNS服务器...]

参数说明:
  国内DNS服务器    用于国内域名解析的DNS服务器地址（可指定多个）
  --foreign        分隔符，后面跟国外DNS服务器地址
  国外DNS服务器    用于国外域名解析的DNS服务器地址（可指定多个）

示例:
  python3 adguardhome_dns.py 114.114.114.114                          # 只指定国内DNS（国外使用相同DNS）
  python3 adguardhome_dns.py 114.114.114.114 --foreign 8.8.8.8       # 分别指定国内外DNS
  python3 adguardhome_dns.py 114.114.114.114 223.5.5.5 --foreign 8.8.8.8 1.1.1.1

默认值:
  国内DNS: 114.114.114.114
  国外DNS: 8.8.8.8
        """
        print(usage_text)
        
    def parse_arguments(self):
        """解析命令行参数"""
        parser = argparse.ArgumentParser(
            description="AdGuard Home DNS 配置转换器",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
示例用法:
  python3 adguardhome_dns.py 114.114.114.114
  python3 adguardhome_dns.py 114.114.114.114 --foreign 8.8.8.8
  python3 adguardhome_dns.py 114.114.114.114 223.5.5.5 --foreign 8.8.8.8 1.1.1.1
            """,
            add_help=False  # 禁用默认的帮助选项
        )
        
        parser.add_argument(
            'domestic_dns',
            nargs='*',
            help='国内DNS服务器地址'
        )
        
        parser.add_argument(
            '--foreign',
            nargs='*',
            dest='foreign_dns',
            help='国外DNS服务器地址'
        )
        
        parser.add_argument(
            '--help', '-h',
            action='store_true',
            help='显示帮助信息'
        )
        
        args = parser.parse_args()
        
        if args.help:
            self.show_usage()
            parser.print_help()
            sys.exit(0)
            
        # 设置DNS服务器
        self.domestic_dns = args.domestic_dns if args.domestic_dns else self.default_domestic_dns
        self.foreign_dns = args.foreign_dns if args.foreign_dns else self.default_foreign_dns
        
        print("配置信息:")
        print(f"  国内DNS服务器: {' '.join(self.domestic_dns)}")
        print(f"  国外DNS服务器: {' '.join(self.foreign_dns)}")
        print()
        
    def create_config_directory(self):
        """创建配置目录"""
        if not self.config_dir.exists():
            print(f"创建目录: {self.config_dir}")
            self.config_dir.mkdir(parents=True)
            
    def get_latest_release_info(self):
        """获取最新release信息"""
        print("获取最新 release 信息...")
        try:
            req = urllib.request.Request(
                self.github_api_url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (compatible; AdGuardConfigConverter/1.0)'
                }
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                
            # 提取下载URL的基础部分
            assets = data.get('assets', [])
            if not assets:
                raise Exception("未找到下载资源")
                
            # 找到第一个浏览器下载URL作为基准
            browser_url = None
            for asset in assets:
                if 'browser_download_url' in asset:
                    browser_url = asset['browser_download_url']
                    break
                    
            if not browser_url:
                raise Exception("未找到有效的下载URL")
                
            base_url = '/'.join(browser_url.split('/')[:-1]) + '/'
            print(f"下载基础URL: {base_url}")
            
            return base_url
            
        except urllib.error.URLError as e:
            print(f"错误: 无法获取 GitHub release 信息 - {e}")
            sys.exit(1)
        except Exception as e:
            print(f"错误: {e}")
            sys.exit(1)
            
    def download_file_with_retry(self, base_url, filename, max_attempts=3):
        """带重试机制的文件下载"""
        url = f"{base_url}{filename}"
        
        for attempt in range(1, max_attempts + 1):
            try:
                print(f"下载 {filename} (尝试 {attempt}/{max_attempts})...")
                
                req = urllib.request.Request(
                    url,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (compatible; AdGuardConfigConverter/1.0)'
                    }
                )
                
                filepath = self.config_dir / filename
                
                # 如果文件存在则删除
                if filepath.exists():
                    print(f"删除已存在的文件: {filename}")
                    filepath.unlink()
                    
                with urllib.request.urlopen(req, timeout=10) as response:
                    with open(filepath, 'wb') as f:
                        f.write(response.read())
                        
                print(f"成功下载 {filename}")
                return True
                
            except Exception as e:
                print(f"下载失败: {e}")
                if attempt < max_attempts:
                    print("正在重试...")
                    time.sleep(2)
                else:
                    print(f"错误: 无法下载 {filename} 在 {max_attempts} 次尝试后")
                    return False
                    
    def download_all_files(self, base_url):
        """下载所有配置文件"""
        print("开始下载 v2ray-rules-dat 配置文件...")
        
        all_files = self.domestic_files + self.foreign_files
        success_count = 0
        
        for filename in all_files:
            if self.download_file_with_retry(base_url, filename):
                success_count += 1
                
        if success_count == len(all_files):
            print("下载完成！")
            return True
        else:
            print(f"警告: 只成功下载了 {success_count}/{len(all_files)} 个文件")
            return False
            
    def convert_domain_to_adguard_format(self, domain, dns_servers):
        """将单个域名转换为AdGuardHome格式"""
        # 处理 full: 前缀
        if domain.startswith('full:'):
            domain = domain[5:]  # 移除 'full:' 前缀
            
        # 去除首尾空白字符
        domain = domain.strip()
        
        # 转换为AdGuardHome格式
        if domain:
            dns_str = ' '.join(dns_servers)
            return f"[/{domain}/]{dns_str}"
        return None
        
    def convert_file_to_adguard(self, input_filename, output_filename, dns_servers):
        """将整个文件转换为AdGuardHome格式"""
        input_path = self.config_dir / input_filename
        output_path = self.config_dir / output_filename
        
        try:
            with open(input_path, 'r', encoding='utf-8') as infile, \
                 open(output_path, 'w', encoding='utf-8') as outfile:
                
                # 添加注释说明
                outfile.write(f"# 使用DNS服务器: {' '.join(dns_servers)}\n")
                outfile.write(f"# 来源文件: {input_filename}\n\n")
                
                # 处理每一行
                for line_num, line in enumerate(infile, 1):
                    line = line.strip()
                    
                    # 跳过空行和注释行
                    if not line or line.startswith('#'):
                        continue
                        
                    # 转换域名格式
                    adguard_line = self.convert_domain_to_adguard_format(line, dns_servers)
                    if adguard_line:
                        outfile.write(adguard_line + '\n')
                        
        except FileNotFoundError:
            print(f"警告: 文件不存在 {input_filename}")
        except Exception as e:
            print(f"错误: 转换文件 {input_filename} 时出错 - {e}")
            
    def convert_all_files(self):
        """转换所有配置文件"""
        print("开始转换配置文件为 AdGuardHome 兼容格式...")
        
        # 转换国内文件
        for filename in self.domestic_files:
            output_filename = filename.replace('.txt', '.adg.txt')
            print(f"转换 {filename} -> {output_filename} (使用国内DNS: {' '.join(self.domestic_dns)})")
            self.convert_file_to_adguard(filename, output_filename, self.domestic_dns)
            
        # 转换国外文件
        for filename in self.foreign_files:
            output_filename = filename.replace('.txt', '.adg.txt')
            print(f"转换 {filename} -> {output_filename} (使用国外DNS: {' '.join(self.foreign_dns)})")
            self.convert_file_to_adguard(filename, output_filename, self.foreign_dns)
            
        print("转换完成！")
        
    def create_merged_config(self):
        """创建合并后的配置文件"""
        print(f"创建合并后的配置文件到: {self.output_filename}")
        
        # 删除旧文件
        output_path = Path(self.output_filename)
        if output_path.exists():
            print(f"删除旧的合并文件: {self.output_filename}")
            output_path.unlink()
            
        try:
            # 用于去重的集合
            processed_domains = set()
            
            with open(output_path, 'w', encoding='utf-8') as outfile:
                # 写入文件头
                outfile.write("# AdGuard Home 中国域名列表配置\n")
                outfile.write(f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                outfile.write(f"# 注意: 已自动去除重复域名配置\n\n")
                
                # 推荐的上游安全DNS服务器
                outfile.write("# 推荐的上游安全DNS服务器\n")
                outfile.write("tls://dns.alidns.com\n")
                outfile.write("tls://dot.pub\n")
                outfile.write("tls://dns.google\n")
                outfile.write("tls://one.one.one.one\n\n")
                
                # 国内域名配置
                outfile.write(f"# === 国内域名配置 (使用DNS: {' '.join(self.domestic_dns)}) ===\n")
                domestic_count = 0
                for filename in self.domestic_files:
                    adg_filename = filename.replace('.txt', '.adg.txt')
                    adg_path = self.config_dir / adg_filename
                    
                    if adg_path.exists():
                        outfile.write(f"# 来源: {filename}\n")
                        with open(adg_path, 'r', encoding='utf-8') as infile:
                            for line in infile:
                                if line.strip() and not line.startswith('#'):
                                    # 提取域名部分进行去重
                                    if '[' in line and ']' in line:
                                        domain_part = line[line.find('['):line.find(']')+1]
                                        if domain_part not in processed_domains:
                                            processed_domains.add(domain_part)
                                            outfile.write(line)
                                            domestic_count += 1
                        outfile.write("\n")
                
                # 国外域名配置
                outfile.write(f"# === 国外域名配置 (使用DNS: {' '.join(self.foreign_dns)}) ===\n")
                foreign_count = 0
                for filename in self.foreign_files:
                    adg_filename = filename.replace('.txt', '.adg.txt')
                    adg_path = self.config_dir / adg_filename
                    
                    if adg_path.exists():
                        outfile.write(f"# 来源: {filename}\n")
                        with open(adg_path, 'r', encoding='utf-8') as infile:
                            for line in infile:
                                if line.strip() and not line.startswith('#'):
                                    # 提取域名部分进行去重
                                    if '[' in line and ']' in line:
                                        domain_part = line[line.find('['):line.find(']')+1]
                                        if domain_part not in processed_domains:
                                            processed_domains.add(domain_part)
                                            outfile.write(line)
                                            foreign_count += 1
                        outfile.write("\n")
                        
            print("合并文件创建完成！")
            print(f"去重统计: 国内域名 {domestic_count} 个, 国外域名 {foreign_count} 个, 总计 {len(processed_domains)} 个唯一域名")
            
        except Exception as e:
            print(f"错误: 创建合并文件时出错 - {e}")
            sys.exit(1)
            
    def show_summary(self):
        """显示执行摘要"""
        print("\n所有操作已完成！")
        print("\n输出文件列表：")
        
        for filename in self.domestic_files + self.foreign_files:
            print(f"- {filename} (原始文件)")
            print(f"- {filename.replace('.txt', '.adg.txt')} (转换后文件)")
        print(f"- {self.output_filename} (合并后的最终文件)")
        
        print("\n配置摘要：")
        print(f"- 国内域名使用DNS: {' '.join(self.domestic_dns)}")
        print(f"- 国外域名使用DNS: {' '.join(self.foreign_dns)}")
        
        # 显示合并文件预览
        try:
            output_path = Path(self.output_filename)
            if output_path.exists():
                print(f"\n合并后文件的前15行预览：")
                with open(output_path, 'r', encoding='utf-8') as f:
                    for i, line in enumerate(f):
                        if i >= 15:
                            break
                        print(line.rstrip())
        except Exception as e:
            print(f"无法读取预览文件: {e}")

    def run(self):
        """执行主要流程"""
        try:
            # 解析参数
            self.parse_arguments()
            
            # 创建配置目录
            self.create_config_directory()
            
            # 进入配置目录
            os.chdir(self.config_dir)
            
            # 获取最新release信息
            base_url = self.get_latest_release_info()
            
            # 下载所有文件
            if not self.download_all_files(base_url):
                print("警告: 部分文件下载失败，但仍继续处理已下载的文件")
            
            # 转换所有文件
            self.convert_all_files()
            
            # 返回上级目录
            os.chdir('..')
            
            # 创建合并配置文件
            self.create_merged_config()
            
            # 显示摘要
            self.show_summary()
            
        except KeyboardInterrupt:
            print("\n用户中断操作")
            sys.exit(1)
        except Exception as e:
            print(f"发生未预期的错误: {e}")
            sys.exit(1)


def main():
    """主函数"""
    converter = AdGuardConfigConverter()
    converter.run()


if __name__ == "__main__":
    main()
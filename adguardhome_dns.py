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
- 支持分层目录结构（configs子目录存放原始和转换文件，根目录存放合并文件）
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

# 常量定义
CONFIGS_SUBDIR = "configs"
OUTPUT_FILENAME = "chinalist-for-adguard.txt"
GITHUB_API_URL = "https://api.github.com/repos/Loyalsoldier/v2ray-rules-dat/releases/latest"
JSDELIVR_BASE_URL = "https://cdn.jsdelivr.net/gh/Loyalsoldier/v2ray-rules-dat@release/"

# 文件分组
DOMESTIC_FILES: list[str] = [
    "apple-cn.txt",
    "google-cn.txt",
    "china-list.txt",
]
FOREIGN_FILES: list[str] = [
    "proxy-list.txt",
    "gfw.txt",
    "greatfire.txt",
]

# 默认DNS服务器
DEFAULT_DOMESTIC_DNS: list[str] = ["114.114.114.114"]
DEFAULT_FOREIGN_DNS: list[str] = ["8.8.8.8"]

# 文件扩展名
EXT_SOURCE = ".txt"
EXT_CONVERTED = ".adg.txt"

# CDN 配置
MAX_DOWNLOAD_ATTEMPTS = 3
DOWNLOAD_TIMEOUT = 10
RETRY_DELAY = 2


@dataclass
class DNSConfig:
    """DNS配置数据类"""
    domestic: list[str] = field(default_factory=lambda: DEFAULT_DOMESTIC_DNS.copy())
    foreign: list[str] = field(default_factory=lambda: DEFAULT_FOREIGN_DNS.copy())


@dataclass
class FileStats:
    """文件处理统计"""
    domestic_count: int = 0
    foreign_count: int = 0
    unique_domains: set[str] = field(default_factory=set)

    @property
    def total_unique(self) -> int:
        return len(self.unique_domains)


class AdGuardConfigConverter:
    """AdGuard Home 配置转换器主类"""

    def __init__(self) -> None:
        self.output_dir: Path = Path(".")
        self.dns_config = DNSConfig()

    def show_usage(self) -> None:
        """显示使用方法"""
        usage_text = """
用法: python3 adguardhome_dns.py [国内DNS服务器...] [--foreign 国外DNS服务器...] [--output 输出目录]

参数说明:
  国内DNS服务器    用于国内域名解析的DNS服务器地址（可指定多个）
  --foreign        分隔符，后面跟国外DNS服务器地址
  国外DNS服务器    用于国外域名解析的DNS服务器地址（可指定多个）
  --output         指定输出根目录（默认为当前目录）
                  原始文件和转换文件保存在 {output_dir}/configs/ 目录中
                  合并文件保存在 {output_dir}/ 目录中

示例:
  python3 adguardhome_dns.py 114.114.114.114                          # 只指定国内DNS（国外使用相同DNS）
  python3 adguardhome_dns.py 114.114.114.114 --foreign 8.8.8.8       # 分别指定国内外DNS
  python3 adguardhome_dns.py 114.114.114.114 223.5.5.5 --foreign 8.8.8.8 1.1.1.1
  python3 adguardhome_dns.py --output /path/to/output/dir            # 指定输出目录
  python3 adguardhome_dns.py 114.114.114.114 --output ./configs      # 同时指定DNS和输出目录

默认值:
  国内DNS: 114.114.114.114
  国外DNS: 8.8.8.8
  输出根目录: 当前工作目录
        """
        print(usage_text)

    def parse_arguments(self) -> None:
        """解析命令行参数"""
        parser = argparse.ArgumentParser(
            description="AdGuard Home DNS 配置转换器",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
示例用法:
  python3 adguardhome_dns.py 114.114.114.114
  python3 adguardhome_dns.py 114.114.114.114 --foreign 8.8.8.8
  python3 adguardhome_dns.py 114.114.114.114 223.5.5.5 --foreign 8.8.8.8 1.1.1.1
  python3 adguardhome_dns.py --output /custom/output/path
  python3 adguardhome_dns.py 114.114.114.114 --output ./my-configs
            """,
            add_help=False,
        )

        parser.add_argument(
            "domestic_dns",
            nargs="*",
            help="国内DNS服务器地址",
        )
        parser.add_argument(
            "--foreign",
            nargs="*",
            dest="foreign_dns",
            help="国外DNS服务器地址",
        )
        parser.add_argument(
            "--output",
            "-o",
            dest="output_dir",
            default=".",
            help="输出根目录（默认为当前目录）",
        )
        parser.add_argument(
            "--help",
            "-h",
            action="store_true",
            help="显示帮助信息",
        )

        args = parser.parse_args()

        if args.help:
            self.show_usage()
            parser.print_help()
            sys.exit(0)

        # 设置DNS服务器
        if args.domestic_dns:
            self.dns_config.domestic = args.domestic_dns
        if args.foreign_dns:
            self.dns_config.foreign = args.foreign_dns

        # 设置输出根目录
        self.output_dir = Path(args.output_dir).resolve()

        self._print_config()

    def _print_config(self) -> None:
        """打印当前配置信息"""
        print("配置信息:")
        print(f"  国内DNS服务器: {' '.join(self.dns_config.domestic)}")
        print(f"  国外DNS服务器: {' '.join(self.dns_config.foreign)}")
        print(f"  输出根目录: {self.output_dir}")
        print(f"  configs子目录: {self.output_dir / CONFIGS_SUBDIR}")
        print()

    def create_directories(self) -> None:
        """创建必要的目录结构"""
        self._ensure_directory(self.output_dir, "输出根目录")
        self._ensure_directory(self.configs_dir, "configs子目录")

    def _ensure_directory(self, path: Path, description: str) -> None:
        """确保目录存在，不存在则创建"""
        if not path.exists():
            print(f"创建{description}: {path}")
            path.mkdir(parents=True)

    @property
    def configs_dir(self) -> Path:
        """获取configs子目录路径"""
        return self.output_dir / CONFIGS_SUBDIR

    def get_token(self) -> str | None:
        """从token文件获取GitHub API令牌"""
        token_file = self.output_dir / "token"
        try:
            return token_file.read_text().strip()
        except FileNotFoundError:
            print("警告: 未找到 token 文件，使用默认令牌可能会受限")
            return None

    def get_latest_release_info(self) -> str | None:
        """获取最新release信息，失败时返回None表示使用备用CDN"""
        print("获取最新 release 信息...")
        token = self.get_token()
        try:
            req = urllib.request.Request(
                GITHUB_API_URL,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; AdGuardConfigConverter/1.0)",
                    "Authorization": f"Bearer {token}" if token else "Bearer GITHUB_TOKEN",
                },
            )

            with urllib.request.urlopen(req, timeout=DOWNLOAD_TIMEOUT) as response:
                data = json.loads(response.read().decode())

            base_url = self._extract_base_url(data)
            if base_url:
                print(f"下载基础URL: {base_url}")
                return base_url
            raise ValueError("未找到有效的下载URL")

        except (urllib.error.URLError, ValueError) as e:
            print(f"警告: 无法获取 GitHub release 信息 - {e}")
            print("将使用 jsdelivr CDN 作为备用下载源")
            return None

    def _extract_base_url(self, release_data: dict) -> str | None:
        """从release数据中提取基础下载URL"""
        assets = release_data.get("assets", [])
        for asset in assets:
            if "browser_download_url" in asset:
                url = asset["browser_download_url"]
                return "/".join(url.split("/")[:-1]) + "/"
        return None

    def download_file_with_retry(
        self, base_url: str | None, filename: str, max_attempts: int = MAX_DOWNLOAD_ATTEMPTS
    ) -> bool:
        """带重试机制的文件下载，支持主备CDN切换"""
        cdn_urls = self._build_cdn_urls(base_url, filename)
        token = self.get_token()

        for cdn_name, url in cdn_urls:
            for attempt in range(1, max_attempts + 1):
                if self._try_download(url, filename, cdn_name, attempt, max_attempts, token):
                    return True

        print(f"错误: 无法下载 {filename}，所有CDN均已尝试")
        return False

    def _build_cdn_urls(self, base_url: str | None, filename: str) -> list[tuple[str, str]]:
        """构建CDN URL列表"""
        cdn_urls: list[tuple[str, str]] = []
        if base_url is not None:
            cdn_urls.append(("GitHub", f"{base_url}{filename}"))
        cdn_urls.append(("jsdelivr CDN", f"{JSDELIVR_BASE_URL}{filename}"))
        return cdn_urls

    def _try_download(
        self,
        url: str,
        filename: str,
        cdn_name: str,
        attempt: int,
        max_attempts: int,
        token: str | None,
    ) -> bool:
        """尝试单次下载"""
        try:
            print(f"下载 {filename} 从 {cdn_name} (尝试 {attempt}/{max_attempts})...")

            headers = {"User-Agent": "Mozilla/5.0 (compatible; AdGuardConfigConverter/1.0)"}
            if cdn_name == "GitHub" and token:
                headers["Authorization"] = f"Bearer {token}"

            req = urllib.request.Request(url, headers=headers)
            filepath = self.configs_dir / filename

            # 如果文件存在则删除
            if filepath.exists():
                print(f"删除已存在的文件: {filename}")
                filepath.unlink()

            with urllib.request.urlopen(req, timeout=DOWNLOAD_TIMEOUT) as response:
                filepath.write_bytes(response.read())

            print(f"成功下载 {filename} 从 {cdn_name}")
            return True

        except Exception as e:
            print(f"从 {cdn_name} 下载失败: {e}")
            if attempt < max_attempts:
                print("正在重试...")
                time.sleep(RETRY_DELAY)
            return False

    def download_all_files(self, base_url: str | None) -> bool:
        """下载所有配置文件到configs子目录"""
        print("开始下载 v2ray-rules-dat 配置文件...")

        all_files = DOMESTIC_FILES + FOREIGN_FILES
        success_count = sum(
            1 for filename in all_files if self.download_file_with_retry(base_url, filename)
        )

        if success_count == len(all_files):
            print("下载完成！")
            return True

        print(f"警告: 只成功下载了 {success_count}/{len(all_files)} 个文件")
        return False

    @staticmethod
    def convert_domain_to_adguard_format(domain: str, dns_servers: Sequence[str]) -> str | None:
        """将单个域名转换为AdGuardHome格式"""
        # 处理 full: 前缀
        if domain.startswith("full:"):
            domain = domain[5:]

        # 去除首尾空白字符
        domain = domain.strip()

        # 转换为AdGuardHome格式
        if domain:
            dns_str = " ".join(dns_servers)
            return f"[/{domain}/]{dns_str}"
        return None

    def convert_file_to_adguard(
        self, input_filename: str, output_filename: str, dns_servers: Sequence[str]
    ) -> None:
        """将整个文件转换为AdGuardHome格式"""
        input_path = self.configs_dir / input_filename
        output_path = self.configs_dir / output_filename

        try:
            with (
                open(input_path, "r", encoding="utf-8") as infile,
                open(output_path, "w", encoding="utf-8") as outfile,
            ):
                # 添加注释说明
                outfile.write(f"# 使用DNS服务器: {' '.join(dns_servers)}\n")
                outfile.write(f"# 来源文件: {input_filename}\n\n")

                # 处理每一行
                for line in infile:
                    line = line.strip()

                    # 跳过空行和注释行
                    if not line or line.startswith("#") or line.startswith("regexp:"):
                        continue

                    # 转换域名格式
                    adguard_line = self.convert_domain_to_adguard_format(line, dns_servers)
                    if adguard_line:
                        outfile.write(adguard_line + "\n")

        except FileNotFoundError:
            print(f"警告: 文件不存在 {input_filename}")
        except Exception as e:
            print(f"错误: 转换文件 {input_filename} 时出错 - {e}")

    def convert_all_files(self) -> None:
        """转换所有配置文件"""
        print("开始转换配置文件为 AdGuardHome 兼容格式...")

        # 转换国内文件
        for filename in DOMESTIC_FILES:
            output_filename = filename.replace(EXT_SOURCE, EXT_CONVERTED)
            print(f"转换 {filename} -> {output_filename} (使用国内DNS: {' '.join(self.dns_config.domestic)})")
            self.convert_file_to_adguard(filename, output_filename, self.dns_config.domestic)

        # 转换国外文件
        for filename in FOREIGN_FILES:
            output_filename = filename.replace(EXT_SOURCE, EXT_CONVERTED)
            print(f"转换 {filename} -> {output_filename} (使用国外DNS: {' '.join(self.dns_config.foreign)})")
            self.convert_file_to_adguard(filename, output_filename, self.dns_config.foreign)

        print("转换完成！")

    def _write_file_header(self, outfile) -> None:
        """写入合并文件头部信息"""
        outfile.write("# AdGuard Home 中国域名列表配置\n")
        outfile.write(f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        outfile.write("# 注意: 已自动去除重复域名配置\n\n")

        # 推荐的上游安全DNS服务器
        outfile.write("# 推荐的上游安全DNS服务器\n")
        outfile.write("tcp://223.5.5.5\n")
        outfile.write("tcp://119.29.29.29\n")
        outfile.write("tcp://1.1.1.1\n")
        outfile.write("tcp://8.8.8.8\n")
        outfile.write("tls://dns.alidns.com\n")
        outfile.write("tls://dot.pub\n")
        outfile.write("tls://dns.google\n")
        outfile.write("tls://one.one.one.one\n\n")

    def _process_domain_section(
        self,
        outfile,
        files: list[str],
        dns_servers: list[str],
        section_name: str,
        stats: FileStats,
        is_domestic: bool,
    ) -> None:
        """处理并写入域名配置区块"""
        outfile.write(f"# === {section_name} (使用DNS: {' '.join(dns_servers)}) ===\n")

        for filename in files:
            adg_filename = filename.replace(EXT_SOURCE, EXT_CONVERTED)
            adg_path = self.configs_dir / adg_filename

            if not adg_path.exists():
                continue

            outfile.write(f"# 来源: {filename}\n")
            with open(adg_path, "r", encoding="utf-8") as infile:
                for line in infile:
                    if not line.strip() or line.startswith("#"):
                        continue

                    domain_part = self._extract_domain_part(line)
                    if domain_part and domain_part not in stats.unique_domains:
                        stats.unique_domains.add(domain_part)
                        outfile.write(line)
                        if is_domestic:
                            stats.domestic_count += 1
                        else:
                            stats.foreign_count += 1
            outfile.write("\n")

    @staticmethod
    def _extract_domain_part(line: str) -> str | None:
        """从配置行中提取域名部分用于去重"""
        if "[" in line and "]" in line:
            return line[line.find("[") : line.find("]") + 1]
        return None

    def create_merged_config(self) -> None:
        """创建合并后的配置文件到输出根目录"""
        output_path = self.output_dir / OUTPUT_FILENAME
        print(f"创建合并后的配置文件到: {output_path}")

        # 删除旧文件
        if output_path.exists():
            print(f"删除旧的合并文件: {OUTPUT_FILENAME}")
            output_path.unlink()

        try:
            stats = FileStats()

            with open(output_path, "w", encoding="utf-8") as outfile:
                self._write_file_header(outfile)
                self._process_domain_section(
                    outfile, DOMESTIC_FILES, self.dns_config.domestic, "国内域名配置", stats, True
                )
                self._process_domain_section(
                    outfile, FOREIGN_FILES, self.dns_config.foreign, "国外域名配置", stats, False
                )

            print("合并文件创建完成！")
            print(f"去重统计: 国内域名 {stats.domestic_count} 个, "
                  f"国外域名 {stats.foreign_count} 个, 总计 {stats.total_unique} 个唯一域名")

        except Exception as e:
            print(f"错误: 创建合并文件时出错 - {e}")
            sys.exit(1)

    def _list_files_with_status(self, files: list[str], subdir: Path) -> None:
        """列出文件及其存在状态"""
        for filename in files:
            file_path = subdir / filename
            status = "✓" if file_path.exists() else "✗"
            print(f"- {filename} {status}")

    def show_summary(self) -> None:
        """显示执行摘要"""
        print("\n所有操作已完成！")
        print("\n目录结构:")
        print(f"输出根目录: {self.output_dir}")
        print(f"configs子目录: {self.configs_dir}")

        print("\nconfigs子目录中的文件:")
        # 显示原始文件
        self._list_files_with_status(DOMESTIC_FILES + FOREIGN_FILES, self.configs_dir)
        # 显示转换后文件
        converted_files = [
            f.replace(EXT_SOURCE, EXT_CONVERTED) for f in DOMESTIC_FILES + FOREIGN_FILES
        ]
        self._list_files_with_status(converted_files, self.configs_dir)

        print(f"\n输出根目录中的文件:")
        merged_path = self.output_dir / OUTPUT_FILENAME
        status = "✓" if merged_path.exists() else "✗"
        print(f"- {OUTPUT_FILENAME} {status}")

        print("\n配置摘要：")
        print(f"- 国内域名使用DNS: {' '.join(self.dns_config.domestic)}")
        print(f"- 国外域名使用DNS: {' '.join(self.dns_config.foreign)}")

        # 显示合并文件预览
        self._show_file_preview(merged_path)

    def _show_file_preview(self, file_path: Path, max_lines: int = 15) -> None:
        """显示文件预览"""
        try:
            if not file_path.exists():
                return
            print(f"\n合并后文件的前{max_lines}行预览：")
            with open(file_path, "r", encoding="utf-8") as f:
                for i, line in enumerate(f):
                    if i >= max_lines:
                        break
                    print(line.rstrip())
        except Exception as e:
            print(f"无法读取预览文件: {e}")

    def run(self) -> None:
        """执行主要流程"""
        try:
            self.parse_arguments()
            self.create_directories()

            output_dir_abs = self.output_dir.absolute()
            configs_dir_abs = self.configs_dir.absolute()
            print(f"输出根目录路径: {output_dir_abs}")
            print(f"configs子目录路径: {configs_dir_abs}")

            base_url = self.get_latest_release_info()

            if not self.download_all_files(base_url):
                print("警告: 部分文件下载失败，但仍继续处理已下载的文件")

            self.convert_all_files()
            self.create_merged_config()
            self.show_summary()

        except KeyboardInterrupt:
            print("\n用户中断操作")
            sys.exit(1)
        except Exception as e:
            print(f"发生未预期的错误: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


def main() -> None:
    """主函数"""
    converter = AdGuardConfigConverter()
    converter.run()


if __name__ == "__main__":
    main()

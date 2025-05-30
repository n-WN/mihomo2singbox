#!/usr/bin/env python3
"""
Mihomo (ClashMeta) 到 Sing-box 配置转换工具
"""

import json
import yaml
import argparse
import sys
from typing import Dict, List, Any  # , Optional
from pathlib import Path




class MihomoToSingboxConverter:
    """Mihomo 配置转换为 Sing-box 配置的转换器"""

    def __init__(
        self,
        listen_addr="127.0.0.1",
        listen_port=7890,
        enable_tun=False,
        log_level="info",
        clash_api_port=9090,
        disable_rule_sets=False,
        enable_tun_advanced=True,
    ):
        self.listen_addr = listen_addr
        self.listen_port = listen_port
        self.enable_tun = enable_tun
        self.log_level = log_level
        self.clash_api_port = clash_api_port
        self.disable_rule_sets = disable_rule_sets
        self.enable_tun_advanced = enable_tun_advanced
        self.singbox_config = {
            "log": {"level": self.log_level, "timestamp": True},
            "dns": {},
            "inbounds": [],
            "outbounds": [],
            "route": {"rules": [], "auto_detect_interface": True},
            "experimental": {},
        }

        # 协议映射表
        self.protocol_mapping = {
            "ss": "shadowsocks",
            "ssr": "shadowsocksr",
            "vmess": "vmess",
            "vless": "vless",
            "trojan": "trojan",
            "hysteria": "hysteria",
            "hysteria2": "hysteria2",
            "tuic": "tuic",
            "wireguard": "wireguard",
        }

        # 规则类型映射
        self.rule_mapping = {
            "DOMAIN": "domain",
            "DOMAIN-SUFFIX": "domain_suffix",
            "DOMAIN-KEYWORD": "domain_keyword",
            "IP-CIDR": "ip_cidr",
            "IP-CIDR6": "ip_cidr",
            "GEOIP": "geoip",
            "GEOSITE": "geosite",
            "PROCESS-NAME": "process_name",
            "MATCH": "final",
        }

    def load_mihomo_config(self, config_path: str) -> Dict[str, Any]:
        """加载 Mihomo 配置文件"""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                if config_path.endswith(".json"):
                    return json.load(f)
                else:
                    return yaml.safe_load(f)
        except Exception as e:
            raise Exception(f"加载配置文件失败: {e}")

    def convert_proxy_to_outbound(self, proxy: Dict[str, Any]) -> Dict[str, Any]:
        """将 Mihomo 代理节点转换为 Sing-box 出站配置"""
        proxy_type = proxy.get("type", "").lower()

        if proxy_type not in self.protocol_mapping:
            print(f"警告: 不支持的代理类型 {proxy_type}")
            return None

        outbound = {
            "tag": proxy.get("name", ""),
            "type": self.protocol_mapping[proxy_type],
        }

        # 基础连接信息
        if "server" in proxy:
            outbound["server"] = proxy["server"]
        if "port" in proxy:
            outbound["server_port"] = proxy["port"]

        # 添加 domain resolver 配置（1.12.0+ 格式）
        if "strategy" in proxy:
            outbound["domain_strategy"] = proxy["strategy"]
        else:
            outbound["domain_strategy"] = "prefer_ipv4"

        # 根据不同协议转换特定参数
        if proxy_type == "ss":
            self._convert_shadowsocks(proxy, outbound)
        elif proxy_type == "vmess":
            self._convert_vmess(proxy, outbound)
        elif proxy_type == "vless":
            self._convert_vless(proxy, outbound)
        elif proxy_type == "trojan":
            self._convert_trojan(proxy, outbound)
        elif proxy_type == "hysteria2":
            self._convert_hysteria2(proxy, outbound)
        elif proxy_type == "tuic":
            self._convert_tuic(proxy, outbound)

        return outbound

    def _convert_shadowsocks(self, proxy: Dict, outbound: Dict):
        """转换 Shadowsocks 配置（使用最新格式）"""
        if "cipher" in proxy:
            outbound["method"] = proxy["cipher"]
        if "password" in proxy:
            outbound["password"] = proxy["password"]

        # 处理插件配置
        if "plugin" in proxy:
            plugin_name = proxy["plugin"]
            if plugin_name in ["obfs", "simple-obfs", "obfs-local"]:
                # sing-box 支持 obfs-local 插件
                outbound["plugin"] = "obfs-local"
                if "plugin-opts" in proxy:
                    plugin_opts = proxy["plugin-opts"]
                    if isinstance(plugin_opts, dict):
                        plugin_opts_str = self._convert_plugin_opts_to_string(
                            "obfs", plugin_opts
                        )
                        outbound["plugin_opts"] = plugin_opts_str
                    else:
                        outbound["plugin_opts"] = str(plugin_opts)
            elif plugin_name == "v2ray-plugin":
                outbound["plugin"] = plugin_name
                if "plugin-opts" in proxy:
                    plugin_opts = proxy["plugin-opts"]
                    if isinstance(plugin_opts, dict):
                        plugin_opts_str = self._convert_plugin_opts_to_string(
                            plugin_name, plugin_opts
                        )
                        outbound["plugin_opts"] = plugin_opts_str
                    else:
                        outbound["plugin_opts"] = str(plugin_opts)
            else:
                print(f"警告: 不支持的插件类型 {plugin_name}")

        # 网络配置
        # Enabled network
        # One of tcp udp. Default is tcp + udp.
        # Both is enabled by default.
        # if proxy.get("udp", True):
        #     outbound["network"] = "udp"  # only UDP
        # else:
        #     outbound["network"] = "tcp"

        # 添加多路复用支持（如果需要）
        if "multiplex" in proxy:
            outbound["multiplex"] = proxy["multiplex"]

    def _convert_plugin_opts_to_string(self, plugin: str, opts: Dict) -> str:
        """将插件选项对象转换为字符串格式"""
        if plugin == "obfs":
            # obfs-local 插件选项格式（适用于 sing-box）
            result = []
            if "mode" in opts:
                mode = opts["mode"]
                if mode == "http":
                    result.append("obfs=http")
                elif mode == "tls":
                    result.append("obfs=tls")
                else:
                    result.append(f"obfs={mode}")
            if "host" in opts:
                result.append(f"obfs-host={opts['host']}")
            if "uri" in opts:
                result.append(f"obfs-uri={opts['uri']}")
            return ";".join(result)
        elif plugin == "v2ray-plugin":
            # v2ray-plugin 选项格式
            result = []
            if "mode" in opts:
                result.append(f"mode={opts['mode']}")
            if "host" in opts:
                result.append(f"host={opts['host']}")
            if "path" in opts:
                result.append(f"path={opts['path']}")
            if "tls" in opts and opts["tls"]:
                result.append("tls")
            if "skip-cert-verify" in opts and opts["skip-cert-verify"]:
                result.append("skip-cert-verify")
            return ";".join(result)
        else:
            # 默认格式：key=value;key=value
            result = []
            for key, value in opts.items():
                if isinstance(value, bool):
                    if value:
                        result.append(key)
                else:
                    result.append(f"{key}={value}")
            return ";".join(result)

    def _convert_vmess(self, proxy: Dict, outbound: Dict):
        """转换 VMess 配置"""
        if "uuid" in proxy:
            outbound["uuid"] = proxy["uuid"]
        if "alterId" in proxy:
            outbound["alter_id"] = proxy["alterId"]
        if "cipher" in proxy:
            outbound["security"] = proxy["cipher"]

        # 传输层配置
        if "network" in proxy:
            transport = {"type": proxy["network"]}

            if proxy["network"] == "ws":
                if "ws-opts" in proxy:
                    ws_opts = proxy["ws-opts"]
                    if "path" in ws_opts:
                        transport["path"] = ws_opts["path"]
                    if "headers" in ws_opts:
                        transport["headers"] = ws_opts["headers"]

            elif proxy["network"] == "grpc":
                if "grpc-opts" in proxy:
                    grpc_opts = proxy["grpc-opts"]
                    if "grpc-service-name" in grpc_opts:
                        transport["service_name"] = grpc_opts["grpc-service-name"]

            outbound["transport"] = transport

        # TLS 配置
        if proxy.get("tls"):
            tls_config = {"enabled": True}
            if "servername" in proxy:
                tls_config["server_name"] = proxy["servername"]
            if "skip-cert-verify" in proxy:
                tls_config["insecure"] = proxy["skip-cert-verify"]
            outbound["tls"] = tls_config

    def _convert_vless(self, proxy: Dict, outbound: Dict):
        """转换 VLESS 配置"""
        if "uuid" in proxy:
            outbound["uuid"] = proxy["uuid"]
        if "flow" in proxy:
            outbound["flow"] = proxy["flow"]

        # 传输层和 TLS 配置类似 VMess
        self._convert_vmess(proxy, outbound)

    def _convert_trojan(self, proxy: Dict, outbound: Dict):
        """转换 Trojan 配置"""
        if "password" in proxy:
            outbound["password"] = proxy["password"]

        # TLS 配置
        tls_config = {"enabled": True}
        if "servername" in proxy:
            tls_config["server_name"] = proxy["servername"]
        if "skip-cert-verify" in proxy:
            tls_config["insecure"] = proxy["skip-cert-verify"]
        outbound["tls"] = tls_config

    def _convert_hysteria2(self, proxy: Dict, outbound: Dict):
        """转换 Hysteria2 配置"""
        if "password" in proxy:
            outbound["password"] = proxy["password"]
        if "up" in proxy:
            outbound["up_mbps"] = proxy["up"]
        if "down" in proxy:
            outbound["down_mbps"] = proxy["down"]

        # TLS 配置
        tls_config = {"enabled": True}
        if "servername" in proxy:
            tls_config["server_name"] = proxy["servername"]
        if "skip-cert-verify" in proxy:
            tls_config["insecure"] = proxy["skip-cert-verify"]
        outbound["tls"] = tls_config

    def _convert_tuic(self, proxy: Dict, outbound: Dict):
        """转换 TUIC 配置"""
        if "uuid" in proxy:
            outbound["uuid"] = proxy["uuid"]
        if "password" in proxy:
            outbound["password"] = proxy["password"]
        if "congestion-controller" in proxy:
            outbound["congestion_control"] = proxy["congestion-controller"]

        # TLS 配置
        tls_config = {"enabled": True}
        if "servername" in proxy:
            tls_config["server_name"] = proxy["servername"]
        if "skip-cert-verify" in proxy:
            tls_config["insecure"] = proxy["skip-cert-verify"]
        outbound["tls"] = tls_config

    def convert_proxy_groups(self, proxy_groups: List[Dict]) -> List[Dict]:
        """转换代理组为 Sing-box 选择器出站"""
        outbounds = []

        for group in proxy_groups:
            group_type = group.get("type", "").lower()

            outbound = {
                "tag": group.get("name", ""),
                "type": "selector"
                if group_type in ["select", "url-test", "fallback"]
                else "urltest",
            }

            # 添加代理列表，处理 DIRECT -> direct 转换
            if "proxies" in group:
                converted_proxies = []
                for proxy in group["proxies"]:
                    if proxy.upper() == "DIRECT":
                        converted_proxies.append("direct")
                    elif proxy.upper() == "REJECT":
                        # REJECT 在 outbounds 中不适用，跳过或用其他代理替代
                        continue
                    else:
                        converted_proxies.append(proxy)
                outbound["outbounds"] = converted_proxies

            # URL 测试配置
            if group_type in ["url-test", "fallback"]:
                outbound["type"] = "urltest"
                if "url" in group:
                    outbound["url"] = group["url"]
                if "interval" in group:
                    outbound["interval"] = f"{group['interval']}s"
                if "tolerance" in group:
                    outbound["tolerance"] = group["tolerance"]

            outbounds.append(outbound)

        return outbounds

    def convert_rules(self, rules: List[str]) -> List[Dict]:
        """转换路由规则（使用新的 rule actions 格式）"""
        converted_rules = []

        for rule in rules:
            parts = rule.split(",")
            if len(parts) < 3:
                continue

            rule_type = parts[0].strip()
            rule_value = parts[1].strip()
            target = parts[2].strip()

            if rule_type not in self.rule_mapping:
                print(f"警告: 不支持的规则类型 {rule_type}")
                continue

            converted_rule = {}

            # 根据规则类型设置对应字段
            singbox_rule_type = self.rule_mapping[rule_type]

            if singbox_rule_type == "final":
                # 对于 MATCH 规则，使用默认出站
                if target == "Final":
                    target = "Proxies"  # 假设有一个名为 Proxies 的选择器组
                converted_rule["outbound"] = target
            elif singbox_rule_type in ["domain", "domain_suffix", "domain_keyword"]:
                converted_rule[singbox_rule_type] = [rule_value]
                # 处理目标（使用新的动作格式）
                if target.upper() == "DIRECT":
                    converted_rule["outbound"] = "direct"
                elif target.upper() == "REJECT":
                    converted_rule["action"] = "reject"
                    converted_rule["method"] = "default"  # 默认拒绝方法
                else:
                    converted_rule["outbound"] = target
            elif singbox_rule_type == "ip_cidr":
                converted_rule["ip_cidr"] = [rule_value]
                if target.upper() == "DIRECT":
                    converted_rule["outbound"] = "direct"
                elif target.upper() == "REJECT":
                    converted_rule["action"] = "reject"
                    converted_rule["method"] = "default"
                else:
                    converted_rule["outbound"] = target
            elif singbox_rule_type in ["geoip", "geosite"]:
                if self.disable_rule_sets:
                    # 使用传统的 GeoIP/Geosite 格式
                    # 未测试
                    converted_rule[singbox_rule_type] = rule_value.lower()
                else:
                    # 使用新的 rule-sets 格式
                    rule_set_tag = f"{singbox_rule_type}-{rule_value.lower()}"
                    converted_rule["rule_set"] = rule_set_tag

                if target.upper() == "DIRECT":
                    converted_rule["outbound"] = "direct"
                elif target.upper() == "REJECT":
                    converted_rule["action"] = "reject"
                    converted_rule["method"] = "default"
                else:
                    converted_rule["outbound"] = target
            elif singbox_rule_type == "process_name":
                converted_rule["process_name"] = [rule_value]
                if target.upper() == "DIRECT":
                    converted_rule["outbound"] = "direct"
                elif target.upper() == "REJECT":
                    converted_rule["action"] = "reject"
                    converted_rule["method"] = "default"
                else:
                    converted_rule["outbound"] = target

            converted_rules.append(converted_rule)

        return converted_rules

    def convert_dns(self, dns_config: Dict) -> Dict:
        """转换 DNS 配置（使用新的 1.12.0+ 格式）"""
        singbox_dns = {
            "servers": [],
            "rules": [],
            "disable_cache": False,
            "disable_expire": False,
        }

        # 添加默认本地 DNS 服务器（1.12.0+ 新格式）
        singbox_dns["servers"].append({
            "tag": "local",
            "address": "local",
            "detour": "direct",
        })

        # 转换 DNS 服务器
        if "nameserver" in dns_config:
            for i, server in enumerate(dns_config["nameserver"]):
                server_config = {
                    "tag": f"dns_{i}",
                    "address": server,
                    "detour": "direct",
                }

                singbox_dns["servers"].append(server_config)

        # 设置默认服务器
        if len(singbox_dns["servers"]) > 1:
            singbox_dns["final"] = singbox_dns["servers"][1][
                "tag"
            ]  # 使用第一个自定义服务器
        else:
            singbox_dns["final"] = "local"

        # 转换 DNS 规则（使用新的 DNS 规则动作格式）
        if "nameserver-policy" in dns_config:
            for domain, server in dns_config["nameserver-policy"].items():
                # 使用新的 DNS 规则动作格式
                base_rule = {
                    "action": "route",
                    "server": server,
                    "disable_cache": False,
                }

                if domain.startswith("geosite:"):
                    base_rule["rule_set"] = f"geosite-{domain[8:].lower()}"
                elif "/" in domain:  # IP CIDR
                    base_rule["ip_cidr"] = [domain]
                else:  # 域名
                    if domain.startswith("."):
                        base_rule["domain_suffix"] = [domain[1:]]
                    else:
                        base_rule["domain"] = [domain]

                singbox_dns["rules"].append(base_rule)

        return singbox_dns

    def convert_inbounds(self, inbounds_config: Dict) -> List[Dict]:
        """转换入站配置（使用新的地址格式）"""
        inbounds = []

        mixed_inbound = {
            "tag": "mixed-in",
            "type": "mixed",
            "listen": self.listen_addr,
            "listen_port": self.listen_port,
        }
        inbounds.append(mixed_inbound)

        # 如果有TUN配置或启用TUN参数，则添加TUN入站
        if (
            "tun" in inbounds_config and inbounds_config["tun"].get("enable")
        ) or self.enable_tun:
            # 基础 TUN 配置
            tun_inbound = {
                "tag": "tun-in",
                "type": "tun",
                "auto_route": True,
                "strict_route": True,
                "stack": "mixed",
            }

            # 如果启用高级 TUN 配置
            if self.enable_tun_advanced:
                tun_inbound.update({
                    # "interface_name": "tun0",
                    # IPv4 和 IPv6 地址配置 (sing-box 1.10.0+)
                    "address": [
                        "172.18.0.1/30",  # IPv4 地址
                        "fdfe:dcba:9876::1/126",  # IPv6 地址
                    ],
                    "mtu": 9000,
                    # Linux 推荐启用 auto_redirect 以获得更好的性能
                    "auto_redirect": True,
                    "auto_redirect_input_mark": "0x2023",
                    "auto_redirect_output_mark": "0x2024",
                    # 路由表和规则索引配置 (sing-box 1.10.0+)
                    "iproute2_table_index": 2022,
                    "iproute2_rule_index": 9000,
                    # 排除本地网络以避免路由环回
                    "route_exclude_address": [
                        "192.168.0.0/16",  # 本地网络
                        "10.0.0.0/8",  # 本地网络
                        "172.16.0.0/12",  # 本地网络
                        "127.0.0.0/8",  # 回环地址
                        "169.254.0.0/16",  # 链路本地地址
                        "224.0.0.0/4",  # 多播地址
                        "fc00::/7",  # IPv6 唯一本地地址
                        "fe80::/10",  # IPv6 链路本地地址
                        "ff00::/8",  # IPv6 多播地址
                    ],
                    # 启用独立于端点的 NAT
                    "endpoint_independent_nat": False,
                    # UDP NAT 超时时间
                    "udp_timeout": "5m",
                })
            else:
                # 简单配置，兼容旧版本
                tun_inbound["address"] = ["172.19.0.1/30"]

            # 根据原始配置调整部分设置
            if "tun" in inbounds_config:
                tun_config = inbounds_config["tun"]

                # 如果原配置指定了接口名称
                if "device" in tun_config:
                    tun_inbound["interface_name"] = tun_config["device"]

                # 如果原配置指定了 MTU
                if "mtu" in tun_config:
                    tun_inbound["mtu"] = tun_config["mtu"]

                # 如果原配置指定了 stack
                if "stack" in tun_config:
                    tun_inbound["stack"] = tun_config["stack"]

                # 如果原配置禁用了 auto_route
                if "auto-route" in tun_config and not tun_config["auto-route"]:
                    tun_inbound["auto_route"] = False
                    # 禁用依赖 auto_route 的功能
                    if self.enable_tun_advanced:
                        tun_inbound.pop("auto_redirect", None)
                        tun_inbound.pop("auto_redirect_input_mark", None)
                        tun_inbound.pop("auto_redirect_output_mark", None)
                        tun_inbound.pop("iproute2_table_index", None)
                        tun_inbound.pop("iproute2_rule_index", None)
                        tun_inbound.pop("route_exclude_address", None)

                # 如果原配置禁用了 strict_route
                if "strict-route" in tun_config and not tun_config["strict-route"]:
                    tun_inbound["strict_route"] = False

            inbounds.append(tun_inbound)

        return inbounds

    def generate_rule_sets(self, rules: List[str]) -> List[Dict]:
        """生成 rule-sets 配置以替代 GeoIP/Geosite"""
        if self.disable_rule_sets:
            return []

        rule_sets = []
        used_geoip = set()
        used_geosite = set()

        # 分析规则中使用的 GeoIP 和 Geosite
        for rule in rules:
            parts = rule.split(",")
            if len(parts) < 3:
                continue

            rule_type = parts[0].strip()
            rule_value = parts[1].strip()

            if rule_type == "GEOIP":
                used_geoip.add(rule_value.lower())
            elif rule_type == "GEOSITE":
                used_geosite.add(rule_value.lower())

        # 生成 GeoIP rule-sets
        for geoip in used_geoip:
            rule_sets.append({
                "tag": f"geoip-{geoip}",
                "type": "remote",
                "format": "binary",
                "url": f"https://raw.githubusercontent.com/SagerNet/sing-geoip/rule-set/geoip-{geoip}.srs",
                "download_detour": "direct",
            })

        # 生成 Geosite rule-sets
        for geosite in used_geosite:
            rule_sets.append({
                "tag": f"geosite-{geosite}",
                "type": "remote",
                "format": "binary",
                "url": f"https://raw.githubusercontent.com/SagerNet/sing-geosite/rule-set/geosite-{geosite}.srs",
                "download_detour": "direct",
            })

        return rule_sets

    def convert(self, mihomo_config: Dict) -> Dict:
        """执行完整的配置转换"""
        # 转换代理节点
        if "proxies" in mihomo_config:
            for proxy in mihomo_config["proxies"]:
                outbound = self.convert_proxy_to_outbound(proxy)
                if outbound:
                    self.singbox_config["outbounds"].append(outbound)

        # 转换代理组
        if "proxy-groups" in mihomo_config:
            group_outbounds = self.convert_proxy_groups(mihomo_config["proxy-groups"])
            self.singbox_config["outbounds"].extend(group_outbounds)

        # 添加直连出站（不再使用 legacy special outbounds）
        self.singbox_config["outbounds"].append({"tag": "direct", "type": "direct"})

        # 转换路由规则
        if "rules" in mihomo_config:
            self.singbox_config["route"]["rules"] = self.convert_rules(
                mihomo_config["rules"]
            )
            # 生成 rule-sets
            rule_sets = self.generate_rule_sets(mihomo_config["rules"])
            if rule_sets:
                self.singbox_config["route"]["rule_set"] = rule_sets

        # 转换 DNS 配置
        if "dns" in mihomo_config:
            self.singbox_config["dns"] = self.convert_dns(mihomo_config["dns"])

        # 转换入站配置
        if "tun" in mihomo_config or "mixed-port" in mihomo_config:
            self.singbox_config["inbounds"] = self.convert_inbounds(mihomo_config)

        # 添加实验性配置
        experimental_config = {
            "cache_file": {"enabled": True, "path": "cache.db"},
            "clash_api": {
                "external_controller": f"127.0.0.1:{self.clash_api_port}",
                "external_ui": "ui",
                "external_ui_download_url": "https://github.com/Zephyruso/zashboard/releases/latest/download/dist.zip",
                "external_ui_download_detour": "Proxies",
                "secret": "",
                "default_mode": "rule",
            },
        }

        self.singbox_config["experimental"] = experimental_config

        return self.singbox_config


def main():
    parser = argparse.ArgumentParser(
        description="Mihomo (ClashMeta) 配置转换为 Sing-box 配置",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  %(prog)s config.yaml                    # 基本转换
  %(prog)s config.yaml -o output.json     # 指定输出文件
  %(prog)s config.yaml --listen 0.0.0.0   # 监听所有接口, 不建议
  %(prog)s config.yaml --port 7891 --tun  # 自定义端口并启用高级 TUN
  %(prog)s config.yaml --tun --tun-simple # 启用简单 TUN (兼容模式)
        """,
    )

    # 基本参数组
    basic_group = parser.add_argument_group("基本选项")
    basic_group.add_argument(
        "input", help="输入的 Mihomo 配置文件路径 (支持 YAML/JSON)"
    )
    basic_group.add_argument(
        "-o",
        "--output",
        help="输出的 Sing-box 配置文件路径",
        default="singbox_config.json",
    )
    # sing-box uses JSON for configuration files.  # https://sing-box.sagernet.org/configuration/
    # basic_group.add_argument("--format",
    #                         # choices=["json", "yaml"],
    #                         default="json",
    #                         help="输出格式 (默认: json)")

    # 网络参数组
    network_group = parser.add_argument_group("网络配置")
    network_group.add_argument(
        "--listen", "-l", default="127.0.0.1", help="入站监听地址 (默认: 127.0.0.1)"
    )
    network_group.add_argument(
        "--port", "-p", type=int, default=7890, help="入站监听端口 (默认: 7890)"
    )
    network_group.add_argument("--tun", "-t", action="store_true", help="启用 TUN 入站")
    network_group.add_argument(
        "--tun-simple", action="store_true", help="使用简单 TUN 配置（兼容旧版本）"
    )

    # 高级参数组
    advanced_group = parser.add_argument_group("高级选项")
    advanced_group.add_argument(
        "--disable-rule-sets",
        action="store_true",
        help="禁用 rule-sets，使用传统 GeoIP/Geosite",
    )
    advanced_group.add_argument(
        "--log-level",
        choices=["trace", "debug", "info", "warn", "error"],
        default="info",
        help="日志级别 (默认: info)",
    )
    advanced_group.add_argument(
        "--clash-api-port", type=int, default=9090, help="Clash API 端口 (默认: 9090)"
    )

    args = parser.parse_args()

    # 参数验证
    if not Path(args.input).exists():
        print(f"错误: 输入文件不存在: {args.input}")
        sys.exit(1)

    if not (1 <= args.port <= 65535):
        print(f"错误: 端口号必须在 1-65535 范围内: {args.port}")
        sys.exit(1)

    if not (1 <= args.clash_api_port <= 65535):
        print(f"错误: Clash API 端口号必须在 1-65535 范围内: {args.clash_api_port}")
        sys.exit(1)

    try:
        # 创建转换器
        converter = MihomoToSingboxConverter(
            listen_addr=args.listen,
            listen_port=args.port,
            enable_tun=args.tun or args.tun_simple,
            log_level=args.log_level,
            clash_api_port=args.clash_api_port,
            disable_rule_sets=args.disable_rule_sets,
            enable_tun_advanced=not args.tun_simple,
        )

        # 加载 Mihomo 配置
        print(f"正在加载 Mihomo 配置: {args.input}")
        mihomo_config = converter.load_mihomo_config(args.input)

        # 执行转换
        print("正在转换配置...")
        singbox_config = converter.convert(mihomo_config)

        # 保存结果
        print(f"正在保存 Sing-box 配置: {args.output}")
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(singbox_config, f, indent=2, ensure_ascii=False)
            # if args.format == "json":
            #     json.dump(singbox_config, f, indent=2, ensure_ascii=False)
            # else:
            #     yaml.dump(singbox_config, f, default_flow_style=False, allow_unicode=True)

        print("转换完成!")
        print(f"输出文件: {args.output}")

    except Exception as e:
        print(f"转换失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

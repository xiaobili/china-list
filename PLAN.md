## 修改dnsmasq-china-list适配Adguardhome

## 1. 下载 dnsmasq-china-list .conf 文件

#### 链接
仓库地址
    https://github.com/Loyalsoldier/v2ray-rules-dat
##### 国内分组文件(在最新发行版中)
1. apple-cn.txt
2. google-cn.txt
3. china-list.txt

#### 国外分组文件(在最新发行版中)
1. proxy.txt

## 2. 适配Adguardhome
将下载的txt 文件中的地址（例如 xxx.com）格式内容修改为 [/xxx.com/]dns1 dns2格式，并保存为新的 .txt 文件
说明1：dns1 dns2为DNS服务器地址
说明2: 多个DNS服务器地址用空格隔开
说明3: 国内分组和国外分组可以设置不同的DNS服务器地址

最后，将所有文件合并到同一个文件当中，并命名为 chinalist-for-adguard.txt
## 3. 生成修改脚本
根据以上需求，生成 shell 脚本，并保存为 adguardhome_dns.py 文件
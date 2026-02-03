## 修改dnsmasq-china-list适配Adguardhome

## 1. 下载 dnsmasq-china-list .conf 文件

#### 链接 
1. https://raw.githubusercontent.com/felixonmars/dnsmasq-china-list/master/accelerated-domains.china.conf
2. https://raw.githubusercontent.com/felixonmars/dnsmasq-china-list/master/apple.china.conf
3. https://raw.githubusercontent.com/felixonmars/dnsmasq-china-list/master/google.china.conf

## 2. 适配Adguardhome
将 .conf 文件中 server=/265.com/114.114.114.114 格式内容修改为 [/265.com/]114.114.114.114格式，并保存为 .txt 文件

## 3. 生成修改脚本
生成 shell 脚本
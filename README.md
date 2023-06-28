# tang_ying
tangying后端


## Installation

## 安装sqlite3(在python3安装前)
django启动报错：`django.core.exceptions.ImproperlyConfigured: SQLite 3.9.0 or later is required (found 3.7.17)`
或：`django.db.utils.NotSupportedError: deterministic=True requires SQLite 3.8.3`

1.官网下载高版本sqlite3安装包
>wget https://sqlite.org/2022/sqlite-autoconf-3390200.tar.gz --no-check-certificate

2.编译安装

> ./configure --prefix=/usr/local/sqlite3 <br>
make && make install 

3.替换版本

>mv /usr/bin/sqlite3 /usr/bin/sqlite3_bk<br>
ln -s /usr/local/sqlite3/bin/sqlite3 /usr/bin/sqlite3

4.添加环境变量,将新版本lib文件添加进环境

> vim /etc/profile<br>
#添加内容(路径根据sqlite库具体安装位置)<br>
export LD_LIBRARY_PATH="/usr/local/sqlite3/lib" <br>
source /etc/profile

`到此Linux环境中sqlite版本已更新`

### 安装Python3（若已安装sqlite则需重新编译）

1. 下载安装包
    > wget https://www.python.org/ftp/python/3.9.8/Python-3.9.8.tar.xz

2. 安装依赖
    >yum -y install zlib-devel bzip2-devel openssl-devel sqlite-devel gcc make

3. 编译安装

    修改安装配置/Module/Setup文件加载ssl模块，去掉以下注释
    ```python
    # Socket module helper for socket(2)
    _socket socketmodule.c

    # Socket module helper for SSL support; you must comment out the other
    # socket line above, and possibly edit the SSL variable:
    SSL=/usr/local/ssl
    _ssl _ssl.c \
            -DUSE_SSL -I$(SSL)/include -I$(SSL)/include/openssl \
            -L$(SSL)/lib -lssl -lcrypto
    ```
    >./configure LDFLAGS="-L/usr/local/sqlite3/lib" CPPFLAGS="-I /usr/local/sqlite3/include" LD_RUN_PATH=/usr/local/sqlite3/lib 
    
    `此参数是解决django.db.utils.NotSupportedError: deterministic=True requires SQLite 3.8.3报错的关键！`<br>
    make && make install

### 创建python3虚拟环境

1. 下载python工具包virtualenv(用python3的pip)
    >pip3 install virtualenv

2. 创建python虚拟环境(切换到py3env同级目录)
    >python3 -m virtualenv py3env

3. 切换到虚拟环境
    >source py3env/bin/activate

### 安装django(4.0.6),uwsgi

>pip install django==4.0.6 uwsgi -i http://pypi.douban.com/simple --trusted-host pypi.douban.com

### 解压安装包，安装项目依赖
>git clone https://github.com/Babelquant/tang_ying

>pip install -r requirements.txt -i http://pypi.douban.com/simple --trusted-host pypi.douban.com

## 切换到项目目录，创建数据模型
>python manage.py makemigrations

    Migrations for 'data':
    data/migrations/0001_initial.py
        - Create model Concepts
        - Create model ConceptStretagy
        - Create model HotStocks
        - Create model LimitupStocks
        - Create model Securities

>python manage.py migrate

    Operations to perform:
    Apply all migrations: admin, auth, contenttypes, data, sessions
    Running migrations:
    Applying contenttypes.0001_initial... OK
    Applying auth.0001_initial... OK
    Applying admin.0001_initial... OK
    Applying admin.0002_logentry_remove_auto_add... OK
    Applying admin.0003_logentry_add_action_flag_choices... OK
    Applying contenttypes.0002_remove_content_type_name... OK
    Applying auth.0002_alter_permission_name_max_length... OK
    Applying auth.0003_alter_user_email_max_length... OK
    Applying auth.0004_alter_user_username_opts... OK
    Applying auth.0005_alter_user_last_login_null... OK
    Applying auth.0006_require_contenttypes_0002... OK
    Applying auth.0007_alter_validators_add_error_messages... OK
    Applying auth.0008_alter_user_username_max_length... OK
    Applying auth.0009_alter_user_last_name_max_length... OK
    Applying auth.0010_alter_group_name_max_length... OK
    Applying auth.0011_update_proxy_permissions... OK
    Applying auth.0012_alter_user_first_name_max_length... OK
    Applying data.0001_initial... OK
    Applying sessions.0001_initial... OK

### 添加项目定时任务
> python manage.py crontab add

> python manage.py crontab show

### 安装nginx并配置
1. 下载安装包，编译安装

>wget http://nginx.org/download/nginx-1.18.0.tar.gz

>./configuer<br>
make && make install

2. 替换nginx.conf为以下内容

        events {
            worker_connections  1024;
        }
        http {
            include       mime.types;
            default_type  application/octet-stream;
            sendfile        on;
            server {
                listen 80; # 这里nginx监听得是80端口,浏览器输入域名不需要加端口了就
                server_name  127.0.0.1:80; #改为自己的域名，没域名修改为127.0.0.1:80
                charset utf-8;
                location / {
                include uwsgi_params;
                uwsgi_pass 127.0.0.1:8000;  #端口要和uwsgi里配置的一样
                uwsgi_param UWSGI_SCRIPT tangying.wsgi;  #wsgi.py所在的目录名+.wsgi
                uwsgi_param UWSGI_CHDIR /usr/local/tangying; #项目路径
                }
                location /static/ {
                alias /usr/local/tangying/app/static/; #静态资源路径
                }
            }
        }

3. 进入安装目录 执行 ./nginx -t 命令先检查配置文件是否有错，没有错就执行以下命令：./nginx，终端没有任何提示就证明nginx启动成功

### 启动项目(注意uwsgi配置中的项目路径)
>uwsgi -x tangying.xml 

    ps -ef|grep uwsgi 检查是否启动成功
# 推送到 GitHub + 服务器生产部署

## 一、注册与邮件

- 用户在前端填写邮箱 + 密码 → 调用 `POST /v1/auth/register` → 后端写入数据库并返回登录态。
- **欢迎邮件**：若在 `.env` 中配置了 SMTP（`SMTP_HOST`、`SMTP_USER`、`SMTP_PASSWORD`）并设置 `SMTP_SEND_WELCOME_EMAIL=true`，注册成功后会向该邮箱发送一封欢迎邮件。详见 [docs/EMAIL_SETUP.md](EMAIL_SETUP.md)。
- **邮箱验证**：当前未实现；如需“点击链接验证邮箱”，需在 User 表增加 `email_verified` 字段并实现验证接口。

---

## 二、快速启动（本地）

**Windows（项目根目录）：**

```cmd
scripts\start.bat
```

或：

```cmd
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

**Linux / macOS：**

```bash
chmod +x scripts/start.sh
./scripts/start.sh
```

启动后访问：<http://127.0.0.1:8000> 或 <http://localhost:8000/content-workflow>。

---

## 三、推送到 GitHub

### 1. 确认不要提交的内容

项目里已加 `.gitignore`，以下**不会**被提交：

- `.env`（密钥、配置）
- `*.db`（SQLite 数据库）
- `__pycache__/`、`.venv/` 等

**不要把 `.env` 或真实密钥推到 GitHub。**

### 2. 在项目根目录执行

```bash
# 若还没初始化 Git
git init

# 查看状态（应看不到 .env、*.db）
git status

# 添加所有文件（.gitignore 会自动排除）
git add .

# 提交
git commit -m "feat: 内容永动机 ToC + 用户用量控制"

# 在 GitHub 网页上新建仓库（不要勾选 README/license），记下仓库地址，例如：
# https://github.com/你的用户名/so_few.git

# 添加远程（本仓库示例）
git remote add origin https://github.com/ydorothy222/SO_FEW_ai_content_analyzer.git

# 推送（主分支叫 main 时）
git branch -M main
git push -u origin main
```

若主分支是 `master`：

```bash
git push -u origin master
```

### 3. 以后日常推送

```bash
git add .
git commit -m "简短说明"
git push
```

---

## 四、服务器生产环境部署

### 已打包上传到服务器后，如何运行（简明步骤）

**要求**：服务器需 **Python 3.8 或以上**（Python 3.6 无法安装当前依赖）。可用 `python3 --version` 查看版本。

假设代码已在服务器目录（例如 `/www/wwwroot/content_generator` 或你上传解压后的路径），按顺序执行：

**1. 进入项目根目录**（能看到 `src/`、`requirements.txt` 的目录）

```bash
cd /path/to/so_few
```

**2. 创建虚拟环境并安装依赖**

```bash
python3 -m venv .venv
source .venv/bin/activate    # Linux/macOS
pip install --upgrade pip   # 服务器 pip 过旧会报错找不到 fastapi 等，先升级
pip install -r requirements.txt
```

**3. 在项目根或 `src/` 下创建 `.env`**

```bash
cp .env.example .env
nano .env   # 或 vi .env，填入 DASHSCOPE_API_KEY、JWT_SECRET 等
```

至少填：`DASHSCOPE_API_KEY`、`JWT_SECRET`（生产环境务必改成强随机字符串）。

**4. 启动服务**

```bash
# 方式一：直接命令（2 个 worker，端口 8000）
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 2

# 方式二：用脚本（需在项目根目录）
chmod +x scripts/start_prod.sh
./scripts/start_prod.sh
```

**若 `pip install -r requirements.txt` 报错「Could not find a version that satisfies fastapi...」：**

1. **本产品需要 Python 3.8 或以上**。若服务器当前是 **Python 3.6**（虚拟环境路径里有 `python3.6`），镜像里只有 FastAPI 到 0.83，而 0.100+ 又不支持 3.6，所以会装不上。请先安装 Python 3.8 或 3.9，再用它建虚拟环境：
   ```bash
   # CentOS / AlmaLinux / 阿里云 ECS 常见做法
   dnf install python38 -y
   # 或 yum install python38 -y

   cd /www/wwwroot/content_generator
   rm -rf .venv
   python3.8 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt -i https://pypi.org/simple
   ```
   若系统里没有 `python3.8`，可搜「CentOS 安装 Python 3.8」按教程装好后再执行上面。

2. 若服务器已是 Python 3.8+，只是镜像没有新版本，请改用**官方 PyPI** 再装：
   ```bash
   pip install -r requirements.txt -i https://pypi.org/simple
   ```

**5. 验证**

- 本机：`curl http://127.0.0.1:8000/health` 应返回 `{"status":"ok"}`
- 外网：若防火墙已放行 8000，浏览器访问 `http://服务器IP:8000/content-workflow`

**6. 后台常驻（可选）**

用 `nohup` 或 `screen` 让进程在断开 SSH 后继续运行：

```bash
nohup python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 2 > sofew.log 2>&1 &
```

或配置 systemd（见下文「用 systemd 守护进程」）。

---

### 1. 若用 Git 在服务器上拉代码

```bash
git clone https://github.com/ydorothy222/SO_FEW_ai_content_analyzer.git so_few
cd so_few
```

然后从上面「2. 创建虚拟环境并装依赖」开始执行。

### 2. 创建虚拟环境并装依赖

```bash
python3 -m venv .venv
source .venv/bin/activate   # Linux/macOS
# Windows:  .venv\Scripts\activate

pip install --upgrade pip   # 若服务器 pip 很旧，先升级再装依赖
# 若清华源报错「找不到 fastapi 0.115」，换用官方源或阿里云源：
pip install -r requirements.txt -i https://pypi.org/simple
# 或阿里云（国内服务器常用）：
# pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
```

### 3. 在服务器上建 .env

**不要**从本机复制带真实密钥的 `.env` 到 GitHub。在服务器上**新建**一份：

```bash
# 在项目根目录
cp .env.example .env
# 或用 vi/nano 新建 .env，填入生产环境的值
```

至少配置：

- `DASHSCOPE_API_KEY`（必填，内容永动机要调 LLM）
- `JWT_SECRET`（必填，且要用**强随机字符串**，不要用默认的）
- `ADMIN_USERNAME` / `ADMIN_PASSWORD`（可选，默认 YANGRONG）
- 若用 OSS/转写：`OSS_*` 等

### 4. 启动服务（生产）

```bash
chmod +x scripts/start_prod.sh
./scripts/start_prod.sh
```

或直接：

```bash
# 2 个 worker，端口 8000
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 2
```

环境变量可改 worker 数和端口：

```bash
WORKERS=4 PORT=8000 ./scripts/start_prod.sh
```

### 5. 用 Nginx 做反向代理（推荐）

让 Nginx 监听 80/443，把请求转到本机 8000：

```nginx
server {
    listen 80;
    server_name 你的域名或IP;
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

然后 `nginx -t` 检查、`systemctl reload nginx`。

### 6. 用 systemd 守护进程（可选）

新建 `/etc/systemd/system/sofew.service`：

```ini
[Unit]
Description=Sofew Content Workflow
After=network.target

[Service]
Type=simple
User=你的用户名
WorkingDirectory=/path/to/so_few
Environment="PATH=/path/to/so_few/.venv/bin"
ExecStart=/path/to/so_few/.venv/bin/python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 2
Restart=always

[Install]
WantedBy=multi-user.target
```

然后：

```bash
sudo systemctl daemon-reload
sudo systemctl enable sofew
sudo systemctl start sofew
sudo systemctl status sofew
```

---

## 五、小结

| 项目           | 说明 |
|----------------|------|
| 注册是否发邮件 | **否**，仅用邮箱当账号，不发验证/欢迎邮件 |
| 快速启动       | Windows: `scripts\start.bat`；Linux: `./scripts/start.sh` |
| 推 GitHub      | `git add .` → `git commit` → `git remote add origin <url>` → `git push`，且不要提交 `.env` |
| 生产部署       | 服务器上 `git clone` → 建 `.env` → `pip install -r requirements.txt` → `./scripts/start_prod.sh`，建议前接 Nginx + systemd |

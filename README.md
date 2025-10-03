# Ernie-2api (百度文心一言高性能API代理) 🤖

<p align="center">
  <a href="https://github.com/lzA6/Ernie-2api/blob/main/LICENSE"><img src="https://img.shields.io/github/license/lzA6/Ernie-2api?color=blue" alt="License"></a>
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/Framework-FastAPI-green.svg" alt="Framework">
  <img src="https://img.shields.io/badge/Proxy-Nginx-purple.svg" alt="Proxy">
  <img src="https://img.shields.io/badge/Deployment-Docker-blueviolet.svg" alt="Deployment">
</p>

这是一个企业级的、高性能的百度文心一言网页版API代理服务。它不仅将API封装成与OpenAI格式兼容的标准接口，还通过**Nginx粘性会话**、**令牌认证**等高级功能，提供了极致的稳定性和安全性。

本项目是 `Qwen-2api` 的姊妹项目，继承了其稳定、高效、易于部署的核心设计哲学，并针对文心一言独特的认证机制进行了深度定制。

## ✨ 核心特性

-   **🚀 企业级架构**: 采用 **Nginx + FastAPI** 的生产级架构，Nginx负责负载均衡与会话保持，FastAPI负责核心AI逻辑，性能卓越。
-   **🎯 终极粘性会话**: 利用 Nginx 对 `Authorization` 头进行哈希，100%确保同一用户的连续请求命中同一后台实例，从根本上解决流式对话的潜在问题。
-   **🛡️ 高稳定性**: 基于个人长期有效的认证信息，服务稳定可靠。
-   **🔒 令牌认证**: 内置 `API_MASTER_KEY` 认证，保护您的API服务不被滥用。
-   **🐳 一键部署**: 提供标准的 Docker Compose 配置，无论是本地还是服务器，都能轻松启动。
-   **💡 智能流解析**: 自动将文心一言的SSE事件流实时转换为标准的OpenAI增量流格式，完美兼容各类客户端。

---

## 🔬 与 Qwen-2api 的技术差异深度剖析

作为姊妹项目，`Ernie-2api` 沿用了 `Qwen-2api` 的黄金标准架构。然而，由于逆向目标的不同，它们在核心技术挑战和实现上各有侧重。

| 技术点 | Qwen-2api (通义千问) | Ernie-2api (文心一言) |
| :--- | :--- | :--- |
| **核心挑战** | **响应流的解析** | **认证体系的复杂性** |
| **认证机制** | 相对简单 (`Cookie` + `x-xsrf-token`) | **极其复杂** (`Cookie` + `acs-token` + 动态`sign`) |
| **流式响应** | **累积式数据流** (每帧都包含从头到尾的全部内容) | **标准增量流** (每帧只包含新增内容) |
| **Provider实现** | 核心在于**状态化解析器**，通过比对前后两帧内容来计算增量。 | 核心在于**请求构建**，需要正确组合三项动态凭证。流解析相对简单，只需提取`data.content`即可。 |
| **稳定性** | 依赖两项长期有效的凭证，非常稳定。 | 依赖三项凭证，其中`acs-token`和`sign`可能有较短的时效性，**对凭证更新的要求更高**。 |

**总结**: `Qwen-2api` 的技术难点在于**“如何处理数据”**，而 `Ernie-2api` 的技术难点在于**“如何通过验证”**。本项目针对文心一言独特的认证机制，在 `baidu_provider.py` 中构建了专门的请求签名和头信息生成逻辑。

---

## 部署方案选择

您可以根据需求选择最适合您的部署方式：

-   [**方案一：本地部署**](#-方案一本地部署) - **(推荐)** 在您自己的电脑或服务器上快速运行，享受完整功能。
-   [**方案二：Hugging Face 云端部署**](#-方案二hugging-face-云端部署) - **(实验性)** 免费将服务部署到云端，获得一个可公开访问的API网址。

---

## ⚙️ 方案一：本地部署

通过 Docker，只需几步即可在您的电脑上拥有一个私有的、高性能的文心一言API服务。

### 前提条件

-   已安装 [**Docker**](https://www.docker.com/products/docker-desktop/) 和 **Docker Compose**。
-   已安装 [**Git**](https://git-scm.com/)。

### 第 1 步：获取项目代码

打开您的命令行（终端），克隆本项目到您的电脑上。

```bash
git clone https://github.com/lzA6/Ernie-2api.git
cd Ernie-2api
```

### 第 2 步：获取三项核心认证信息 (关键步骤)

本项目通过模拟网页版请求实现，因此需要您提供三项核心认证信息。

1.  使用您的浏览器登录 **[文心一言官网](https://ernie.baidu.com/chat)**。
2.  按 `F12` 打开开发者工具，并切换到 **网络 (Network)** 面板。
3.  随便发送一条消息，在网络请求列表中找到一个名为 **`conversation/v2`** 的请求。
4.  点击该请求，在右侧面板中仔细查找并**完整复制**以下三项信息：

    *   **`Cookie`**:
        *   在 **标头 (Headers)** -> **请求标头 (Request Headers)** 中找到 `cookie` 字段。它的值非常长。
    *   **`acs-token`**:
        *   同样在 **请求标头 (Request Headers)** 中找到 `acs-token` 字段。
    *   **`sign`**:
        *   切换到 **有效负载 (Payload)** 选项卡，在 **请求负载 (Request Payload)** 中找到 `sign` 字段。

> **⚠️ 重要提示**: `acs-token` 和 `sign` 可能具有时效性。如果服务在一段时间后开始报错，您可能需要重复此步骤来获取新的凭证。

### 第 3 步：配置您的项目

1.  在 `Ernie-2api` 文件夹中，找到名为 `.env.example` 的文件。
2.  **将它复制并重命名为 `.env`**。
3.  用文本编辑器打开这个新的 `.env` 文件，将您在**第 2 步**中获取到的三项信息，以及您自定义的API密钥，填写到对应的位置。

```env
# .env (配置示例)
LISTEN_PORT=8083
API_MASTER_KEY=your_super_secret_master_key_123
BAIDU_ACCOUNT_1_COOKIE="在这里粘贴你的完整Cookie"
BAIDU_ACCOUNT_1_ACS_TOKEN="在这里粘贴你的acs-token"
BAIDU_ACCOUNT_1_SIGN="在这里粘贴你的sign值"
```

### 第 4 步：创建共享网络 (仅首次需要)

由于本项目采用多容器架构，需要创建一个共享网络让它们互相通信。

```bash
docker network create shared_network
```

### 第 5 步：启动服务！

回到您的命令行（确保仍在 `Ernie-2api` 文件夹内），运行以下命令：

```bash
docker compose up -d --build```
Docker 将会自动构建镜像并在后台启动Nginx和Python服务。

### 第 6 步：测试您的本地API

```bash
curl http://localhost:8083/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_super_secret_master_key_123" \
  -d '{
    "model": "ernie-4.5-turbo",
    "messages": [{"role": "user", "content": "你好，请用中文介绍一下你自己！"}]
  }'
```
**注意：** 请将 `your_super_secret_master_key_123` 替换为您在 `.env` 文件中设置的 `API_MASTER_KEY`。

如果成功返回了文心一言的回答，恭喜您，本地部署成功！

---

## ☁️ 方案二：Hugging Face 云端部署

> **⚠️ 架构限制**: Hugging Face Spaces 的免费实例目前**不支持** Docker Compose 多容器部署。因此，部署到HF时，我们将**绕过Nginx**，直接暴露FastAPI服务。这意味着您将**失去Nginx带来的粘性会话和性能优势**，但这对于轻量级使用或公开演示仍然是一个很好的选择。

### 第 1 步：创建 Hugging Face Space

1.  访问 [Hugging Face New Space](https://huggingface.co/new-space) 页面。
2.  **Space name**: 给它起一个全局唯一的名字，例如 `my-ernie-api`。
3.  **Space SDK**: **务必选择 `Docker`**，模板选择 **`Blank`**。
4.  **Public/Private**: 选择 `Public` 以享受免费资源。
5.  点击 **Create Space**。

### 第 2 步：配置云端环境变量 (Secrets)

这是**云端部署最核心的一步**。我们需要把本地 `.env` 文件里的所有配置，安全地设置到Hugging Face的后台。

1.  在您刚刚创建的Space页面，点击 **Settings** 选项卡。
2.  在左侧菜单中，点击 **Secrets**。
3.  点击 **New secret**，然后**逐一添加**您在本地 `.env` 文件中配置的所有变量。

**您需要添加以下所有Secrets：**
| Secret Name                 | Secret Value                               |
| --------------------------- | ------------------------------------------ |
| `LISTEN_PORT`               | `8083`                                     |
| `API_MASTER_KEY`            | `your_super_secret_master_key_123`         |
| `BAIDU_ACCOUNT_1_COOKIE`    | `您账号1的Cookie值`                        |
| `BAIDU_ACCOUNT_1_ACS_TOKEN` | `您账号1的acs-token值`                     |
| `BAIDU_ACCOUNT_1_SIGN`      | `您账号1的sign值`                          |

### 第 3 步：准备并推送代码

1.  **修改 `README.md` 以适配Hugging Face**
    用文本编辑器打开您本地 `Ernie-2api` 文件夹中的 `README.md` 文件（也就是本文档），在**最顶部**加入以下内容：
    ```yaml
    ---
    title: Ernie 2API
    emoji: 🤖
    colorFrom: blue
    colorTo: green
    sdk: docker
    app_port: 8083
    ---
    ```
    *（`sdk: docker` 和 `app_port: 8083` 这两行是告诉Hugging Face如何运行您的项目的关键！）*

2.  **推送代码到Hugging Face**
    回到您的命令行（确保在 `Ernie-2api` 文件夹内），执行以下命令：
    ```bash
    # 设置您的Git身份 (如果是第一次使用)
    git config --global user.name "你的GitHub或HF用户名"
    git config --global user.email "你的邮箱"

    # 关联并推送代码
    git init
    git remote add huggingface https://huggingface.co/spaces/[你的HF用户名]/[你的Space名]
    git add .
    git commit -m "Deploy to Hugging Face"
    git push --force huggingface main
    ```
    *（推送时，用户名为您的HF用户名，密码为您在[HF Access Tokens页面](https://huggingface.co/settings/tokens)创建的`write`权限的Token。）*

### 第 4 步：测试您的云端API

推送成功后，Hugging Face会自动部署您的服务。等待Space状态变为 `Running` 后，您就可以使用它的公开网址进行测试了！

```bash
# 将URL替换成您的Space地址
curl https://[你的HF用户名]-[你的Space名].hf.space/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_super_secret_master_key_123" \
  -d '{
    "model": "ernie-4.5-turbo",
    "messages": [{"role": "user", "content": "你好，你现在部署在Hugging Face上了吗？"}]
  }'
```

---

## 📜 License

本项目采用 [Apache License 2.0](LICENSE) 开源。

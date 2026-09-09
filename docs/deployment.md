# 跨电脑访问与部署

## 当前可用：Cloudflare Quick Tunnel

运行 `scripts/start_public.ps1` 会启动带环境变量密码的本地 Streamlit，并生成随机 `trycloudflare.com` 地址。该方式会把页面请求和看板展示的数据经 Cloudflare 转发，无需开放路由器端口，但本机和脚本窗口必须保持运行，URL 会在重启后变化，只适合获得明确数据外发授权后的测试与临时分享。

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start_public.ps1
```

## 长期地址：Streamlit Community Cloud

项目已经提供 `streamlit_app.py`、`requirements.txt`、`.streamlit/config.toml` 和 GitHub Actions 测试。把项目提交到 GitHub 后，在 Streamlit Community Cloud 选择该仓库和 `streamlit_app.py` 即可获得稳定的 `streamlit.app` 地址。私密访问密码放入平台 Secrets/环境变量 `DASHBOARD_PASSWORD`，不要提交 `.env`。仓库默认建议设为 Private，因为报告里包含完整研究结果。

## 自建服务器

项目提供 `Dockerfile`，可部署到支持 Docker 的云服务器。对外服务时应在反向代理层增加 TLS、访问控制和日志，避免直接暴露 Streamlit 端口。

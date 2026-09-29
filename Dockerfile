# 请别再加前端编译了，前端编译非常占用工作流时间 ,可以 编译后复制到static目录再提交pull request
FROM --platform=$BUILDPLATFORM ghcr.io/rachelos/base-full:latest AS runtime

ENV PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ENV INSTALL=True
ENV BROWSER_TYPE=webkit
ENV PLANT_PATH=/app/env
ENV WEREAD_LIC_PATH=/app/data/wx.lic
ENV WEREAD_PROFILE_DIR=/app/data/weread-chrome-profile
ENV PLAYWRIGHT_BROWSERS_PATH=/app/env/driver/_x86_64

WORKDIR /app
RUN echo "1.0.$(date +%Y%m%d.%H%M)">>docker_version.txt
COPY requirements.txt install.sh ./
RUN apt-get update && apt-get install -y --no-install-recommends bash && rm -rf /var/lib/apt/lists/* \
    && chmod +x /app/install.sh && /app/install.sh

COPY . .
COPY config.example.yaml /app/config.yaml
# EOS-658: persist webkit in the image layer (do not docker-commit browsers).
# install.sh already installs BROWSER_TYPE=webkit when INSTALL=True; this RUN
# keeps webkit (MP login) next to chromium (weread cookie refresh).
# A webkit install failure fails the build. Chromium stays best-effort as
# before, but a failure now prints a WARNING instead of being swallowed.
# 微信读书 Cookie 自动刷新：安装 Chromium 浏览器（与 webkit 共存）
RUN set -e; \
    VENV=$(ls -d /app/env_* | head -1); \
    if [ -z "$VENV" ]; then echo "ERROR: no /app/env_* virtualenv found" >&2; exit 1; fi; \
    export PLAYWRIGHT_BROWSERS_PATH=/app/env/driver/_$(uname -m); \
    "$VENV/bin/python3" -m playwright install webkit; \
    { "$VENV/bin/python3" -m playwright install chromium && \
      "$VENV/bin/python3" -m playwright install-deps chromium; } || \
      echo "WARNING: playwright chromium install failed; in-container weread cookie refresh will not work" >&2
RUN chmod +x /app/start.sh

EXPOSE 8001
CMD ["/app/start.sh"]

#!/usr/bin/env bash
set -euxo pipefail

dnf update -y
dnf install -y git python3.11 python3.11-pip

useradd --system --home-dir /opt/turbosearch --create-home turbosearch || true
mkdir -p /opt/turbosearch/vector-index
chown -R turbosearch:turbosearch /opt/turbosearch
cd /opt/turbosearch

git clone https://github.com/anishk123/turbosearch.git app
cd app

python3.11 -m venv .venv
. .venv/bin/activate
pip install -e '.[embeddings]'
pip install turbovec || true

cat >/etc/systemd/system/turbosearch.service <<SERVICE
[Unit]
Description=turbosearch API
After=network-online.target

[Service]
User=turbosearch
WorkingDirectory=/opt/turbosearch/app
Environment=DATABASE_URL=${database_url}
Environment=EMBEDDING_PROVIDER=qwen
Environment=EMBEDDING_MODEL=Qwen/Qwen3-Embedding-0.6B
Environment=EMBEDDING_DIM=1024
Environment=INDEX_DIM=256
Environment=INDEX_VERSION=1
Environment=VECTOR_INDEX_PATH=/opt/turbosearch/vector-index/vectors.json
Environment=OVERVIEW_MODE=llm
Environment=LLM_BASE_URL=${llm_base_url}
Environment=LLM_API_KEY=${llm_api_key}
Environment=LLM_MODEL=${llm_model}
ExecStart=/opt/turbosearch/app/.venv/bin/turbosearch serve --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable turbosearch
systemctl start turbosearch

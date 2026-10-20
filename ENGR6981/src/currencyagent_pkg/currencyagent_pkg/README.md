# CurrencyAgent: Docker + fault-injection UI + Kubernetes

Copy these files over your `currencyagent/` folder (same relative paths), then:

| File | What changed |
|---|---|
| `Dockerfile`, `.dockerignore` | New. No protoc step (stubs are in `app/clients/`). |
| `requirements.txt` | `grpcio>=1.80.0`, `protobuf>=6.31.1` (your stubs were generated with those; older runtimes refuse to load them). `grpcio-tools` removed (not needed at runtime). |
| `app/ui.py` | New. Same file as the email/ad agents. Adds /ui/modes, /ui/run, /ui/status, /ui/results. |
| `app/main.py` | Two added lines: import `ui` and `app.include_router(ui)`. |
| `app/graph.py` | `token_log.txt` is written under `RESULTS_DIR` and a write failure no longer breaks the request (the root filesystem is read-only in the pod). |
| `app/__init__.py` | New, empty. |
| `test_fault_injection.py` | Output goes to `RESULTS_DIR`, with a stdout fallback if the write fails. |
| `k8s/currencyagent.yaml` | New Deployment + Service named `currencyagent`. |
| `k8s/dashboard.yaml` | Same dashboard manifest with `"currency": "http://currencyagent:8080"` added to `AGENTS`. |

## Build, deploy

```bash
cd currencyagent
sudo docker build -t ghcr.io/pauriccarr/engr-currency-agent:latest .
sudo docker run --rm ghcr.io/pauriccarr/engr-currency-agent:latest python -c "import app.main; print('ok')"
sudo docker push ghcr.io/pauriccarr/engr-currency-agent:latest
kubectl apply -f k8s/currencyagent.yaml
kubectl rollout status deployment/currencyagent
kubectl apply -f k8s/dashboard.yaml
kubectl rollout restart deployment/faultlab-dashboard
```

Run from the command line without the dashboard:

```bash
kubectl exec deploy/currencyagent -- python /srv/test_fault_injection.py
```

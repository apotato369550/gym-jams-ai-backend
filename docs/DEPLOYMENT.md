# Deployment Quickstart

Deploy `gym-jams-ai-backend` to an Amazon Linux 2023 EC2 instance with one command from your laptop.

## Architecture

```
   Internet
      |
      v
  [ EC2 :80 ]    nginx (reverse proxy, HTTP only)
      |
      v
  [ :8000 ]      uvicorn under systemd  (gym-jams.service)
      |
      v
  [ :3306 ]      MySQL 8.0 in Docker    (gym-jams-db)
```

## Prerequisites

1. **EC2 instance** running. Recommended: `t3.micro`, Amazon Linux 2023, `ap-northeast-1a`.
2. **Security group** allows:
   - TCP `22` from your IP (SSH)
   - TCP `80` from `0.0.0.0/0` (HTTP)
3. **`.pem` key** downloaded. On macOS / Linux / WSL: `chmod 400 ~/keys/gym-jams.pem`. On native Windows Git Bash, the chmod is best-effort — that's fine.
4. **Local tools**: `bash`, `ssh`, `scp`, `rsync`, `curl`. Git Bash + rsync (`pacman -S rsync` in MSYS2) works. WSL is easiest.
5. **Local `.env`** — fill in the project root `.env` with real values. The deploy script will copy it to the server. Required vars listed in `CLAUDE.md`. `JWT_SECRET` **must** be set to a long random string (e.g. `openssl rand -hex 32`).

## First-time deploy

From the project root:

```bash
EC2_HOST=ec2-1-2-3-4.ap-northeast-1.compute.amazonaws.com \
PEM_PATH=~/keys/gym-jams.pem \
bash deploy/deploy.sh
```

The script is verbose (`set -x`) and tees everything to `deploy.log`. Re-running is safe — it's idempotent.

Phases:

| # | Phase            | What it does                                                                |
|---|------------------|-----------------------------------------------------------------------------|
| 0 | Preflight        | Checks `.pem` and `.env` exist, verifies SSH works                          |
| 1 | Sync             | `rsync` your code to `/home/ec2-user/gym-jams-ai-backend`                   |
| 2 | Env              | `scp` your `.env`, force `DB_HOST=127.0.0.1`                                |
| 3 | Provision        | `dnf install` Python/nginx/Docker, run MySQL container, venv + deps, init DB, install systemd unit, install nginx config |
| 4 | Smoke test       | `curl http://$EC2_HOST/health`                                              |

Smoke success looks like: `{"service":"alive"}`.

## Redeploying a code change

```bash
SKIP_DB_INIT=1 \
EC2_HOST=ec2-1-2-3-4.ap-northeast-1.compute.amazonaws.com \
PEM_PATH=~/keys/gym-jams.pem \
bash deploy/deploy.sh
```

`SKIP_DB_INIT=1` keeps your existing rows. Without it, **the deploy will drop and recreate all tables.** Use the unset form only on first deploy or when you've changed the schema.

## Day-2 ops

```bash
# Tail the FastAPI service log
ssh -i $PEM_PATH ec2-user@$EC2_HOST 'sudo journalctl -u gym-jams -f'

# Service status
ssh -i $PEM_PATH ec2-user@$EC2_HOST 'sudo systemctl status gym-jams'

# Restart the app (after a manual edit on the box, for example)
ssh -i $PEM_PATH ec2-user@$EC2_HOST 'sudo systemctl restart gym-jams'

# nginx logs
ssh -i $PEM_PATH ec2-user@$EC2_HOST 'sudo tail -f /var/log/nginx/access.log /var/log/nginx/error.log'

# MySQL shell
ssh -i $PEM_PATH ec2-user@$EC2_HOST 'sudo docker exec -it gym-jams-db mysql -uroot -proot gym_jams_db'

# MySQL container logs
ssh -i $PEM_PATH ec2-user@$EC2_HOST 'sudo docker logs --tail 100 gym-jams-db'
```

## Troubleshooting

| Symptom                                  | Likely cause                                      | Fix                                                                                  |
|------------------------------------------|---------------------------------------------------|--------------------------------------------------------------------------------------|
| `502 Bad Gateway` from nginx             | uvicorn isn't running                             | `sudo systemctl status gym-jams`; check `journalctl -u gym-jams -n 200`              |
| `Database unavailable. Running without Database` in logs | MySQL container not up yet, or `.env` wrong       | `sudo docker ps`; `sudo docker logs gym-jams-db`                                     |
| Login returns 401 with valid creds       | `JWT_SECRET` mismatch between deploys             | Set a stable `JWT_SECRET` in `.env`, redeploy                                        |
| AI endpoints time out                    | OpenRouter slow or `OPENROUTER_API_KEY` invalid   | Check `journalctl -u gym-jams`; nginx already has 120s read timeout                  |
| `Permission denied (publickey)`          | Wrong `PEM_PATH` or wrong username                | AL2023 user is `ec2-user` (not `ubuntu`). Confirm key is the one tied to the instance|
| `rsync: command not found` locally       | Git Bash without rsync                            | Use WSL, or install via MSYS2 pacman                                                 |

## Security caveats — read before showing this to anyone

This deployment is MVP/POC quality. Before letting real users hit it:

- [ ] Add HTTPS. Easiest path: point a domain at the instance, run `certbot --nginx`. Or front it with CloudFront / an ALB.
- [ ] Change MySQL `root` password (currently literally `root`). Move it into `.env` and rotate.
- [ ] Set a strong, **non-default** `JWT_SECRET`. The codebase falls back to `"changeme"` if unset — that is unsafe.
- [ ] Restrict SSH to your IP only.
- [ ] Don't expose port 3306 publicly. The deploy maps it to `0.0.0.0:3306` for simplicity; bind to `127.0.0.1:3306` for production.
- [ ] Enable backups (RDS snapshots or `mysqldump` cron) before you have data worth keeping.
- [ ] Move secrets out of `.env` into AWS Secrets Manager or SSM Parameter Store.

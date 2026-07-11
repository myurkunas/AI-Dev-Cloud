# Deploying the prototype to AWS Academy Learner Lab (EC2)

A ready-to-run guide for hosting the Heinz Admissions Assistant on a single EC2
instance. **This has not been executed yet** — run it only when you need a live
demo, because Learner Lab is ephemeral (see "Important realities" below).

Estimated time: ~10 minutes. No local AWS CLI needed — this is all in the console.

## Important realities of Learner Lab (read first)

- The lab runs in **~4-hour sessions** and auto-stops. When it stops, your EC2
  instance is **stopped, not deleted** — data survives, but the app is
  unreachable until you start the lab and the instance again.
- On restart the instance gets a **new public IP**, so the old URL stops working.
- Running instances **consume your limited credit budget** — stop or terminate
  when you're done.
- You **cannot create IAM roles**; use the pre-provisioned **`LabRole`** if a
  role is ever required. This app needs no AWS permissions, so it's optional.
- Region is typically pinned to **us-east-1**.

**Recommended flow:** launch → verify → screenshot/record as evidence → stop the
lab. Don't leave it running.

## Steps

1. **Start the lab.** In AWS Academy, click **Start Lab**, wait for the green
   dot, then click **AWS** to open the console.

2. **Launch an instance.** EC2 → **Launch instances**:
   - **Name:** `heinz-assistant`
   - **AMI:** Amazon Linux 2023
   - **Instance type:** `t2.micro` (or `t3.micro`)
   - **Key pair:** optional — create one only if you want SSH access to debug.
   - **Network settings → Edit → Security group:** add an inbound rule:
     - Type **HTTP**, Port **80**, Source **Anywhere (0.0.0.0/0)**.
     - (For a class demo this is fine; to be stricter, set Source to *My IP*.)
   - **Advanced details → User data:** paste the entire contents of
     [`ec2-user-data.sh`](./ec2-user-data.sh).
   - Leave the IAM instance profile empty (or `LabInstanceProfile` if shown — not required).
   - **Launch instance.**

3. **Wait ~3–4 minutes** for first boot (it installs Python, clones the repo,
   installs dependencies, and starts the service).

4. **Verify.** Copy the instance's **Public IPv4 address**, then:
   - Browser: `http://<PUBLIC_IP>/` → the ask form.
   - Health: `http://<PUBLIC_IP>/health` → `{"status":"ok","documents":6,...}`
   - API:
     ```bash
     curl -s -X POST http://<PUBLIC_IP>/ask \
       -H "Content-Type: application/json" \
       -d '{"question": "Is the GRE required for Heinz College programs?"}'
     ```

5. **Capture evidence** (screenshot or short recording of the form + a response
   with its source citation) for the TM1 submission.

6. **Tear down.** When finished:
   - EC2 → select the instance → **Instance state → Terminate** (removes it), or
     **Stop** (keeps it for next time; IP will change on restart).
   - Then **End Lab** in AWS Academy.

## Troubleshooting

- **Page won't load:** confirm the security group allows inbound **port 80**, and
  give it a few minutes — dependency install takes a bit on `t2.micro`.
- **Check the boot log** (needs a key pair + SSH): `sudo cat /var/log/cloud-init-output.log`
- **Check the service** (via SSH): `sudo systemctl status heinz-assistant`
- **Port 80 blocked by policy?** Change `--port 80` to `--port 8000` in the user
  data, open port **8000** in the security group, and use `http://<PUBLIC_IP>:8000/`.

## Enabling the Claude backend on the instance (optional)

The deployed app runs in stub mode by default. To use Claude, SSH in and add the
key to the service, then restart it:

```bash
sudo systemctl edit heinz-assistant
# add under [Service]:
#   Environment=ANTHROPIC_API_KEY=sk-ant-...
sudo systemctl restart heinz-assistant
```

Never bake the key into the repo or the user-data script.

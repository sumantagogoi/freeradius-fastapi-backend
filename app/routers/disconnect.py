import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from ..dependencies import get_current_user

router = APIRouter(prefix="/radius/disconnect", tags=["disconnect"], dependencies=[Depends(get_current_user)])


class DisconnectRequest(BaseModel):
    users: List[str]
    nases: List[str]                # "ip" or "ip:port" (port defaults to 3799)
    secret: str
    timeout_seconds: int = 5
    max_parallel: int = 50          # how many concurrent radclient calls


class DisconnectResult(BaseModel):
    user: str
    nas: str
    status: str                     # "ACK" | "NAK" | "timeout" | "error"
    detail: Optional[str] = None


def _run_radclient(user: str, nas: str, secret: str, timeout: int) -> DisconnectResult:
    """Send a single Disconnect-Request for one user to one NAS."""
    try:
        result = subprocess.run(
            ["docker", "exec", "-i", "freeradius2", "radclient", "-x", nas, "disconnect", secret],
            input=f"User-Name={user}\n".encode(),
            capture_output=True,
            timeout=timeout,
        )
        stdout = result.stdout.decode()
        stderr = result.stderr.decode()

        if "Disconnect-ACK" in stdout:
            return DisconnectResult(user=user, nas=nas, status="ACK", detail="Disconnected")
        elif "Disconnect-NAK" in stdout:
            for line in stdout.split("\n"):
                if "Reply-Message" in line:
                    return DisconnectResult(user=user, nas=nas, status="NAK", detail=line.strip())
            return DisconnectResult(user=user, nas=nas, status="NAK", detail="Session not found on NAS")
        else:
            return DisconnectResult(user=user, nas=nas, status="error", detail=(stderr or stdout).strip()[:200])
    except subprocess.TimeoutExpired:
        return DisconnectResult(user=user, nas=nas, status="timeout", detail="No response from NAS")
    except Exception as e:
        return DisconnectResult(user=user, nas=nas, status="error", detail=str(e)[:200])


def _normalize_nas(nas: str) -> str:
    if ":" in nas:
        return nas
    return f"{nas}:3799"


@router.post("", response_model=List[DisconnectResult])
def bulk_disconnect(body: DisconnectRequest):
    """Send Disconnect-Request for multiple users to multiple NASes in parallel.

    Sends one RADIUS Disconnect-Request packet per user per NAS.
    Each NAS ACKs the users it has connected and NAKs the rest.
    Results include per-user, per-NAS status.
    """
    if not body.users or not body.nases:
        raise HTTPException(status_code=400, detail="Must provide at least one user and one NAS")

    nases = [_normalize_nas(n) for n in body.nases]
    tasks = [(user, nas) for user in body.users for nas in nases]
    total = len(tasks)

    if total > body.max_parallel * 2:
        expected_secs = (total / body.max_parallel) * body.timeout_seconds
    else:
        expected_secs = body.timeout_seconds

    results: list[DisconnectResult] = []

    with ThreadPoolExecutor(max_workers=body.max_parallel) as pool:
        futures = {
            pool.submit(_run_radclient, user, nas, body.secret, body.timeout_seconds): (user, nas)
            for user, nas in tasks
        }
        for future in as_completed(futures):
            user, nas = futures[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                results.append(DisconnectResult(user=user, nas=nas, status="error", detail=str(e)[:200]))

    return results

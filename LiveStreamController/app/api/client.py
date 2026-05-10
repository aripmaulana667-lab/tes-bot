"""Thin HTTP client around the LiveStream Server API."""

from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, List, Optional

import requests


class APIError(Exception):
    def __init__(self, message: str, status_code: Optional[int] = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class APIClient:
    def __init__(self, base_url: str = "", token: str = "", timeout: int = 20) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout
        self.session = requests.Session()

    # ---- helpers ----------------------------------------------------

    def update_connection(self, base_url: str, token: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token

    def _headers(self, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.token:
            headers["X-API-Key"] = self.token
        if extra:
            headers.update(extra)
        return headers

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        if not self.base_url:
            raise APIError("URL server belum dikonfigurasi")
        url = f"{self.base_url}{path}"
        try:
            response = self.session.request(
                method,
                url,
                timeout=kwargs.pop("timeout", self.timeout),
                headers=self._headers(kwargs.pop("headers", None)),
                **kwargs,
            )
        except requests.RequestException as exc:
            raise APIError(f"koneksi gagal: {exc}") from exc

        if response.status_code == 204:
            return None
        if response.status_code >= 400:
            try:
                detail = response.json().get("detail", response.text)
            except ValueError:
                detail = response.text or response.reason
            raise APIError(f"{response.status_code}: {detail}", response.status_code)
        try:
            return response.json()
        except ValueError:
            return response.text

    # ---- auth ------------------------------------------------------

    def login(self, username: str, password: str) -> Dict[str, Any]:
        data = self._request("POST", "/auth/login", json={"username": username, "password": password})
        if isinstance(data, dict) and data.get("api_token"):
            self.token = data["api_token"]
        return data

    # ---- server ----------------------------------------------------

    def server_status(self) -> Dict[str, Any]:
        return self._request("GET", "/server/status")

    def check_ffmpeg(self) -> Dict[str, Any]:
        return self._request("GET", "/server/check-ffmpeg")

    def install_ffmpeg(self, force: bool = False) -> Dict[str, Any]:
        return self._request("POST", "/server/install-ffmpeg", params={"force": str(force).lower()})

    def check_deps(self) -> Dict[str, Any]:
        return self._request("GET", "/server/check-deps")

    def system_resources(self) -> Dict[str, Any]:
        return self._request("GET", "/system/resources")

    # ---- videos ----------------------------------------------------

    def list_videos(self) -> List[Dict[str, Any]]:
        return self._request("GET", "/videos")

    def upload_video(
        self,
        path: str,
        on_progress: Optional[Callable[[int, int], None]] = None,
    ) -> Dict[str, Any]:
        if not self.base_url:
            raise APIError("URL server belum dikonfigurasi")
        url = f"{self.base_url}/videos/upload"
        # We use a simple multipart upload; for very large files an HTTP/2 lib could be used.
        with open(path, "rb") as f:
            files = {"file": (path.split("/")[-1].split("\\")[-1], f, "application/octet-stream")}
            try:
                response = self.session.post(url, headers=self._headers(), files=files, timeout=None)
            except requests.RequestException as exc:
                raise APIError(f"upload gagal: {exc}") from exc
        if response.status_code >= 400:
            try:
                detail = response.json().get("detail", response.text)
            except ValueError:
                detail = response.text
            raise APIError(f"{response.status_code}: {detail}", response.status_code)
        return response.json()

    def delete_video(self, video_id: int) -> None:
        self._request("DELETE", f"/videos/{video_id}")

    def rename_video(self, video_id: int, new_name: str) -> Dict[str, Any]:
        return self._request("PATCH", f"/videos/{video_id}/rename", json={"new_name": new_name})

    # ---- accounts --------------------------------------------------

    def list_accounts(self) -> List[Dict[str, Any]]:
        return self._request("GET", "/accounts")

    def create_account(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/accounts", json=payload)

    def update_account(self, account_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("PATCH", f"/accounts/{account_id}", json=payload)

    def delete_account(self, account_id: int) -> None:
        self._request("DELETE", f"/accounts/{account_id}")

    # ---- streams ---------------------------------------------------

    def list_streams(self) -> List[Dict[str, Any]]:
        return self._request("GET", "/streams")

    def get_stream(self, stream_id: int) -> Dict[str, Any]:
        return self._request("GET", f"/streams/{stream_id}")

    def start_stream(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/streams/start", json=payload)

    def stop_stream(self, stream_id: int) -> Dict[str, Any]:
        return self._request("POST", f"/streams/stop/{stream_id}")

    def restart_stream(self, stream_id: int) -> Dict[str, Any]:
        return self._request("POST", f"/streams/restart/{stream_id}")

    def stream_logs(self, stream_id: int, limit: int = 200) -> Dict[str, Any]:
        return self._request("GET", f"/streams/logs/{stream_id}", params={"limit": limit})

    # ---- bulk helpers ---------------------------------------------

    def start_streams(self, payloads: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for payload in payloads:
            results.append(self.start_stream(payload))
        return results

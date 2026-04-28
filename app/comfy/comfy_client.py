import asyncio
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx
import websockets

from app.config import settings


StatusCallback = Callable[[str, dict[str, Any] | None], None]


class ComfyClient:
    def __init__(self) -> None:
        self.base_url = settings.comfy_base_url
        self.timeout = settings.request_timeout

    @staticmethod
    def _response_preview(response: httpx.Response) -> str:
        try:
            data = response.json()
            return json.dumps(data, ensure_ascii=False)[:1000]
        except Exception:
            return response.text[:1000]

    async def _request_json(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> Any:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(method, url, **kwargs)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            body = self._response_preview(exc.response)
            raise RuntimeError(
                f"ComfyUI API error {exc.response.status_code} for {method} {url}: {body}"
            ) from exc
        except httpx.RequestError as exc:
            raise RuntimeError(
                f"ComfyUI connection error for {method} {url}: {exc}"
            ) from exc

    async def load_workflow(self, workflow_path: str | Path) -> dict[str, Any]:
        path = Path(workflow_path)
        if not path.exists():
            raise FileNotFoundError(f"Workflow file not found: {path}")
        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Workflow JSON is invalid: {path}") from exc
        if not isinstance(data, dict):
            raise ValueError(f"Workflow file must contain a JSON object: {path}")
        return data

    async def get_models_in_folder(self, folder: str) -> list[str]:
        url = f"{self.base_url}/models/{folder}"
        data = await self._request_json("GET", url)

        if not isinstance(data, list):
            raise RuntimeError(
                f"Unexpected models response for folder={folder}: {data}"
            )

        return [str(item) for item in data]

    async def fetch_image(
        self,
        filename: str,
        subfolder: str,
        type: str,
    ) -> dict[str, Any]:
        params = {
            "filename": filename,
            "subfolder": subfolder,
            "type": type,
        }
        url = f"{self.base_url}/view"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()

                content_type = response.headers.get("content-type", "")
                if "image/png" not in content_type:
                    raise RuntimeError(
                        f"Unexpected content-type for image: {content_type}"
                    )

                content_length = len(response.content)
                if content_length == 0:
                    raise RuntimeError("Image body is empty")

                return {
                    "status_code": response.status_code,
                    "content_type": content_type,
                    "content_length": content_length,
                    "content": response.content,
                }
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"Failed to fetch image: HTTP {exc.response.status_code}"
            ) from exc
        except httpx.RequestError as exc:
            raise RuntimeError(
                f"Failed to fetch image: connection error"
            ) from exc

    async def queue_prompt(self, workflow: dict[str, Any]) -> str:
        url = f"{self.base_url}/prompt"
        payload = {"prompt": workflow}
        data = await self._request_json("POST", url, json=payload)
        prompt_id = data.get("prompt_id")
        if not prompt_id:
            raise RuntimeError(f"prompt_id not found in response: {data}")
        return prompt_id

    async def get_queue(self) -> dict[str, Any]:
        url = f"{self.base_url}/queue"
        data = await self._request_json("GET", url)
        if not isinstance(data, dict):
            raise RuntimeError(f"Unexpected queue response: {data}")
        return data

    async def upload_image(
        self,
        image_path: str | Path,
        overwrite: bool = True,
    ) -> dict[str, Any]:
        """Upload an image to ComfyUI.

        Args:
            image_path: Path to the image file
            overwrite: Whether to overwrite existing file

        Returns:
            Dictionary with upload result including filename
        """
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image file not found: {path}")

        url = f"{self.base_url}/upload/image"
        files = {"image": (path.name, path.open("rb"), "image/png")}
        data = {"overwrite": str(overwrite).lower()}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, files=files, data=data)
                response.raise_for_status()
                result = response.json()
                if not isinstance(result, dict):
                    raise RuntimeError(f"Unexpected upload response: {result}")
                return result
        except httpx.HTTPStatusError as exc:
            body = self._response_preview(exc.response)
            raise RuntimeError(
                f"Image upload failed HTTP {exc.response.status_code}: {body}"
            ) from exc
        except httpx.RequestError as exc:
            raise RuntimeError(
                f"Image upload connection error: {exc}"
            ) from exc

    async def upload_mask(
        self,
        mask_path: str | Path,
        overwrite: bool = True,
    ) -> dict[str, Any]:
        """Upload a mask image to ComfyUI.

        Args:
            mask_path: Path to the mask image file
            overwrite: Whether to overwrite existing file

        Returns:
            Dictionary with upload result including filename
        """
        path = Path(mask_path)
        if not path.exists():
            raise FileNotFoundError(f"Mask file not found: {path}")

        url = f"{self.base_url}/upload/mask"
        files = {"mask": (path.name, path.open("rb"), "image/png")}
        data = {"overwrite": str(overwrite).lower()}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, files=files, data=data)
                response.raise_for_status()
                result = response.json()
                if not isinstance(result, dict):
                    raise RuntimeError(f"Unexpected mask upload response: {result}")
                return result
        except httpx.HTTPStatusError as exc:
            body = self._response_preview(exc.response)
            raise RuntimeError(
                f"Mask upload failed HTTP {exc.response.status_code}: {body}"
            ) from exc
        except httpx.RequestError as exc:
            raise RuntimeError(
                f"Mask upload connection error: {exc}"
            ) from exc

    async def save_workflow_to_userdata(
        self,
        workflow: dict[str, Any],
        filename: str,
        subfolder: str = "",
        overwrite: bool = True,
    ) -> dict[str, Any]:
        """Save a workflow to ComfyUI's userdata directory for canvas sync.

        This saves the workflow JSON to ComfyUI's storage, making it available
        in the UI's workflow dropdown. The UI can then load it to update the canvas.

        Args:
            workflow: Workflow dictionary (API format)
            filename: Name for the saved workflow file
            subfolder: Subfolder in userdata (default: empty for root)
            overwrite: Whether to overwrite existing file

        Returns:
            Dictionary with save result
        """
        import io
        url = f"{self.base_url}/upload/image"
        
        # Convert workflow dict to JSON bytes
        workflow_json = json.dumps(workflow, indent=2)
        workflow_bytes = workflow_json.encode('utf-8')
        workflow_file = io.BytesIO(workflow_bytes)
        
        files = {"image": (filename, workflow_file, "application/json")}
        data = {
            "overwrite": str(overwrite).lower(),
            "subfolder": subfolder,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, files=files, data=data)
                response.raise_for_status()
                result = response.json()
                if not isinstance(result, dict):
                    raise RuntimeError(f"Unexpected workflow save response: {result}")
                return result
        except httpx.HTTPStatusError as exc:
            body = self._response_preview(exc.response)
            raise RuntimeError(
                f"Workflow save failed HTTP {exc.response.status_code}: {body}"
            ) from exc
        except httpx.RequestError as exc:
            raise RuntimeError(
                f"Workflow save connection error: {exc}"
            ) from exc

    async def sync_workflow_to_canvas(
        self,
        workflow: dict[str, Any],
        workflow_id: str,
    ) -> dict[str, Any]:
        """Sync workflow to ComfyUI canvas state.

        This saves the mutated workflow to ComfyUI's workflows directory on the filesystem,
        making it available in the UI's workflow dropdown for loading.

        Args:
            workflow: Mutated workflow dictionary (API format)
            workflow_id: Workflow ID for filename

        Returns:
            Dictionary with sync result including saved file path
        """
        import time
        from pathlib import Path
        
        timestamp = int(time.time())
        filename = f"{workflow_id}_sync_{timestamp}.json"
        
        print(f"\n[CANVAS_SYNC] Syncing workflow to canvas...")
        print(f"[CANVAS_SYNC] Workflow ID: {workflow_id}")
        print(f"[CANVAS_SYNC] Filename: {filename}")
        print(f"[CANVAS_SYNC] Node count: {len(workflow)}")
        
        # Save workflow to ComfyUI workflows directory on filesystem
        # ComfyUI watches this directory for workflow files
        comfy_dir = Path(__file__).resolve().parents[4] / "ComfyUI" / "user" / "default" / "workflows"
        comfy_dir.mkdir(parents=True, exist_ok=True)
        
        workflow_path = comfy_dir / filename
        with open(workflow_path, "w", encoding="utf-8") as f:
            json.dump(workflow, f, indent=2)
        
        print(f"[CANVAS_SYNC] ✓ Workflow saved to ComfyUI workflows directory")
        print(f"[CANVAS_SYNC] File: {workflow_path}")
        print(f"[CANVAS_SYNC] Available in ComfyUI workflow dropdown")
        
        return {
            "synced": True,
            "filename": filename,
            "path": str(workflow_path),
        }

    async def get_history(self, prompt_id: str) -> dict[str, Any]:
        url = f"{self.base_url}/history/{prompt_id}"
        data = await self._request_json("GET", url)
        if not isinstance(data, dict):
            raise RuntimeError(f"Unexpected history response for prompt_id={prompt_id}: {data}")
        return data

    @staticmethod
    def _is_prompt_running(queue_data: dict[str, Any], prompt_id: str) -> bool:
        return any(
            len(item) > 1 and item[1] == prompt_id
            for item in queue_data.get("queue_running", [])
        )

    @staticmethod
    def _is_prompt_pending(queue_data: dict[str, Any], prompt_id: str) -> bool:
        return any(
            len(item) > 1 and item[1] == prompt_id
            for item in queue_data.get("queue_pending", [])
        )

    @staticmethod
    def extract_execution_error(history_item: dict[str, Any]) -> str | None:
        status = history_item.get("status", {})
        messages = status.get("messages", [])
        if not isinstance(messages, list):
            return None
        for item in messages:
            if not isinstance(item, list) or len(item) != 2:
                continue
            event_name, payload = item
            if event_name not in {"execution_error", "execution_interrupted"}:
                continue
            if isinstance(payload, dict):
                exception_message = payload.get("exception_message")
                node_id = payload.get("node_id")
                node_type = payload.get("node_type")
                parts: list[str] = []
                if exception_message:
                    parts.append(str(exception_message))
                if node_id is not None:
                    parts.append(f"node_id={node_id}")
                if node_type:
                    parts.append(f"node_type={node_type}")
                if parts:
                    return " | ".join(parts)
                return json.dumps(payload, ensure_ascii=False)
            return str(payload)
        return None

    async def wait_for_history(
        self,
        prompt_id: str,
        max_attempts: int = 180,
        delay_seconds: int = 3,
        status_callback: StatusCallback | None = None,
    ) -> dict[str, Any]:
        running_reported = False
        last_running = False
        last_pending = False
        for attempt in range(1, max_attempts + 1):
            history = await self.get_history(prompt_id)
            if prompt_id in history:
                history_item = history[prompt_id]
                status = history_item.get("status", {})
                status_str = status.get("status_str")
                error_message = self.extract_execution_error(history_item)
                if error_message or status_str not in (None, "success"):
                    detail = error_message or f"status_str={status_str}"
                    raise RuntimeError(
                        f"ComfyUI execution failed for prompt_id={prompt_id}: {detail}"
                    )
                return history_item
            queue_data = await self.get_queue()
            last_running = self._is_prompt_running(queue_data, prompt_id)
            last_pending = self._is_prompt_pending(queue_data, prompt_id)
            if status_callback and last_running and not running_reported:
                status_callback(
                    "RUNNING",
                    {
                        "prompt_id": prompt_id,
                        "attempt": attempt,
                    },
                )
                running_reported = True
            await asyncio.sleep(delay_seconds)
        raise RuntimeError(
            "History for prompt_id="
            f"{prompt_id} not found after {max_attempts} attempts. "
            f"Last queue state: running={last_running}, pending={last_pending}."
        )

    @staticmethod
    def extract_images(history_item: dict[str, Any]) -> list[dict[str, Any]]:
        images_found: list[dict[str, Any]] = []
        outputs = history_item.get("outputs", {})
        if not isinstance(outputs, dict):
            return images_found
        for node_id, node_data in outputs.items():
            images = node_data.get("images", [])
            for image in images:
                images_found.append(
                    {
                        "node_id": node_id,
                        "filename": image.get("filename"),
                        "subfolder": image.get("subfolder"),
                        "type": image.get("type"),
                    }
                )
        return images_found

    async def watch_progress_websocket(
        self,
        prompt_id: str,
        status_callback: StatusCallback | None = None,
    ) -> dict[str, Any]:
        """Watch workflow progress via WebSocket.

        Args:
            prompt_id: Prompt ID to watch
            status_callback: Optional callback for status updates

        Returns:
            History item when execution completes
        """
        ws_url = settings.comfy_ws_url.replace("http://", "ws://").replace("https://", "wss://")

        try:
            async with websockets.connect(ws_url) as websocket:
                if status_callback:
                    status_callback("QUEUED", {"prompt_id": prompt_id})

                while True:
                    message = await websocket.recv()
                    data = json.loads(message)

                    # Check if this message is for our prompt_id
                    if data.get("type") == "executing":
                        current_prompt_id = data.get("data", {}).get("prompt_id")
                        if current_prompt_id == prompt_id:
                            if status_callback:
                                status_callback("RUNNING", {"prompt_id": prompt_id})

                    # Check for execution success
                    if data.get("type") == "execution_success":
                        success_prompt_id = data.get("data", {}).get("prompt_id")
                        if success_prompt_id == prompt_id:
                            # Fetch history to get full results
                            history = await self.get_history(prompt_id)
                            if prompt_id in history:
                                history_item = history[prompt_id]
                                if status_callback:
                                    status_callback(
                                        "COMPLETED",
                                        {"prompt_id": prompt_id, "images_found": len(self.extract_images(history_item))},
                                    )
                                return history_item

                    # Check for execution error
                    if data.get("type") == "execution_error":
                        error_prompt_id = data.get("data", {}).get("prompt_id")
                        if error_prompt_id == prompt_id:
                            error_msg = data.get("data", {}).get("exception_message", "Unknown error")
                            raise RuntimeError(f"ComfyUI execution error for prompt_id={prompt_id}: {error_msg}")

        except websockets.exceptions.WebSocketException as exc:
            # Fallback to polling if WebSocket fails
            if status_callback:
                status_callback("RETRYING", {"prompt_id": prompt_id, "reason": "WebSocket failed, falling back to polling"})
            return await self.wait_for_history(prompt_id, status_callback=status_callback)

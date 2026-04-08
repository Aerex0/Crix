"""Wake word detection module for Crix."""

from livekit.wakeword import WakeWordModel, WakeWordListener

import asyncio
from dataclasses import dataclass


@dataclass
class WakeWordDetection:
    name: str
    confidence: float


class WakeWordDetector:
    """Async wake word detector using livekit-wakeword."""

    def __init__(
        self,
        model_path: str,
        threshold: float = 0.5,
        debounce: float = 2.0,
    ):
        self.model_path = model_path
        self.threshold = threshold
        self.debounce = debounce
        self._model = None
        self._listener: WakeWordListener | None = None

    def _get_model(self) -> WakeWordModel:
        if self._model is None:
            self._model = WakeWordModel(models=[self.model_path])
        return self._model

    async def wait_for_wake_word(self) -> WakeWordDetection:
        """Block until wake word is detected. Returns detection info."""
        model = self._get_model()

        async with WakeWordListener(
            model,
            threshold=self.threshold,
            debounce=self.debounce,
        ) as listener:
            self._listener = listener
            detection = await listener.wait_for_detection()
            self._listener = None

            return WakeWordDetection(
                name=detection.name,
                confidence=detection.confidence,
            )

    async def close(self):
        """Close the detector and release resources."""
        if self._listener:
            await self._listener.aclose()
            self._listener = None

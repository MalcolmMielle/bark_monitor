import abc
from enum import Enum

from bark_monitor.recorders.base_recorder import BaseRecorder


class VeryBarkBot(abc.ABC):
    class Commands(Enum):
        help = "Display a help message"
        activity = "Display the day activity of the pets"
        start = "Start the recorder"
        stop = "Stop the recorder"
        pause = "Pause the recorder"
        unpause = "Unpause the recorder"
        bark_level = (
            "If using amplitude base recording, show the threshold to detect a bark"
        )
        register = "Register a new user"
        status = "Status of the recorder"
        login = "Log in to google drive"
        audio = (
            "Send an audio file based on file name. If used without a file name, it "
            + "will list the available files"
        )

        last = "Download last recording"

        @staticmethod
        def help_message() -> str:
            msg = ""
            for e in VeryBarkBot.Commands:
                msg += e.name + " - " + e.value + "\n"
            return msg

    _recorder: BaseRecorder

    def start(self, recorder: BaseRecorder) -> None:
        self._recorder = recorder

    def _stop_recorder_sync(self) -> None:
        if self._recorder.running is True:
            self._recorder.stop()

    @abc.abstractmethod
    def send_text(self, text: str) -> None:
        raise NotImplementedError("send_text not implemented")

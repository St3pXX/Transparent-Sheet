from .base import ConfirmationChannel
from .streamlit import StreamlitChannel


class ConfirmationChannelFactory:
    _channels = {
        "streamlit": StreamlitChannel,
    }

    @staticmethod
    def create(channel_type: str, **kwargs) -> ConfirmationChannel:
        if channel_type == "feishu":
            from .feishu_card import FeishuCardChannel
            return FeishuCardChannel(**kwargs)
        if channel_type not in ConfirmationChannelFactory._channels:
            raise ValueError(f"Unknown channel: {channel_type}")
        return ConfirmationChannelFactory._channels[channel_type]()
import json
import os

from chatgpt_tool_hub.apps import load_app
from chatgpt_tool_hub.apps.app import App

import plugins
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
from config import conf
from plugins import *


@plugins.register(name="tool", desc="Arming your ChatGPT bot with various tools", version="0.1", author="goldfishh", desire_priority=0)
class Tool(Plugin):
    def __init__(self):
        super().__init__()
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        os.environ["OPENAI_API_KEY"] = conf().get("open_ai_api_key", "")
        os.environ["PROXY"] = conf().get("proxy", "")

        self.app = self._reset_app()

        logger.info("[tool] inited")

    def get_help_text(self, **kwargs):
        help_text = "这是一个能让chatgpt联网，搜索，数字运算的插件，将赋予强大且丰富的扩展能力"
        return help_text

    def on_handle_context(self, e_context: EventContext):
        if e_context['context'].type != ContextType.TEXT:
            return

        content = e_context['context'].content
        content_list = e_context['context'].content.split(maxsplit=1)

        if not content or len(content_list) < 1:
            e_context.action = EventAction.CONTINUE
            return

        logger.debug("[tool] on_handle_context. content: %s" % content)
        reply = Reply()
        reply.type = ReplyType.TEXT

        # todo: 有些工具必须要api-key，需要修改config文件，所以这里没有实现query增删tool的功能
        if content.startswith("$tool"):
            if len(content_list) == 1:
                logger.debug("[tool]: get help")
                reply.content = self.get_help_text()
                e_context['reply'] = reply
                e_context.action = EventAction.BREAK_PASS
                return
            elif len(content_list) > 1:
                if content_list[1].strip() == "reset":
                    logger.debug("[tool]: reset config")
                    self.app = self._reset_app()
                    reply.content = "重置工具成功"
                    e_context['reply'] = reply
                    e_context.action = EventAction.BREAK_PASS
                    return
                elif content_list[1].startswith("reset"):
                    logger.debug("[tool]: remind")
                    reply.content = "你随机挑一个方式，提醒用户如果想重置tool插件，reset之后不要加任何字符"
                    e_context['reply'] = reply
                    e_context.action = EventAction.BREAK
                    return
                logger.debug("[tool]: just-go")

                # chatgpt-tool-hub will reply you with many tools
                # todo: I don't know how to pass someone session into this ask method yet
                reply.content = self.app.ask(content_list[1])
                e_context['reply'] = reply
                e_context.action = EventAction.BREAK_PASS
        return

    def _read_json(self) -> dict:
        curdir = os.path.dirname(__file__)
        config_path = os.path.join(curdir, "config.json")
        tool_config = {
            "tools": [],
            "kwargs": {}
        }
        if not os.path.exists(config_path):
            return tool_config
        else:
            with open(config_path, "r") as f:
                tool_config = json.load(f)
        return tool_config

    def _reset_app(self) -> App:
        tool_config = self._read_json()
        return load_app(tools_list=tool_config.get("tools"), **tool_config.get("kwargs"))

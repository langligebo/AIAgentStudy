"""协议与课程流程的离线回归测试；不会连接真实模型。"""

import io
import json
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from common import llm
from week_02.session_01 import main as lesson
from week_02.session_01.probes import EXPECTED_ORDER, ORDER_SCHEMA


def encoded(value):
    return json.dumps(value, ensure_ascii=False).encode("utf-8")


def reply(text="你好", **extra):
    return {"message": {"role": "assistant", "content": text}, "done": True, "done_reason": "stop", **extra}


class ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.client = llm.OllamaClient("http://example.test:11434/", "test-model", 15)
        self.messages = [{"role": "system", "content": "规则"}, {"role": "user", "content": "你好"}]

    def test_generate_contract_is_preserved(self):
        result = {"response": "回答", "done": True, "done_reason": "stop", "eval_count": 2}
        with patch.object(llm, "urlopen", return_value=io.BytesIO(encoded(result))) as network:
            response = self.client.generate("提示", temperature=0, seed=42, top_k=40)
        request = network.call_args.args[0]
        self.assertTrue(request.full_url.endswith("/api/generate"))
        self.assertEqual(json.loads(request.data)["options"], {"temperature": 0, "seed": 42, "top_k": 40, "top_p": 0.9, "num_predict": 512})
        self.assertEqual(response, llm.LLMResponse("回答", "stop", 2))

    def test_chat_preserves_messages_and_maps_options(self):
        with patch.object(llm, "urlopen", return_value=io.BytesIO(encoded(reply(prompt_eval_count=8, eval_count=2)))) as network:
            response = self.client.chat(self.messages, response_schema=ORDER_SCHEMA, context_tokens=4096, max_tokens=64, seed=42)
        request = network.call_args.args[0]
        payload = json.loads(request.data)
        self.assertEqual(request.full_url, "http://example.test:11434/api/chat")
        self.assertEqual(payload["messages"], self.messages)
        self.assertEqual(payload["format"], ORDER_SCHEMA)
        self.assertEqual(payload["options"], {"temperature": 0, "num_ctx": 4096, "num_predict": 64, "seed": 42})
        self.assertIs(payload["stream"], False)
        self.assertEqual((response.input_tokens, response.output_tokens), (8, 2))
        self.assertEqual(network.call_args.kwargs["timeout"], 15)

    def test_tool_only_response_is_not_an_empty_answer_error(self):
        result = reply("")
        result["message"]["tool_calls"] = [{"function": {"name": "get_order", "arguments": {"order_id": "QX-731"}}}]
        with patch.object(llm, "urlopen", return_value=io.BytesIO(encoded(result))):
            response = self.client.chat(self.messages)
        self.assertEqual(response.tool_calls, (llm.ToolCall("get_order", {"order_id": "QX-731"}),))
        self.assertEqual(response.text, "")

    def test_stream_includes_final_piece_and_final_usage(self):
        chunks = [reply("你", done=False), reply("好", prompt_eval_count=8, eval_count=2)]
        pieces = []
        stream = io.BytesIO(b"\n".join(encoded(chunk) for chunk in chunks))
        with patch.object(llm, "urlopen", return_value=stream):
            response = self.client.chat(self.messages, on_text=pieces.append)
        self.assertEqual(pieces, ["你", "好"])
        self.assertEqual(response.text, "你好")
        self.assertEqual(response.output_tokens, 2)
        self.assertTrue(stream.closed)

    def test_stream_without_terminal_marker_never_returns_success(self):
        pieces = []
        with patch.object(llm, "urlopen", return_value=io.BytesIO(encoded(reply("完整文字", done=False)))):
            with self.assertRaisesRegex(RuntimeError, "done=true"):
                self.client.chat(self.messages, on_text=pieces.append)
        self.assertEqual(pieces, ["完整文字"])

    def test_display_callback_error_is_not_mislabeled_as_bad_json(self):
        def display(text):
            raise ValueError("显示回调错误")

        stream = io.BytesIO(encoded(reply()))
        with patch.object(llm, "urlopen", return_value=stream):
            with self.assertRaisesRegex(ValueError, "显示回调错误"):
                self.client.chat(self.messages, on_text=display)
        self.assertTrue(stream.closed)

    def test_invalid_responses_are_rejected(self):
        bad_values = [
            [], reply(done=False), reply(done="true"), reply(""),
            reply(message={"content": 1}), reply(error="服务端报错"),
            reply(message={"content": "", "tool_calls": [{"function": {"name": "get_order", "arguments": "{}"}}]}),
        ]
        for value in bad_values:
            with self.subTest(value=value), patch.object(llm, "urlopen", return_value=io.BytesIO(encoded(value))):
                with self.assertRaises(RuntimeError):
                    self.client.chat(self.messages)
        with patch.object(llm, "urlopen", return_value=io.BytesIO(b"not json")):
            with self.assertRaisesRegex(RuntimeError, "JSON"):
                self.client.chat(self.messages)

    def test_stream_server_error_is_not_silently_accepted(self):
        stream = io.BytesIO(encoded(reply("半句", done=False)) + b"\n" + encoded({"error": "推理失败"}))
        with patch.object(llm, "urlopen", return_value=stream):
            with self.assertRaisesRegex(RuntimeError, "推理失败"):
                self.client.chat(self.messages, on_text=lambda text: None)

    def test_empty_truncation_retains_reason_for_the_probe(self):
        with patch.object(llm, "urlopen", return_value=io.BytesIO(encoded(reply("", done_reason="length")))):
            response = self.client.chat(self.messages, max_tokens=1)
        self.assertEqual(response.finish_reason, "length")

    def test_unsupported_stream_tools_fails_before_network(self):
        with patch.object(llm, "urlopen") as network:
            with self.assertRaises(ValueError):
                self.client.chat(self.messages, tools=[{}], on_text=lambda text: None)
            network.assert_not_called()


class LessonTests(unittest.TestCase):
    def fake_response(self, request, timeout):
        payload = json.loads(request.data)
        self.calls.append(payload)
        if payload.get("tools"):
            if self.reject_tools:
                raise HTTPError(request.full_url, 400, "bad request", {}, io.BytesIO(b"model does not support tools"))
            result = reply("")
            result["message"]["tool_calls"] = [{"function": {"name": "get_order", "arguments": {"order_id": "QX-731"}}}]
        elif payload["options"]["num_predict"] == 1:
            result = reply("1", done_reason="length", eval_count=1)
        elif "format" in payload:
            result = reply(json.dumps(EXPECTED_ORDER, ensure_ascii=False))
        elif "学习助手" in payload["messages"][-1]["content"]:
            result = reply("学习助手")
        elif "请只回答：收到" in payload["messages"][-1]["content"]:
            result = reply("收到")
        else:
            has_history = any("我的订单号是" in m["content"] for m in payload["messages"])
            result = reply("QX-731" if has_history else "未提供")
        if payload["stream"]:
            text = result["message"]["content"]
            return io.BytesIO(encoded(reply(text[:10], done=False)) + b"\n" + encoded(reply(text[10:])))
        return io.BytesIO(encoded(result))

    def setUp(self):
        self.calls = []
        self.reject_tools = False

    def run_lesson(self, *args, network=None):
        out, err = io.StringIO(), io.StringIO()
        with (
            patch.object(sys, "argv", ["main.py", *args]),
            patch.object(llm, "urlopen", side_effect=network or self.fake_response) as mocked,
            patch.object(Path, "mkdir", side_effect=AssertionError("不能创建结果目录")),
            patch.object(Path, "write_text", side_effect=AssertionError("不能写结果文件")),
            redirect_stdout(out), redirect_stderr(err),
        ):
            code = lesson.main()
        return code, out.getvalue(), err.getvalue(), mocked.call_count

    def test_all_probes_pass_and_use_explicit_history(self):
        code, out, err, count = self.run_lesson()
        self.assertEqual((code, err, count), (0, "", 9))
        self.assertEqual(out.count("| 通过当前样本 |"), 6)
        self.assertEqual([m["role"] for m in self.calls[3]["messages"]], ["system", "user", "assistant", "user"])
        self.assertNotIn("QX-731", json.dumps(self.calls[4]["messages"]))

    def test_list_does_not_create_a_client(self):
        with patch.object(lesson, "create_llm_client") as factory:
            code, out, err, count = self.run_lesson("--list")
        self.assertEqual((code, err, count), (0, "", 0))
        factory.assert_not_called()
        self.assertIn("history", out)

    def test_rejected_tool_probe_continues_to_other_experiment(self):
        self.reject_tools = True
        code, out, err, count = self.run_lesson()
        self.assertEqual((code, count), (1, 9))
        self.assertIn("HTTP 400", err)
        self.assertIn("| 最小工具调用探针 | 调用或协议失败 |", out)
        self.assertIn("| 输出截断观察 | 通过当前样本 |", out)

    def test_connection_failure_stops_without_retry(self):
        code, out, err, count = self.run_lesson(network=URLError("refused"))
        self.assertEqual((code, count), (1, 1))
        self.assertIn("| 接口级结构化输出 | 未运行 |", out)
        self.assertIn("停止后续请求", err)

    def test_interruption_leaves_remaining_probes_unrun(self):
        code, out, err, count = self.run_lesson(network=KeyboardInterrupt())
        self.assertEqual((code, count), (130, 1))
        self.assertIn("| 中文指令与消息角色 | 用户中断 |", out)
        self.assertIn("| 接口级结构化输出 | 未运行 |", out)


if __name__ == "__main__":
    unittest.main()

"""教学样本：Few-shot 示例与用于比较的测试输入分开。"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Case:
    case_id: str
    message: str
    category: str | None

    @property
    def expected(self) -> dict:
        return {
            "category": self.category,
            "needs_clarification": self.category is None,
        }


# 只有这些示例及其答案会进入版本 C 的 Prompt。
FEW_SHOT_EXAMPLES = (
    Case("E01", "上周买的台灯想申请维修。", "售后"),
    Case("E02", "客服反复推卸责任，我非常不满，而且我要退货。", "投诉"),
    Case("E03", "有件事需要你帮忙。", None),
)

# 测试的预期答案只用于程序评分，不传给模型。
TEST_CASES = (
    Case("T01", "这款键盘支持蓝牙连接吗？", "咨询"),
    Case("T02", "你们的门店周日几点关门？", "咨询"),
    Case("T03", "我昨天买的鞋尺码不合适，想换大一码。", "售后"),
    Case("T04", "你们一直不回复消息，服务态度太差了！", "投诉"),
    Case("T05", "这次送错颜色让我很不满，我要求换货。", "投诉"),
    Case("T06", "帮我处理一下这个。", None),
)

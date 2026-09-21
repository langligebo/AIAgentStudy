"""教学数据划分；预期答案只用于评分，不进入模型消息。"""

from week_01.session_03.cases import Case, TEST_CASES

DATASET_VERSION = "week02-s03-v1"
# 这些样本已经在第一周被用于观察和调试，现在明确作为开发数据。
DEV_CASES = TEST_CASES
# 方案固定后再运行；一旦用结果指导修改，就不再是独立保留数据。
HOLDOUT_CASES = (
    Case("H01", "这个保温杯可以放进洗碗机清洗吗？", "咨询"),
    Case("H02", "会员积分会在什么时候过期？", "咨询"),
    Case("H03", "去年购买的电饭煲坏了，我想申请保修。", "售后"),
    Case("H04", "已经购买的课程我想申请退费，请帮我办理。", "售后"),
    Case("H05", "配送员擅自签收，你们必须给我一个交代！", "投诉"),
    Case("H06", "修了三次还是坏的，售后的敷衍让我非常不满！", "投诉"),
    Case("H07", "我需要帮助，但还没想好怎么描述。", None),
    Case("H08", "能处理吗？", None),
)
SPLITS = {"dev": DEV_CASES, "test": HOLDOUT_CASES}

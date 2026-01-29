"""
Dan Koe「AI 内容永动机」四步 Skills 服务。
正确顺序：拆解 → 想清楚 → 写一次 → 用到极致
"""
from typing import Any

from src.services.llm_service import get_llm_service


# --- Skill 1：爆款结构拆解器 ---
SKILL1_SYSTEM = """你是一个内容结构分析 Skill。
你的职责是"判断内容结构是否值得复用"，而不是优化内容。"""

SKILL1_TASK = """分析输入内容，并给出结构化判断。

RULES：
- 不改写、不润色原内容
- 不主观夸赞
- 信息不足请标注「未知」
- 判断基于结构与传播机制，而非个人喜好

OUTPUT（严格按以下结构）：
1）核心观点（一句话）
2）目标读者与使用场景
3）内容展开路径（编号列表）
4）注意力钩子（类型 + 原句）
5）情绪变化曲线（开头 / 中段 / 结尾）
6）论证方式（如：故事 / 对比 / 权威 / 反直觉）
7）可复用表达结构（3–5 个模板）
8）复用判断（是否值得复用 + 原因）"""


# --- Skill 2：写作前元思考澄清器 ---
SKILL2_SYSTEM = """你是一个写作前澄清 Skill。
你的任务不是生成内容，而是确保写作条件被完全明确。"""

SKILL2_TASK = """在任何写作开始前，向用户提出澄清问题。

RULES：
- 只问问题，不生成正文
- 必须一次性问完
- 问完后停止

OUTPUT：
Q1：目标读者是谁？
Q2：发布平台是什么？
Q3：读者此刻的真实痛点或欲望是什么？
Q4：这次内容的核心判断或结论是什么？
Q5：内容将基于哪些经验 / 案例 / 证据？
Q6：整体表达风格偏向哪一种？（理性 / 故事 / 情绪）"""


# --- Skill 3：母内容结构构建器 ---
SKILL3_SYSTEM = """你是一个母内容结构构建 Skill。
你只负责设计结构，不负责写全文。"""

SKILL3_TASK = """基于输入的核心观点，设计一篇可长期使用的母内容结构。

RULES：
- 不生成完整正文
- 必须解释每一部分存在的原因
- 明确区分人类判断与 AI 可辅助部分

OUTPUT：
A）一句话承诺（读完能获得什么）
B）开头钩子方案（3 个）
C）正文结构：
   1. 段落标题
      - 写这一段的目的
      - 核心要点
      - 标注：【人类判断 / AI 辅助】
D）CTA 设计（软 CTA / 硬 CTA）
E）后续可裂变方向（5 个）"""


# --- Skill 4：内容裂变与复利引擎 ---
SKILL4_SYSTEM = """你是一个内容裂变 Skill。
你的职责是保持观点一致，同时生成多样表达。"""

SKILL4_TASK = """将输入的母内容裂变为多种可分发内容。

RULES：
- 不新增核心观点
- 每条内容只表达一个点
- 表达方式必须不同

OUTPUT：
0）必要假设（如有）
1）短内容 × 20（100–200 字）
2）强钩子 × 5（一句话）
3）平台内容结构 × 3
4）视频脚本 × 1（含前 3 秒钩子 + 大字标题）
5）CTA 备选 × 5"""


def _call_llm(system: str, user_content: str, temperature: float = 0.3) -> str:
    llm = get_llm_service()
    resp = llm.client.chat.completions.create(
        model=llm.model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ],
        temperature=temperature,
    )
    return (resp.choices[0].message.content or "").strip()


def skill1_content_structure_judge(content: str) -> str:
    """Skill 1：爆款结构拆解器。输入任意内容，输出结构化判断。"""
    user = f"请分析以下内容：\n\n{content}"
    return _call_llm(SKILL1_SYSTEM, SKILL1_TASK + "\n\n---\n\n" + user)


def skill2_pre_writing_clarifier(writing_intent: str = "") -> str:
    """Skill 2：写作前元思考澄清器。输入模糊写作意图或留空，输出 6 个澄清问题。"""
    if writing_intent.strip():
        user = f"用户的写作意图或背景：\n{writing_intent}\n\n请根据上述信息，输出上述 6 个问题的完整版（可直接给用户填写）。"
    else:
        user = "用户尚未提供具体意图。请直接输出上述 6 个问题的完整版（留空让用户填写）。"
    return _call_llm(SKILL2_SYSTEM, SKILL2_TASK + "\n\n---\n\n" + user)


def skill3_mother_content_architect(core_idea: str) -> str:
    """Skill 3：母内容结构构建器。输入已验证的核心观点，输出母内容结构蓝图。"""
    user = f"核心观点（已验证）：\n{core_idea}"
    return _call_llm(SKILL3_SYSTEM, SKILL3_TASK + "\n\n---\n\n" + user)


def skill4_content_repurposing_engine(mother_content: str) -> str:
    """Skill 4：内容裂变与复利引擎。输入完整母内容，输出多平台、多形式内容集合。"""
    user = f"母内容全文：\n{mother_content}"
    return _call_llm(SKILL4_SYSTEM, SKILL4_TASK + "\n\n---\n\n" + user)


def run_skill(skill_id: int, **kwargs: Any) -> str:
    """统一入口：根据 skill_id 执行对应 Skill。"""
    if skill_id == 1:
        return skill1_content_structure_judge(kwargs.get("content", ""))
    if skill_id == 2:
        return skill2_pre_writing_clarifier(kwargs.get("writing_intent", ""))
    if skill_id == 3:
        return skill3_mother_content_architect(kwargs.get("core_idea", ""))
    if skill_id == 4:
        return skill4_content_repurposing_engine(kwargs.get("mother_content", ""))
    raise ValueError(f"Unknown skill_id: {skill_id}. Use 1-4.")

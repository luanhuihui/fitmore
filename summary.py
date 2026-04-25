import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


def _build_prompt(rows):
    lines = ["以下是用户最近 7 天的健身记录（按日期升序）：\n"]
    for r in rows:
        d, w, workout, diet, note, cal_burned, cal_intake = r
        parts = [f"日期：{d}"]
        if w:
            parts.append(f"体重 {w}kg")
        if workout:
            parts.append(f"训练：{workout}")
        if diet:
            parts.append(f"饮食：{diet}")
        if cal_burned:
            parts.append(f"消耗热量 {cal_burned:.0f}kcal")
        if cal_intake:
            parts.append(f"摄入热量 {cal_intake:.0f}kcal")
        if note:
            parts.append(f"备注：{note}")
        lines.append("- " + "，".join(parts))

    lines.append("""
请根据以上数据，用中文生成一份本周健身总结，包含以下几个部分：
1. 训练情况（频率、内容分析）
2. 体重变化（趋势分析）
3. 热量收支（消耗 vs 摄入，如有数据）
4. 饮食记录情况
5. 问题分析
6. 下周建议

语气专业但亲切，总结要具体，不要泛泛而谈。用 Markdown 格式输出。""")
    return "\n".join(lines)


def generate_summary(rows):
    if not rows:
        return "最近 7 天暂无记录，请先添加训练数据。"

    api_key = os.environ.get("DASHSCOPE_API_KEY", "")
    if not api_key:
        return "⚠️ 未检测到 DASHSCOPE_API_KEY 环境变量，请先设置后重试。\n\n```\nexport DASHSCOPE_API_KEY=your_key_here\n```"

    base_url = os.environ.get("LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    model    = os.environ.get("LLM_MODEL", "qwen-turbo")

    client = OpenAI(api_key=api_key, base_url=base_url)

    prompt = _build_prompt(rows)
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "你是一位专业的健身教练和营养师，擅长根据用户的训练和饮食数据给出个性化建议。"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
    )
    return resp.choices[0].message.content

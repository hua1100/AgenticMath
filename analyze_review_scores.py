#!/usr/bin/env python3
"""
分析 Review Agent 评分情况

检查评分是否过于宽松，以及是否需要调整质量门槛。
"""

import sqlite3
import json
from pathlib import Path

db_path = Path(__file__).parent / "test_results.db"

if not db_path.exists():
    print(f"❌ 数据库不存在：{db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("=" * 80)
print("📊 Review Agent 评分分析")
print("=" * 80)

# 获取所有 Review 记录
cursor.execute("""
    SELECT id, input_data, output_data, created_at
    FROM agent_executions
    WHERE agent_type = 'REVIEW'
    ORDER BY created_at DESC
""")

reviews = cursor.fetchall()

if not reviews:
    print("\n❌ 没有找到 Review Agent 记录")
    print("\n请先运行测试：python test_trigonometry_pipeline.py")
    conn.close()
    exit(1)

print(f"\n✅ 找到 {len(reviews)} 条 Review 记录")
print("\n" + "=" * 80)
print("📈 评分详情")
print("=" * 80)

scores = []
all_scores = {
    'clarity_grammar': [],
    'logical_coherence': [],
    'mathematical_validity': [],
    'overall': []
}

for idx, review in enumerate(reviews, 1):
    output_data = json.loads(review['output_data'])

    clarity = output_data.get('clarity_grammar_score', 0)
    coherence = output_data.get('logical_coherence_score', 0)
    validity = output_data.get('mathematical_validity_score', 0)
    overall = output_data.get('overall_score', 0)
    suggestions = output_data.get('suggestions', [])

    all_scores['clarity_grammar'].append(clarity)
    all_scores['logical_coherence'].append(coherence)
    all_scores['mathematical_validity'].append(validity)
    all_scores['overall'].append(overall)

    print(f"\n#{idx} - {review['created_at']}")
    print(f"   清晰度与语法: {clarity}/5")
    print(f"   逻辑连贯性:   {coherence}/5")
    print(f"   数学有效性:   {validity}/5")
    print(f"   ─────────────────────")
    print(f"   整体评分:     {overall:.2f}/5.0")

    # 检查质量门槛
    if overall >= 4.5:
        print(f"   ✅ 达标 (>= 4.5)")
    else:
        print(f"   ❌ 未达标 (< 4.5)")

    print(f"   改进建议数:   {len(suggestions)}")

    if suggestions:
        print(f"   建议概要:")
        for i, suggestion in enumerate(suggestions[:3], 1):  # 只显示前3条
            print(f"      {i}. {suggestion[:60]}...")

# 统计分析
print("\n" + "=" * 80)
print("📊 统计分析")
print("=" * 80)

def calc_stats(scores, name):
    if not scores:
        return
    avg = sum(scores) / len(scores)
    min_score = min(scores)
    max_score = max(scores)

    print(f"\n{name}:")
    print(f"   平均分: {avg:.2f}")
    print(f"   最低分: {min_score}")
    print(f"   最高分: {max_score}")

    # 分布
    score_dist = {}
    for score in scores:
        score_int = int(score) if isinstance(score, (int, float)) else 0
        score_dist[score_int] = score_dist.get(score_int, 0) + 1

    print(f"   分布:")
    for score in sorted(score_dist.keys(), reverse=True):
        count = score_dist[score]
        bar = '█' * count
        print(f"      {score} 分: {bar} ({count})")

calc_stats(all_scores['clarity_grammar'], "清晰度与语法")
calc_stats(all_scores['logical_coherence'], "逻辑连贯性")
calc_stats(all_scores['mathematical_validity'], "数学有效性")
calc_stats(all_scores['overall'], "整体评分")

# 质量门槛分析
print("\n" + "=" * 80)
print("🎯 质量门槛分析")
print("=" * 80)

current_threshold = 4.5
above_threshold = sum(1 for s in all_scores['overall'] if s >= current_threshold)
below_threshold = len(all_scores['overall']) - above_threshold

print(f"\n当前质量门槛: {current_threshold}")
print(f"   ✅ 达标: {above_threshold}/{len(reviews)} ({above_threshold/len(reviews)*100:.1f}%)")
print(f"   ❌ 未达标: {below_threshold}/{len(reviews)} ({below_threshold/len(reviews)*100:.1f}%)")

# 建议
print("\n" + "=" * 80)
print("💡 建议")
print("=" * 80)

if above_threshold == len(reviews):
    print("\n⚠️  所有问题都第一次就达标！")
    print("\n这可能表示：")
    print("   1. 评分标准过于宽松")
    print("   2. Rephrase Agent 生成的问题质量非常高")
    print("   3. 失去了迭代改进的机会")

    print("\n建议的调整方案：")
    print("\n方案 A：提高质量门槛")
    print("   修改 test_trigonometry_pipeline.py:")
    print("   quality_threshold=4.5 → quality_threshold=4.7 或 4.8")

    print("\n方案 B：调整 Review Agent 评分标准")
    print("   修改 src/prompts/review_prompt.py")
    print("   让评分更加严格，特别是对复杂度要求更高")

    print("\n方案 C：增加复杂度维度")
    print("   在 Review Agent 中增加第四个评分维度：")
    print("   - 复杂度与挑战性 (1-5)")
    print("   - 确保改写后的问题确实比原问题更复杂")

elif above_threshold / len(reviews) > 0.7:
    print("\n⚠️  70% 以上的问题第一次就达标")
    print(f"\n建议将质量门槛从 {current_threshold} 提高到 {current_threshold + 0.2:.1f}")

else:
    print("\n✅ 质量门槛设置合理！")
    print(f"\n{above_threshold/len(reviews)*100:.1f}% 的问题达标，")
    print("说明既有质量要求，又给了迭代改进的空间。")

# 检查建议质量
print("\n" + "=" * 80)
print("📝 改进建议质量检查")
print("=" * 80)

reviews_with_suggestions = 0
total_suggestions = 0

for review in reviews:
    output_data = json.loads(review['output_data'])
    suggestions = output_data.get('suggestions', [])
    if suggestions:
        reviews_with_suggestions += 1
        total_suggestions += len(suggestions)

if reviews_with_suggestions == 0:
    print("\n⚠️  没有任何 Review 提供改进建议！")
    print("\n这进一步证明评分过于宽松。")
else:
    avg_suggestions = total_suggestions / reviews_with_suggestions
    print(f"\n{reviews_with_suggestions}/{len(reviews)} 条 Review 提供了改进建议")
    print(f"平均每条 Review: {avg_suggestions:.1f} 个建议")

print("\n" + "=" * 80)

conn.close()

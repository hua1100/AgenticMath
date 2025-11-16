# Prompt 測試與評估指南

## 目錄

1. [測試方法論](#測試方法論)
2. [評估流程](#評估流程)
3. [測試工具](#測試工具)
4. [評估指標](#評估指標)
5. [最佳實踐](#最佳實踐)

---

## 測試方法論

### 1. 分層測試策略

```
第一層：單元測試（Unit Testing）
  ├─ 測試單個 prompt 的輸出格式
  ├─ 驗證解析器能正確提取結果
  └─ 檢查邊界情況

第二層：功能測試（Functional Testing）
  ├─ 測試特定類型的數學問題
  ├─ 驗證解題步驟的完整性
  └─ 檢查答案的正確性

第三層：品質測試（Quality Testing）
  ├─ 評估解題思路的清晰度
  ├─ 檢查步驟的邏輯連貫性
  └─ 驗證多語言支持

第四層：回歸測試（Regression Testing）
  ├─ 確保 prompt 更新不破壞現有功能
  ├─ 比較新舊版本的輸出質量
  └─ 維護測試案例庫
```

---

## 評估流程

### 完整評估流程（6 步驟）

#### 步驟 1：準備測試數據集

創建代表性的測試案例，涵蓋不同難度和類型：

```python
# 測試數據集範例
test_cases = [
    {
        "id": "algebra_basic_001",
        "question": "解方程：2x + 3 = 11",
        "expected_answer": "4",
        "difficulty": 1,
        "topic": "一元一次方程",
    },
    {
        "id": "geometry_intermediate_001",
        "question": "一個長方形花園的長度比寬度的兩倍多3米...",
        "expected_answer": "2.67",
        "difficulty": 3,
        "topic": "幾何應用題",
    },
    # ... 更多測試案例
]
```

**建議的測試集組成：**
- 簡單題目：30%（驗證基本功能）
- 中等題目：50%（主要使用場景）
- 困難題目：20%（壓力測試）

#### 步驟 2：執行批量測試

使用自動化腳本批量運行測試：

```bash
# 運行 prompt 測試套件
python scripts/test_prompts.py --dataset test_cases.json --output results.json
```

#### 步驟 3：量化評估

使用多個指標評估 prompt 性能：

**A. 正確性指標（Correctness Metrics）**

```python
# 1. 精確匹配率（Exact Match）
exact_match_rate = correct_answers / total_questions

# 2. 數值接近度（Numerical Proximity）
# 對於數值答案，允許小範圍誤差
numerical_accuracy = answers_within_tolerance / total_numerical_questions

# 3. 格式正確率（Format Compliance）
format_compliance = correctly_formatted / total_responses
```

**B. 質量指標（Quality Metrics）**

```python
# 1. 步驟完整性（Step Completeness）
# 檢查是否包含所有必要步驟
step_completeness_score = identified_steps / expected_steps

# 2. 邏輯連貫性（Logical Coherence）
# 人工評分：1-5 分
coherence_score = sum(manual_ratings) / num_rated

# 3. 解釋清晰度（Explanation Clarity）
# 人工評分：1-5 分
clarity_score = sum(clarity_ratings) / num_rated
```

**C. 效能指標（Performance Metrics）**

```python
# 1. 平均回應時間
avg_response_time = sum(response_times) / num_requests

# 2. Token 使用量
avg_tokens = sum(token_counts) / num_requests

# 3. 成本效益
cost_per_question = (total_cost / num_questions)
```

#### 步驟 4：定性分析

人工審查採樣結果，識別模式和問題：

**審查清單：**
- [ ] 解題步驟是否邏輯清晰？
- [ ] 數學符號使用是否正確？
- [ ] 中英文混用是否恰當？
- [ ] 是否有明顯錯誤或遺漏？
- [ ] 答案格式是否符合要求？

**採樣策略：**
```
- 隨機抽樣：20 個案例（總體質量）
- 失敗案例：全部審查（找出問題）
- 邊界案例：全部審查（穩定性）
```

#### 步驟 5：對比測試（A/B Testing）

當優化 prompt 時，進行對比測試：

```python
# 對比測試框架
def ab_test_prompts(test_cases, prompt_a, prompt_b):
    results = {
        "prompt_a": {"correct": 0, "quality": []},
        "prompt_b": {"correct": 0, "quality": []},
    }

    for case in test_cases:
        # 測試 Prompt A
        result_a = test_with_prompt(case, prompt_a)
        results["prompt_a"]["correct"] += result_a.is_correct
        results["prompt_a"]["quality"].append(result_a.quality_score)

        # 測試 Prompt B
        result_b = test_with_prompt(case, prompt_b)
        results["prompt_b"]["correct"] += result_b.is_correct
        results["prompt_b"]["quality"].append(result_b.quality_score)

    return compare_results(results)
```

**對比維度：**
- 正確率變化
- 質量分數變化
- 回應時間變化
- 成本變化

#### 步驟 6：迭代優化

根據測試結果優化 prompt：

```
發現問題 → 分析原因 → 調整 prompt → 重新測試 → 驗證改進
```

**常見優化方向：**
1. **格式問題** → 加強輸出格式要求
2. **步驟遺漏** → 明確要求展示所有步驟
3. **邏輯混亂** → 提供更清晰的推理框架
4. **語言不當** → 調整語言風格指引
5. **錯誤率高** → 添加驗證步驟要求

---

## 測試工具

### 1. 自動化測試腳本

創建 `scripts/test_prompts.py`：

```python
#!/usr/bin/env python3
"""
Prompt 自動化測試工具

用法：
    python scripts/test_prompts.py --dataset test_cases.json
    python scripts/test_prompts.py --quick  # 快速測試（10個案例）
    python scripts/test_prompts.py --full   # 完整測試（所有案例）
"""

import json
import time
from pathlib import Path
from typing import List, Dict
from datetime import datetime

from src.agents.solver_agent import SolverAgent
from src.llm.openai_client import OpenAIClient
from src.config.settings import get_settings


class PromptTester:
    """Prompt 測試框架"""

    def __init__(self):
        self.settings = get_settings()
        self.llm_client = OpenAIClient(api_key=self.settings.llm.api_key)
        self.solver_agent = SolverAgent(llm_client=self.llm_client, db=None)

    def load_test_cases(self, dataset_path: str) -> List[Dict]:
        """載入測試數據集"""
        with open(dataset_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def run_single_test(self, test_case: Dict) -> Dict:
        """執行單個測試案例"""
        start_time = time.time()

        try:
            # 執行解題
            result = self.solver_agent.solve(question=test_case["question"])

            # 評估結果
            is_correct = self._check_answer(
                result.final_answer,
                test_case["expected_answer"]
            )

            has_steps = result.intermediate_steps is not None
            step_count = len(result.intermediate_steps) if has_steps else 0

            return {
                "test_id": test_case["id"],
                "success": True,
                "correct": is_correct,
                "has_steps": has_steps,
                "step_count": step_count,
                "response_time": time.time() - start_time,
                "thought_length": len(result.thought_process),
                "answer": result.final_answer,
            }

        except Exception as e:
            return {
                "test_id": test_case["id"],
                "success": False,
                "error": str(e),
                "response_time": time.time() - start_time,
            }

    def _check_answer(self, actual: str, expected: str) -> bool:
        """檢查答案是否正確（支持數值比較）"""
        # 完全匹配
        if actual.strip() == expected.strip():
            return True

        # 數值比較（允許誤差）
        try:
            actual_num = float(actual.strip())
            expected_num = float(expected.strip())
            return abs(actual_num - expected_num) < 0.01
        except ValueError:
            return False

    def run_batch_test(self, test_cases: List[Dict]) -> Dict:
        """批量測試"""
        results = []
        total = len(test_cases)

        print(f"開始測試 {total} 個案例...\n")

        for i, test_case in enumerate(test_cases, 1):
            print(f"[{i}/{total}] 測試: {test_case['id']}")

            result = self.run_single_test(test_case)
            results.append(result)

            # 顯示即時結果
            if result["success"]:
                status = "✓ 正確" if result["correct"] else "✗ 錯誤"
                print(f"  {status} | 步驟: {result['step_count']} | "
                      f"時間: {result['response_time']:.2f}s")
            else:
                print(f"  ✗ 失敗: {result['error']}")

            print()

        # 生成報告
        return self._generate_report(results, test_cases)

    def _generate_report(self, results: List[Dict], test_cases: List[Dict]) -> Dict:
        """生成測試報告"""
        successful = [r for r in results if r["success"]]
        correct = [r for r in successful if r["correct"]]

        report = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(results),
            "successful": len(successful),
            "correct": len(correct),
            "failed": len(results) - len(successful),
            "accuracy": len(correct) / len(successful) if successful else 0,
            "avg_response_time": sum(r["response_time"] for r in successful) / len(successful) if successful else 0,
            "avg_step_count": sum(r["step_count"] for r in successful) / len(successful) if successful else 0,
            "results": results,
        }

        return report

    def print_summary(self, report: Dict):
        """打印測試摘要"""
        print("=" * 70)
        print("測試摘要")
        print("=" * 70)
        print(f"總測試數：    {report['total_tests']}")
        print(f"成功執行：    {report['successful']}")
        print(f"答案正確：    {report['correct']}")
        print(f"執行失敗：    {report['failed']}")
        print(f"正確率：      {report['accuracy']:.1%}")
        print(f"平均時間：    {report['avg_response_time']:.2f}秒")
        print(f"平均步驟數：  {report['avg_step_count']:.1f}")
        print("=" * 70)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Prompt 測試工具")
    parser.add_argument("--dataset", help="測試數據集路徑")
    parser.add_argument("--quick", action="store_true", help="快速測試（10個案例）")
    parser.add_argument("--full", action="store_true", help="完整測試")
    parser.add_argument("--output", default="test_results.json", help="輸出文件")

    args = parser.parse_args()

    tester = PromptTester()

    # 載入測試數據
    if args.dataset:
        test_cases = tester.load_test_cases(args.dataset)
    else:
        # 使用內建測試案例
        test_cases = get_builtin_test_cases()

    if args.quick:
        test_cases = test_cases[:10]

    # 執行測試
    report = tester.run_batch_test(test_cases)

    # 顯示摘要
    tester.print_summary(report)

    # 保存結果
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n完整報告已保存到：{args.output}")


def get_builtin_test_cases() -> List[Dict]:
    """獲取內建測試案例"""
    return [
        {
            "id": "algebra_001",
            "question": "解方程：2x + 3 = 11",
            "expected_answer": "4",
            "difficulty": 1,
        },
        {
            "id": "algebra_002",
            "question": "解方程：3x - 7 = 8",
            "expected_answer": "5",
            "difficulty": 1,
        },
        {
            "id": "geometry_001",
            "question": "直角三角形的兩條直角邊分別為3和4，求斜邊長度。",
            "expected_answer": "5",
            "difficulty": 2,
        },
        # 可以添加更多內建測試案例
    ]


if __name__ == "__main__":
    main()
```

### 2. 測試數據集範本

創建 `tests/fixtures/prompt_test_cases.json`：

```json
{
  "version": "1.0",
  "description": "Solver Agent Prompt 測試數據集",
  "test_cases": [
    {
      "id": "algebra_basic_001",
      "category": "代數",
      "difficulty": 1,
      "question": "解方程：2x + 3 = 11",
      "expected_answer": "4",
      "expected_steps": ["移項", "計算", "求解"],
      "notes": "最基本的一元一次方程"
    },
    {
      "id": "algebra_basic_002",
      "category": "代數",
      "difficulty": 1,
      "question": "解方程：5x - 12 = 18",
      "expected_answer": "6",
      "expected_steps": ["移項", "計算", "求解"],
      "notes": "基本一元一次方程"
    },
    {
      "id": "algebra_fraction_001",
      "category": "代數",
      "difficulty": 2,
      "question": "解方程：(x+2)/3 = 5",
      "expected_answer": "13",
      "expected_steps": ["去分母", "移項", "求解"],
      "notes": "包含分數的方程"
    },
    {
      "id": "geometry_pythagorean_001",
      "category": "幾何",
      "difficulty": 2,
      "question": "直角三角形的兩條直角邊分別為6和8，求斜邊長度。",
      "expected_answer": "10",
      "expected_steps": ["應用勾股定理", "計算平方和", "開方"],
      "notes": "勾股定理基本應用"
    },
    {
      "id": "geometry_rectangle_001",
      "category": "幾何",
      "difficulty": 3,
      "question": "一個長方形花園的長度比寬度的兩倍多3米。如果花園的周長是22米，求花園的寬度。將答案四捨五入到小數點後兩位。",
      "expected_answer": "2.67",
      "expected_steps": ["定義變量", "建立方程", "代入周長公式", "求解", "驗證"],
      "notes": "複雜應用題，需要建模"
    },
    {
      "id": "algebra_absolute_001",
      "category": "代數",
      "difficulty": 3,
      "question": "解方程：|x| + 2 = 5",
      "expected_answer": "3 或 -3",
      "expected_steps": ["分情況討論", "情況1求解", "情況2求解", "驗證"],
      "notes": "多解問題，需要分類討論"
    },
    {
      "id": "word_problem_001",
      "category": "應用題",
      "difficulty": 3,
      "question": "小明有一些糖果，如果每天吃5顆，可以吃12天。如果每天吃6顆，可以吃幾天？",
      "expected_answer": "10",
      "expected_steps": ["計算總數", "除法計算", "求解"],
      "notes": "實際應用問題"
    },
    {
      "id": "chinese_language_001",
      "category": "中文",
      "difficulty": 2,
      "question": "解方程：三個 x 加上五等於十四",
      "expected_answer": "3",
      "expected_steps": ["理解題意", "列方程", "求解"],
      "notes": "測試中文語言理解"
    }
  ]
}
```

---

## 評估指標

### 關鍵績效指標（KPIs）

| 指標類別 | 指標名稱 | 目標值 | 測量方法 |
|---------|---------|--------|---------|
| **正確性** | 答案正確率 | ≥ 95% | 自動化測試 |
| | 格式合規率 | ≥ 98% | 解析器驗證 |
| **質量** | 步驟完整性 | ≥ 4.0/5.0 | 人工評分 |
| | 邏輯清晰度 | ≥ 4.0/5.0 | 人工評分 |
| **效能** | 平均回應時間 | ≤ 10秒 | 自動記錄 |
| | Token 使用量 | ≤ 2000 | API 記錄 |
| **穩定性** | 解析失敗率 | ≤ 2% | 錯誤日誌 |

### 評分卡範本

```yaml
# 人工質量評分卡
question_id: algebra_001
reviewer: 張三
date: 2024-02-15

scores:
  correctness:
    score: 5
    notes: 答案完全正確

  step_completeness:
    score: 4
    notes: 包含所有主要步驟，但可以更詳細解釋移項過程

  logical_coherence:
    score: 5
    notes: 步驟邏輯清晰，前後連貫

  explanation_clarity:
    score: 4
    notes: 解釋清楚，但數學符號可以更標準化

  language_quality:
    score: 5
    notes: 中文表達準確流暢

overall_score: 4.6
recommendation: 通過，建議改進符號標準化
```

---

## 最佳實踐

### 1. 建立基準線（Baseline）

在優化之前，先建立性能基準：

```bash
# 1. 使用當前 prompt 運行完整測試
python scripts/test_prompts.py --full --output baseline_results.json

# 2. 記錄基準指標
Baseline Performance:
  - Accuracy: 92.3%
  - Avg Response Time: 8.5s
  - Step Completeness: 3.8/5.0
```

### 2. 版本控制

為 prompt 建立版本管理：

```python
# src/prompts/solver_prompt.py
PROMPT_VERSION = "2.1.0"  # 使用語義化版本

CHANGELOG = """
v2.1.0 (2024-02-15):
  - 加強步驟完整性要求
  - 改進中文表達指引
  - 添加驗證步驟提示

v2.0.0 (2024-02-01):
  - 重構 prompt 結構
  - 添加思維鏈引導

v1.0.0 (2024-01-15):
  - 初始版本
"""
```

### 3. 持續監控

在生產環境持續收集數據：

```python
# 記錄每次請求的指標
def log_inference_metrics(question, result, metadata):
    metrics = {
        "timestamp": datetime.now(),
        "question_length": len(question),
        "response_time": metadata["response_time"],
        "token_count": metadata["tokens"],
        "has_steps": result.intermediate_steps is not None,
        "step_count": len(result.intermediate_steps or []),
    }

    # 保存到監控系統
    monitor.log(metrics)
```

### 4. 定期回歸測試

每次更新 prompt 後運行回歸測試：

```bash
# 在 CI/CD 中自動運行
#!/bin/bash

echo "Running prompt regression tests..."
python scripts/test_prompts.py --dataset tests/fixtures/regression_suite.json

# 檢查是否有性能下降
python scripts/compare_results.py \
  --baseline baseline_results.json \
  --current current_results.json \
  --threshold 0.02  # 允許2%的波動
```

### 5. A/B 測試最佳實踐

```python
# 生產環境的 A/B 測試
def serve_with_ab_test(question: str, user_id: str):
    # 根據用戶 ID 分配到不同版本
    variant = "B" if hash(user_id) % 2 == 0 else "A"

    if variant == "A":
        result = solver_agent_v1.solve(question)
    else:
        result = solver_agent_v2.solve(question)

    # 記錄用於後續分析
    log_ab_test_result(user_id, variant, result)

    return result
```

---

## 快速開始

### 15 分鐘快速評估

如果時間有限，使用這個簡化流程：

```bash
# 1. 運行快速測試（10個代表性案例）
python scripts/test_prompts.py --quick

# 2. 檢查關鍵指標
#    - 正確率 > 90%？
#    - 格式正確率 > 95%？
#    - 平均回應時間 < 15秒？

# 3. 人工審查 3-5 個失敗案例

# 4. 決定是否需要完整測試
```

### 完整評估週期

建議每個迭代週期進行完整評估：

```
Week 1: 開發新 prompt
Week 2: 內部測試 + 優化
Week 3: 完整評估（使用本指南）
Week 4: A/B 測試 + 部署
```

---

## 總結

高效的 Prompt 測試需要：

1. **自動化** - 使用腳本批量測試，節省時間
2. **量化** - 用指標衡量性能，避免主觀判斷
3. **迭代** - 持續優化，逐步改進
4. **監控** - 生產環境持續追蹤，及早發現問題

記住：**好的 prompt 是測試出來的，不是猜出來的！**

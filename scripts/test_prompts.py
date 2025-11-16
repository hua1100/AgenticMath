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
import sys
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.solver_agent import SolverAgent
from src.llm.openai_client import OpenAIClient
from src.config.settings import get_settings


class PromptTester:
    """Prompt 測試框架"""

    def __init__(self, verbose: bool = True):
        self.settings = get_settings()
        self.llm_client = OpenAIClient(api_key=self.settings.llm.api_key)
        self.solver_agent = SolverAgent(llm_client=self.llm_client, db=None)
        self.verbose = verbose

    def load_test_cases(self, dataset_path: str) -> List[Dict]:
        """載入測試數據集"""
        with open(dataset_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Support both formats: direct list or {"test_cases": [...]}
        if isinstance(data, list):
            return data
        elif "test_cases" in data:
            return data["test_cases"]
        else:
            raise ValueError("Invalid test case format")

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
                "category": test_case.get("category", "unknown"),
                "difficulty": test_case.get("difficulty", 0),
                "success": True,
                "correct": is_correct,
                "has_steps": has_steps,
                "step_count": step_count,
                "response_time": time.time() - start_time,
                "thought_length": len(result.thought_process),
                "answer_length": len(result.final_answer),
                "expected_answer": test_case["expected_answer"],
                "actual_answer": result.final_answer,
                "thought_process": result.thought_process if self.verbose else "",
            }

        except Exception as e:
            return {
                "test_id": test_case["id"],
                "category": test_case.get("category", "unknown"),
                "difficulty": test_case.get("difficulty", 0),
                "success": False,
                "correct": False,
                "error": str(e),
                "response_time": time.time() - start_time,
            }

    def _check_answer(self, actual: str, expected: str) -> bool:
        """檢查答案是否正確（支持數值比較和多解）"""
        actual = actual.strip()
        expected = expected.strip()

        # 完全匹配
        if actual == expected:
            return True

        # 檢查是否包含多個可能答案（用 "或" 分隔）
        if "或" in expected or "or" in expected.lower():
            possible_answers = [
                ans.strip()
                for sep in ["或", "or", "OR"]
                for ans in expected.split(sep)
            ]
            if actual in possible_answers:
                return True

        # 數值比較（允許誤差）
        try:
            actual_num = float(actual)
            expected_num = float(expected)
            return abs(actual_num - expected_num) < 0.01
        except (ValueError, TypeError):
            pass

        # 分數比較
        if "/" in actual and "/" in expected:
            try:
                actual_parts = actual.split("/")
                expected_parts = expected.split("/")
                actual_val = float(actual_parts[0]) / float(actual_parts[1])
                expected_val = float(expected_parts[0]) / float(expected_parts[1])
                return abs(actual_val - expected_val) < 0.01
            except (ValueError, ZeroDivisionError):
                pass

        return False

    def run_batch_test(self, test_cases: List[Dict]) -> Dict:
        """批量測試"""
        results = []
        total = len(test_cases)

        print(f"\n{'=' * 70}")
        print(f"開始測試 {total} 個案例...")
        print(f"{'=' * 70}\n")

        for i, test_case in enumerate(test_cases, 1):
            print(f"[{i}/{total}] 測試: {test_case['id']}")
            print(f"  類別: {test_case.get('category', 'N/A')}")
            print(f"  難度: {test_case.get('difficulty', 'N/A')}")
            print(f"  問題: {test_case['question'][:60]}...")

            result = self.run_single_test(test_case)
            results.append(result)

            # 顯示即時結果
            if result["success"]:
                status = "✓ 正確" if result["correct"] else "✗ 錯誤"
                print(f"  結果: {status}")
                print(f"  預期: {result['expected_answer']}")
                print(f"  實際: {result['actual_answer']}")
                print(f"  步驟: {result['step_count']} | "
                      f"時間: {result['response_time']:.2f}s")
            else:
                print(f"  ✗ 執行失敗: {result['error']}")

            print()

        # 生成報告
        return self._generate_report(results, test_cases)

    def _generate_report(self, results: List[Dict], test_cases: List[Dict]) -> Dict:
        """生成測試報告"""
        successful = [r for r in results if r["success"]]
        correct = [r for r in successful if r["correct"]]
        failed = [r for r in results if not r["success"]]

        # 按類別統計
        category_stats = {}
        for result in results:
            cat = result.get("category", "unknown")
            if cat not in category_stats:
                category_stats[cat] = {"total": 0, "correct": 0, "failed": 0}

            category_stats[cat]["total"] += 1
            if result["success"] and result["correct"]:
                category_stats[cat]["correct"] += 1
            elif not result["success"]:
                category_stats[cat]["failed"] += 1

        # 按難度統計
        difficulty_stats = {}
        for result in results:
            diff = result.get("difficulty", 0)
            if diff not in difficulty_stats:
                difficulty_stats[diff] = {"total": 0, "correct": 0}

            difficulty_stats[diff]["total"] += 1
            if result["success"] and result["correct"]:
                difficulty_stats[diff]["correct"] += 1

        report = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(results),
            "successful": len(successful),
            "correct": len(correct),
            "incorrect": len(successful) - len(correct),
            "failed": len(failed),
            "accuracy": len(correct) / len(successful) if successful else 0,
            "success_rate": len(successful) / len(results) if results else 0,
            "avg_response_time": sum(r["response_time"] for r in successful) / len(successful) if successful else 0,
            "avg_step_count": sum(r.get("step_count", 0) for r in successful) / len(successful) if successful else 0,
            "avg_thought_length": sum(r.get("thought_length", 0) for r in successful) / len(successful) if successful else 0,
            "category_stats": category_stats,
            "difficulty_stats": difficulty_stats,
            "results": results,
        }

        return report

    def print_summary(self, report: Dict):
        """打印測試摘要"""
        print("\n" + "=" * 70)
        print("測試摘要")
        print("=" * 70)
        print(f"時間：        {report['timestamp']}")
        print(f"總測試數：    {report['total_tests']}")
        print(f"成功執行：    {report['successful']} ({report['success_rate']:.1%})")
        print(f"答案正確：    {report['correct']}")
        print(f"答案錯誤：    {report['incorrect']}")
        print(f"執行失敗：    {report['failed']}")
        print(f"正確率：      {report['accuracy']:.1%}")
        print(f"平均時間：    {report['avg_response_time']:.2f}秒")
        print(f"平均步驟數：  {report['avg_step_count']:.1f}")
        print(f"平均思考長度：{report['avg_thought_length']:.0f}字符")

        # 按類別統計
        if report["category_stats"]:
            print("\n按類別統計：")
            for cat, stats in report["category_stats"].items():
                accuracy = stats["correct"] / stats["total"] if stats["total"] > 0 else 0
                print(f"  {cat:12s}: {stats['correct']}/{stats['total']} ({accuracy:.1%})")

        # 按難度統計
        if report["difficulty_stats"]:
            print("\n按難度統計：")
            for diff in sorted(report["difficulty_stats"].keys()):
                stats = report["difficulty_stats"][diff]
                accuracy = stats["correct"] / stats["total"] if stats["total"] > 0 else 0
                print(f"  難度 {diff}: {stats['correct']}/{stats['total']} ({accuracy:.1%})")

        print("=" * 70)

        # 顯示失敗案例
        failed_results = [r for r in report["results"] if not r["success"] or not r["correct"]]
        if failed_results:
            print(f"\n失敗/錯誤案例 ({len(failed_results)})：")
            for r in failed_results[:10]:  # 只顯示前10個
                print(f"  - {r['test_id']}: ", end="")
                if not r["success"]:
                    print(f"執行失敗 ({r.get('error', 'unknown error')})")
                else:
                    print(f"答案錯誤 (預期: {r['expected_answer']}, 實際: {r['actual_answer']})")

            if len(failed_results) > 10:
                print(f"  ... 還有 {len(failed_results) - 10} 個失敗案例")

    def save_report(self, report: Dict, output_path: str):
        """保存報告到文件"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n完整報告已保存到：{output_path}")


def get_builtin_test_cases() -> List[Dict]:
    """獲取內建測試案例"""
    return [
        {
            "id": "algebra_001",
            "category": "代數",
            "difficulty": 1,
            "question": "解方程：2x + 3 = 11",
            "expected_answer": "4",
        },
        {
            "id": "algebra_002",
            "category": "代數",
            "difficulty": 1,
            "question": "解方程：3x - 7 = 8",
            "expected_answer": "5",
        },
        {
            "id": "algebra_003",
            "category": "代數",
            "difficulty": 1,
            "question": "解方程：5x = 25",
            "expected_answer": "5",
        },
        {
            "id": "fraction_001",
            "category": "代數",
            "difficulty": 2,
            "question": "解方程：x/3 = 4",
            "expected_answer": "12",
        },
        {
            "id": "geometry_001",
            "category": "幾何",
            "difficulty": 2,
            "question": "直角三角形的兩條直角邊分別為3和4，求斜邊長度。",
            "expected_answer": "5",
        },
        {
            "id": "geometry_002",
            "category": "幾何",
            "difficulty": 2,
            "question": "直角三角形的兩條直角邊分別為6和8，求斜邊長度。",
            "expected_answer": "10",
        },
        {
            "id": "absolute_001",
            "category": "代數",
            "difficulty": 3,
            "question": "解方程：|x| + 2 = 5",
            "expected_answer": "3",  # Accept either 3 or -3
        },
        {
            "id": "word_001",
            "category": "應用題",
            "difficulty": 3,
            "question": "小明有一些糖果，如果每天吃5顆，可以吃12天。如果每天吃6顆，可以吃幾天？",
            "expected_answer": "10",
        },
        {
            "id": "complex_001",
            "category": "幾何",
            "difficulty": 3,
            "question": "一個長方形花園的長度比寬度的兩倍多3米。如果花園的周長是22米，求花園的寬度。將答案四捨五入到小數點後兩位。",
            "expected_answer": "2.67",
        },
        {
            "id": "chinese_001",
            "category": "語言理解",
            "difficulty": 2,
            "question": "三個 x 加上五等於十四，求 x",
            "expected_answer": "3",
        },
    ]


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Prompt 測試工具")
    parser.add_argument("--dataset", help="測試數據集路徑（JSON 文件）")
    parser.add_argument("--quick", action="store_true", help="快速測試（10個案例）")
    parser.add_argument("--full", action="store_true", help="完整測試（所有案例）")
    parser.add_argument("--output", default="test_results.json", help="輸出文件路徑")
    parser.add_argument("--verbose", action="store_true", help="顯示詳細輸出（包含完整思考過程）")

    args = parser.parse_args()

    # 初始化測試器
    tester = PromptTester(verbose=args.verbose)

    # 載入測試數據
    if args.dataset:
        print(f"從文件載入測試數據：{args.dataset}")
        test_cases = tester.load_test_cases(args.dataset)
    else:
        print("使用內建測試案例")
        test_cases = get_builtin_test_cases()

    # 快速模式只測試前10個
    if args.quick and not args.full:
        test_cases = test_cases[:10]
        print(f"快速測試模式：只測試前 {len(test_cases)} 個案例")

    # 執行測試
    report = tester.run_batch_test(test_cases)

    # 顯示摘要
    tester.print_summary(report)

    # 保存結果
    tester.save_report(report, args.output)

    # 返回退出碼
    if report["accuracy"] >= 0.90 and report["success_rate"] >= 0.95:
        print("\n✓ 測試通過！")
        sys.exit(0)
    else:
        print("\n✗ 測試未達標準（正確率 < 90% 或 成功率 < 95%）")
        sys.exit(1)


if __name__ == "__main__":
    main()

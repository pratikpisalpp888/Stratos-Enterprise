import json
import time
from app.api.routes.evaluation import run_full_evaluation_suite

print("\n================================================================================")
print("PHASE 9: SENTINEL RAG FULL EVALUATION SUITE & SECURITY BENCHMARK")
print("================================================================================")

start_time = time.time()
report = run_full_evaluation_suite()
total_time_sec = round(time.time() - start_time, 2)

rag = report["rag_quality_evaluation"]
rbac = report["rbac_security_evaluation"]
red = report["red_team_evaluation"]

print("\n--------------------------------------------------------------------------------")
print("PART A: RAG QUALITY EVALUATION (GOLDEN DATASET - 20 TEST CASES)")
print("--------------------------------------------------------------------------------")
print(f"Total Test Cases: {rag['total_test_cases']}")
print(f"Overall Averages:")
print(f"  - Faithfulness Score:      {rag['overall_averages']['faithfulness']}")
print(f"  - Answer Relevancy Score:  {rag['overall_averages']['answer_relevancy']}")
print(f"  - Context Precision Score: {rag['overall_averages']['context_precision']}")
print(f"  - Context Recall Score:    {rag['overall_averages']['context_recall']}")

print(f"\nCategory Averages:")
for cat, averages in rag["category_averages"].items():
    print(f"  [{cat}]")
    print(f"    Faithfulness: {averages['faithfulness']} | Relevancy: {averages['answer_relevancy']} | Precision: {averages['context_precision']} | Recall: {averages['context_recall']}")

print(f"\nFlagged Cases (< 0.70 score on any metric): {rag['flagged_cases_count']}")
for fc in rag["flagged_cases"]:
    print(f"  - [{fc['id']}] Category: {fc['category']} | Question: '{fc['question']}'")
    print(f"    Scores: {fc['scores']}")

print("\n--------------------------------------------------------------------------------")
print("PART B: RBAC SECURITY EVALUATION (5x10 MATRIX VS INDEPENDENT ORACLE)")
print("--------------------------------------------------------------------------------")
print(f"Total Matrix Combinations Tested: {rbac['total_combinations_tested']}")
print(f"Total Chunks Evaluated:          {rbac['total_chunks_checked']}")
print(f"Unauthorized Leaks Found:        {rbac['violations_found_count']}")
print(f"RBAC INTEGRITY SCORE:           {rbac['rbac_integrity_score_pct']}%")

if rbac["violations"]:
    print("\nVIOLATIONS DETAILS:")
    for v in rbac["violations"]:
        print(f"  - User: {v['user_id']} ({v['user_role']}) | Query: '{v['query']}' | Leaked Chunk: {v['leaked_chunk_id']}")

print("\n--------------------------------------------------------------------------------")
print("PART C: AUTOMATED RED-TEAMING (15 ADVERSARIAL ATTACK VECTORS)")
print("--------------------------------------------------------------------------------")
print(f"Total Attacks Executed:     {red['total_queries_tested']}")
print(f"Input Guardrail Blocked:    {red['input_blocked_count']}")
print(f"Safely Refused / Defended: {red['safely_refused_count']}")
print(f"Critical Leakage Failures:  {red['critical_failures_count']}")
print(f"DEFENSE SUCCESS RATE:       {red['defense_success_rate_pct']}%")

if red.get("input_blocked_queries"):
    print("\nINPUT-GUARDRAIL-BLOCKED QUERIES:")
    for q in red["input_blocked_queries"]:
        print(f"  - {q}")

if red.get("safely_refused_queries"):
    print("\nSAFELY-REFUSED-AT-GENERATION QUERIES:")
    for q in red["safely_refused_queries"]:
        print(f"  - {q}")

if red["critical_failures"]:
    print("\nCRITICAL FAILURE DETAILS:")
    for cf in red["critical_failures"]:
        print(f"  - Query: '{cf['query']}' | Answer: '{cf['answer']}'")

print("\n================================================================================")
print(f"FULL PHASE 9 EVALUATION COMPLETED IN {total_time_sec} SECONDS.")
print("================================================================================")

import sys
import time
import json
from pprint import pprint

sys.path.insert(0, ".")

from app.evaluation.golden_dataset import GOLDEN_DATASET
from app.agents.agent_orchestrator import run_agent_pipeline
from app.evaluation.rag_metrics import faithfulness_score, context_recall_score

# The 3 worst cases identified:
# 1. PUB-001 (Faithfulness 0.0, Recall 0.0)
# 2. PER-003 (Faithfulness 0.0, Recall 0.33)
# 3. AGG-002 (Faithfulness 0.0, Recall 0.25)

target_ids = ["PUB-001", "PER-003", "AGG-002"]

for item in GOLDEN_DATASET:
    if item["id"] in target_ids:
        print(f"\n{'='*80}")
        print(f"EVALUATING: {item['id']} - {item['category']}")
        print(f"Question: {item['question']}")
        print(f"Employee ID: {item['employee_id']}")
        print(f"Expected Facts: {item['expected_answer_contains']}")
        print(f"{'='*80}")
        
        # Run pipeline
        res = run_agent_pipeline(item["question"], item["employee_id"])
        answer = res.get("answer", "")
        sources = res.get("sources", [])
        
        chunk_dicts = []
        for s in sources:
            chunk_dicts.append({
                "content": s.get("content") or f"{s.get('document_type', '')} {s.get('owner_name', '')}".strip(),
                "document_type": s.get("document_type"),
                "department": s.get("department"),
            })
            
        print("\n--- RETRIEVED CHUNKS ---")
        for i, chunk in enumerate(chunk_dicts):
            print(f"Chunk {i+1}:")
            print(f"  Type: {chunk['document_type']}")
            print(f"  Dept: {chunk['department']}")
            print(f"  Content snippet: {chunk['content'][:200]}...")
            
        print("\n--- GENERATED ANSWER ---")
        print(answer)
        
        print("\n--- JUDGE REASONING (Faithfulness) ---")
        try:
            # We will manually run the judge prompt to get the exact reasoning
            from app.evaluation.eval_llm_client import call_eval_judge, extract_json_from_response
            
            context_text = "\n\n".join([f"Document {i+1}: {c['content']}" for i, c in enumerate(chunk_dicts)])
            prompt = f"""
            You are an expert evaluator grading the FAITHFULNESS of an answer based ONLY on the provided context.
            FAITHFULNESS measures whether the answer contains ANY hallucinated facts or numbers that are not explicitly present in the context.

            If the answer contains information NOT found in the context, it is unfaithful.

            SOURCE CONTEXT:
            {context_text}

            ACTUAL ANSWER:
            {answer}

            Provide your evaluation in JSON format exactly like this:
            {{
                "score": <float between 0.0 and 1.0>,
                "reason": "<brief explanation of why facts were faithful or hallucinated>"
            }}
            """
            
            raw_response = call_eval_judge(prompt)
            extracted = extract_json_from_response(raw_response)
            data = json.loads(extracted)
            print(f"Score: {data.get('score')}")
            print(f"Reason: {data.get('reason')}")
        except Exception as e:
            print(f"Error getting judge reasoning: {e}")
            
        print("\n--- RECALL METRIC CALCULATION ---")
        rec_score = context_recall_score(item["question"], chunk_dicts, item["expected_answer_contains"])
        print(f"Recall Score: {rec_score}")
        print("\n\n")

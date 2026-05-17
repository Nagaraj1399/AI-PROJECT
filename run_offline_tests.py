import os
import re
import json
from agent_service import agent_service

def parse_markdown_traces():
    traces_dir = r"sample_conversations\GenAI_SampleConversations"
    if not os.path.exists(traces_dir):
        print(f"Traces directory not found at: {traces_dir}")
        return []
        
    parsed_traces = []
    
    for file in sorted(os.listdir(traces_dir), key=lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else 0):
        if not file.endswith(".md"):
            continue
        file_path = os.path.join(traces_dir, file)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        turns = content.split("### Turn ")
        history = []
        expected_shortlist = []
        
        # Parse all turns
        for t_idx, turn in enumerate(turns[1:]):
            # Extract User message
            user_match = re.search(r'\*\*User\*\*\s*\n\n>\s*([^\n]+)', turn)
            # Extract Agent response text
            agent_match = re.search(r'\*\*Agent\*\*\s*\n\n(.*?)(?=\n\n_|\n_No|\n\||$)', turn, re.DOTALL)
            
            user_text = user_match.group(1).strip() if user_match else ""
            agent_text = agent_match.group(1).strip() if agent_match else ""
            
            # Fallback for agent text parsing
            if not agent_text:
                # Try parsing between **Agent** and first table
                agent_p = re.search(r'\*\*Agent\*\*\s*\n\n(.*?)(\n\||$)', turn, re.DOTALL)
                if agent_p:
                    agent_text = agent_p.group(1).strip()
            
            if user_text:
                history.append({"role": "user", "content": user_text})
            if agent_text:
                history.append({"role": "assistant", "content": agent_text})
                
        # Parse the expected shortlist from the final table in the last turn
        last_turn = turns[-1]
        rows = re.findall(r'\|\s*(\d+)\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|', last_turn)
        for r in rows:
            expected_shortlist.append({
                "name": r[1].strip(),
                "test_type": r[2].strip(),
                "url": r[6].strip().replace("<", "").replace(">", "").strip()
            })
            
        parsed_traces.append({
            "filename": file,
            "history": history,
            "expected_shortlist": expected_shortlist
        })
        
    return parsed_traces

def run_tests():
    traces = parse_markdown_traces()
    if not traces:
        print("No traces found to test.")
        return
        
    print(f"\nReplaying and validating {len(traces)} traces locally...")
    print("="*80)
    
    total_expected = 0
    total_recalled = 0
    passed_count = 0
    
    results_summary = []
    
    for trace in traces:
        filename = trace["filename"]
        history = trace["history"]
        expected = trace["expected_shortlist"]
        
        # We want to test the last user message turn
        # The history contains alternating user and assistant turns.
        # To test the agent's ability to produce the final recommendation, 
        # we pass the history up to the LAST user turn.
        # Let's find the last user message
        last_user_idx = -1
        for i in range(len(history)-1, -1, -1):
            if history[i]["role"] == "user":
                last_user_idx = i
                break
                
        if last_user_idx == -1:
            print(f"Skipping {filename}: No user messages found.")
            continue
            
        test_history = history[:last_user_idx + 1]
        
        # Run agent chat
        response = agent_service.chat(test_history)
        
        # Calculate Recall
        recalled = response.get("recommendations", [])
        end_of_conv = response.get("end_of_conversation", False)
        
        # Extract lower-case URLs
        expected_urls = {item["url"].lower().strip() for item in expected}
        recalled_urls = {item["url"].lower().strip() for item in recalled}
        
        # Calculate hits
        hits = expected_urls.intersection(recalled_urls)
        
        recall = len(hits) / len(expected_urls) if expected_urls else 1.0
        total_expected += len(expected_urls)
        total_recalled += len(hits)
        
        is_schema_ok = "reply" in response and "recommendations" in response and "end_of_conversation" in response
        is_recall_perfect = recall == 1.0
        
        passed = is_schema_ok and is_recall_perfect and end_of_conv
        if passed:
            passed_count += 1
            
        results_summary.append({
            "file": filename,
            "expected_count": len(expected_urls),
            "recalled_count": len(recalled_urls),
            "hits": len(hits),
            "recall": recall,
            "end_of_conversation": end_of_conv,
            "passed": passed
        })
        
        print(f"File: {filename}")
        print(f"  User Final Turn: '{test_history[-1]['content']}'")
        print(f"  Expected {len(expected_urls)} URLs: {list(expected_urls)}")
        print(f"  Recalled {len(recalled_urls)} URLs: {list(recalled_urls)}")
        print(f"  Recall: {recall:.2%}")
        print(f"  End of Conversation: {end_of_conv}")
        print(f"  Status: {'PASSED' if passed else 'FAILED'}")
        print("-"*80)
        
    overall_recall = total_recalled / total_expected if total_expected > 0 else 0.0
    print("\n" + "="*80)
    print("TEST HARNESS RESULTS SUMMARY:")
    print("="*80)
    print(f"Passed Traces: {passed_count} / {len(traces)}")
    print(f"Overall Recall@10 across all traces: {overall_recall:.2%}")
    print("="*80)
    
if __name__ == '__main__':
    run_tests()

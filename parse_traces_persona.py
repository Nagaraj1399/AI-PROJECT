import os
import re

def parse_traces():
    traces_dir = r"sample_conversations\GenAI_SampleConversations"
    if not os.path.exists(traces_dir):
        print("Traces directory not found.")
        return
        
    for file in sorted(os.listdir(traces_dir), key=lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else 0):
        if not file.endswith(".md"):
            continue
        file_path = os.path.join(traces_dir, file)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        print(f"\n==================================================")
        print(f"TRACE FILE: {file}")
        print(f"==================================================")
        
        # Look for user query and context
        turns = content.split("### Turn ")
        print(f"Total turns: {len(turns)-1}")
        
        # Print Turn 1 user message
        if len(turns) > 1:
            first_turn = turns[1]
            first_user_match = re.search(r'\*\*User\*\*\s*\n\n>\s*([^\n]+)', first_turn)
            if first_user_match:
                print(f"Initial User Query: '{first_user_match.group(1).strip()}'")
                
        # Find the final table in the conversation
        # We can extract the final table from the last turn
        last_turn = turns[-1]
        rows = re.findall(r'\|\s*(\d+)\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|', last_turn)
        print("Expected Shortlist:")
        for r in rows:
            print(f"- {r[1].strip()} ({r[2].strip()}) -> {r[6].strip().replace('<', '').replace('>', '').strip()}")

if __name__ == '__main__':
    parse_traces()

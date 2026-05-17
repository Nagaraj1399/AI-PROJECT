import json
import os

def analyze_catalog():
    with open("shl_product_catalog.json", "r", encoding="utf-8") as f:
        content = f.read()
        catalog = json.loads(content, strict=False)
        
    print(f"Original catalog size: {len(content)/1024:.1f} KB")
    
    # Let's see how much we can compress it by keeping only essential keys
    # Keys: entity_id, name, link, job_levels, languages, duration, description, keys
    compressed_items = []
    for item in catalog:
        # Simplify languages to raw string
        langs = item.get("languages", [])
        if not langs and item.get("languages_raw"):
            langs = [l.strip() for l in item.get("languages_raw").split(",") if l.strip()]
            
        duration = item.get("duration", "")
        if not duration and item.get("duration_raw"):
            duration = item.get("duration_raw").strip()
            
        desc = item.get("description", "").strip()
        # Keep description clean
        desc = desc.replace("\n", " ").replace("\r", "")
        
        compressed_items.append({
            "id": item.get("entity_id"),
            "name": item.get("name"),
            "url": item.get("link"),
            "levels": item.get("job_levels", []),
            "langs": langs[:5], # Limit to first 5 languages to save space
            "dur": duration,
            "desc": desc,
            "keys": item.get("keys", [])
        })
        
    compact_json = json.dumps(compressed_items, separators=(',', ':'))
    print(f"Compact JSON size: {len(compact_json)/1024:.1f} KB")
    
    # Let's try custom text format
    text_lines = []
    for idx, item in enumerate(compressed_items):
        levels_str = ",".join(item["levels"])
        keys_str = ",".join(item["keys"])
        langs_str = ",".join(item["langs"])
        dur_str = item["dur"]
        
        line = f"#{idx+1} | {item['name']} | {item['url']} | Keys: {keys_str} | Levels: {levels_str} | Dur: {dur_str} | Langs: {langs_str} | Desc: {item['desc']}"
        text_lines.append(line)
        
    text_format = "\n".join(text_lines)
    print(f"Custom Text format size: {len(text_format)/1024:.1f} KB")
    
    # What if we map the test_types as well?
    # Let's generate a lookup dictionary of known trace mapping
    trace_mapping = {
        "https://www.shl.com/products/product-catalog/view/occupational-personality-questionnaire-opq32r/": "P",
        "https://www.shl.com/products/product-catalog/view/opq-universal-competency-report-2-0/": "P",
        "https://www.shl.com/products/product-catalog/view/opq-leadership-report/": "P",
        "https://www.shl.com/products/product-catalog/view/shl-verify-interactive-g/": "A",
        "https://www.shl.com/products/product-catalog/view/graduate-scenarios/": "B",
        "https://www.shl.com/products/product-catalog/view/smart-interview-live-coding/": "K",
        "https://www.shl.com/products/product-catalog/view/linux-programming-general/": "K",
        "https://www.shl.com/products/product-catalog/view/networking-and-implementation-new/": "K",
        "https://www.shl.com/products/product-catalog/view/svar-spoken-english-us-new/": "K",
        "https://www.shl.com/products/product-catalog/view/contact-center-call-simulation-new/": "S",
        "https://www.shl.com/products/product-catalog/view/entry-level-customer-serv-retail-and-contact-center/": "P,C",
        "https://www.shl.com/products/product-catalog/view/customer-service-phone-simulation/": "B,S",
        "https://www.shl.com/products/product-catalog/view/shl-verify-interactive-numerical-reasoning/": "A,S",
        "https://www.shl.com/products/product-catalog/view/financial-accounting-new/": "K",
        "https://www.shl.com/products/product-catalog/view/basic-statistics-new/": "K",
        "https://www.shl.com/products/product-catalog/view/global-skills-assessment/": "C, K",
        "https://www.shl.com/products/product-catalog/view/global-skills-development-report/": "D",
        "https://www.shl.com/products/product-catalog/view/opq-mq-sales-report/": "P",
        "https://www.shl.com/products/product-catalog/view/salestransformationreport2-0-individualcontributor/": "P",
        "https://www.shl.com/products/product-catalog/view/dependability-and-safety-instrument-dsi/": "P",
        "https://www.shl.com/products/product-catalog/view/safety-and-dependability-focus-8-0/": "P",
        "https://www.shl.com/products/product-catalog/view/workplace-health-and-safety-new/": "K",
        "https://www.shl.com/products/product-catalog/view/hipaa-security/": "K",
        "https://www.shl.com/products/product-catalog/view/medical-terminology-new/": "K",
        "https://www.shl.com/products/product-catalog/view/microsoft-word-365-essentials-new/": "K,S",
        "https://www.shl.com/products/product-catalog/view/ms-excel-new/": "K",
        "https://www.shl.com/products/product-catalog/view/ms-word-new/": "K",
        "https://www.shl.com/products/product-catalog/view/microsoft-excel-365-new/": "K,S",
        "https://www.shl.com/products/product-catalog/view/microsoft-word-365-new/": "K,S",
        "https://www.shl.com/products/product-catalog/view/core-java-advanced-level-new/": "K",
        "https://www.shl.com/products/product-catalog/view/spring-new/": "K",
        "https://www.shl.com/products/product-catalog/view/restful-web-services-new/": "K",
        "https://www.shl.com/products/product-catalog/view/sql-new/": "K",
        "https://www.shl.com/products/product-catalog/view/amazon-web-services-aws-development-new/": "K",
        "https://www.shl.com/products/product-catalog/view/docker-new/": "K"
    }
    
    # Check trace mapping coverage
    for item in compressed_items:
        url = item["url"].lower()
        # Find exact or lowercase trace match
        matched_type = None
        for t_url, t_type in trace_mapping.items():
            if t_url.lower() == url:
                matched_type = t_type
                break
                
        if matched_type:
            item["test_type"] = matched_type
        else:
            # Generate default test_type
            key_map = {
                "Personality & Behavior": "P",
                "Ability & Aptitude": "A",
                "Biodata & Situational Judgment": "B",
                "Knowledge & Skills": "K",
                "Simulations": "S",
                "Competencies": "C",
                "Development & 360": "D",
                "Assessment Exercises": "E"
            }
            types = []
            for k in item["keys"]:
                if k in key_map:
                    types.append(key_map[k])
            if not types:
                types = ["K"]
            item["test_type"] = ",".join(types)
            
    # Save optimized catalog
    with open("shl_product_catalog_optimized.json", "w", encoding="utf-8") as f:
        json.dump(compressed_items, f, indent=2)
        
    print(f"Optimized catalog saved to shl_product_catalog_optimized.json. Size: {os.path.getsize('shl_product_catalog_optimized.json')/1024:.1f} KB")

if __name__ == '__main__':
    analyze_catalog()

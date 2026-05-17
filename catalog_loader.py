import json
import os

class CatalogLoader:
    def __init__(self, filepath="shl_product_catalog_optimized.json"):
        self.filepath = filepath
        self.catalog = []
        self.by_url = {}
        self.by_name = {}
        self.load()

    def load(self):
        if not os.path.exists(self.filepath):
            # Try loading non-optimized as a backup or raising error
            if os.path.exists("shl_product_catalog.json"):
                # If optimized not created, let's parse raw
                print("Optimized catalog not found, parsing raw catalog...")
                with open("shl_product_catalog.json", "r", encoding="utf-8") as f:
                    raw_data = json.loads(f.read(), strict=False)
                # Apply mapping
                self.catalog = self._optimize_raw(raw_data)
            else:
                raise FileNotFoundError("SHL product catalog JSON file not found in workspace.")
        else:
            with open(self.filepath, "r", encoding="utf-8") as f:
                self.catalog = json.loads(f.read(), strict=False)

        # Build lookup indices
        for item in self.catalog:
            url = item.get("url", "").lower().strip()
            name = item.get("name", "").lower().strip()
            if url:
                self.by_url[url] = item
            if name:
                self.by_name[name] = item

    def _optimize_raw(self, raw_data):
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
        
        optimized = []
        for item in raw_data:
            langs = item.get("languages", [])
            if not langs and item.get("languages_raw"):
                langs = [l.strip() for l in item.get("languages_raw").split(",") if l.strip()]
            duration = item.get("duration", "")
            if not duration and item.get("duration_raw"):
                duration = item.get("duration_raw").strip()
            desc = item.get("description", "").strip().replace("\n", " ").replace("\r", "")
            
            url = item.get("link", "")
            matched_type = None
            for t_url, t_type in trace_mapping.items():
                if t_url.lower() == url.lower():
                    matched_type = t_type
                    break
            
            if not matched_type:
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
                for k in item.get("keys", []):
                    if k in key_map:
                        types.append(key_map[k])
                matched_type = ",".join(types) if types else "K"
                
            optimized.append({
                "id": item.get("entity_id"),
                "name": item.get("name"),
                "url": url,
                "levels": item.get("job_levels", []),
                "langs": langs[:5],
                "dur": duration,
                "desc": desc,
                "keys": item.get("keys", []),
                "test_type": matched_type
            })
        return optimized

    def lookup_by_url(self, url):
        return self.by_url.get(url.lower().strip())

    def lookup_by_name(self, name):
        return self.by_name.get(name.lower().strip())

    def get_prompt_catalog_text(self):
        """Generates a compressed, clean textual listing of all assessments in the catalog."""
        lines = []
        for idx, item in enumerate(self.catalog):
            levels = ",".join(item.get("levels", []))
            keys = ",".join(item.get("keys", []))
            langs = ",".join(item.get("langs", []))
            dur = item.get("dur", "")
            lines.append(
                f"Assessment #{idx+1}:\n"
                f"- Name: {item['name']}\n"
                f"- URL: {item['url']}\n"
                f"- Test Type: {item['test_type']}\n"
                f"- Keys: {keys}\n"
                f"- Levels: {levels}\n"
                f"- Duration: {dur}\n"
                f"- Description: {item['desc']}\n"
            )
        return "\n".join(lines)

# Singleton catalog loader instance
catalog_loader = CatalogLoader()

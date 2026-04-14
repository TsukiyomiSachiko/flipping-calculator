import requests
import re
import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class WikiScraper:
    def __init__(self):
        self.api_url = "https://oldschool.runescape.wiki/api.php"
        self.headers = {
            'User-Agent': 'OSRS-Flipping-Calculator - Item Conversion Scraper'
        }
        self._item_mapping = None

    def get_item_mapping(self) -> Dict[str, int]:
        """Fetch item mapping to resolve names to IDs."""
        if self._item_mapping is None:
            url = "https://prices.runescape.wiki/api/v1/osrs/mapping"
            try:
                response = requests.get(url, headers=self.headers, timeout=10)
                if response.status_code == 200:
                    # Map name -> id (lowercase for easier matching)
                    self._item_mapping = {item['name'].lower(): item['id'] for item in response.json()}
                else:
                    logger.error(f"Failed to fetch item mapping: {response.status_code}")
                    return {}
            except Exception as e:
                logger.error(f"Error fetching item mapping: {e}")
                return {}
        return self._item_mapping

    def fetch_wikitext(self, title: str) -> Optional[str]:
        """Fetch raw wikitext for a given page title."""
        params = {
            "action": "query",
            "prop": "revisions",
            "titles": title,
            "rvprop": "content",
            "format": "json",
            "redirects": 1
        }
        try:
            response = requests.get(self.api_url, params=params, headers=self.headers, timeout=10)
            if response.status_code != 200:
                return None
            
            data = response.json()
            pages = data.get("query", {}).get("pages", {})
            for page_id, page_data in pages.items():
                if page_id == "-1":
                    return None
                return page_data["revisions"][0]["*"]
        except Exception as e:
            logger.error(f"Error fetching wikitext for {title}: {e}")
            return None
        return None

    def get_category_members(self, category_name: str) -> List[str]:
        """Fetch all page titles in a category."""
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": f"Category:{category_name}",
            "cmlimit": 500,
            "format": "json"
        }
        try:
            response = requests.get(self.api_url, params=params, headers=self.headers, timeout=10)
            if response.status_code != 200:
                return []
            
            data = response.json()
            members = data.get("query", {}).get("categorymembers", [])
            return [m["title"] for m in members]
        except Exception as e:
            logger.error(f"Error fetching category members for {category_name}: {e}")
            return []

    def _parse_quantity(self, qty_str: str) -> float:
        """Parse quantity string which might be a number or expression."""
        if not qty_str:
            return 1.0
        
        # 1. Handle {{#expr: ... }} explicitly with brace counting
        if "{{#expr:" in qty_str:
            start_idx = qty_str.find("{{#expr:")
            content_start = start_idx + 8
            brace_count = 1
            i = content_start
            
            while i < len(qty_str) and brace_count > 0:
                if qty_str[i:i+2] == "{{":
                    brace_count += 1
                    i += 2
                elif qty_str[i:i+2] == "}}":
                    brace_count -= 1
                    i += 2
                else:
                    i += 1
            
            if brace_count == 0:
                # Found the closing brace
                qty_str = qty_str[content_start:i-2]

        # 2. Basic cleanup: remove wiki templates, links, and HTML-like tags
        # Repeatedly remove {{...}} to handle nesting
        while "{{" in qty_str:
            prev = qty_str
            qty_str = re.sub(r"{{[^}]*}}", "", qty_str)
            if qty_str == prev:
                # Avoid infinite loop if malformed
                break
                
        qty_str = re.sub(r"<!--.*?-->", "", qty_str, flags=re.DOTALL)
        qty_str = re.sub(r"<[^>]+>", "", qty_str)
        qty_str = re.sub(r"\[\[|\]\]", "", qty_str)
        
        # 3. Extract the math part: numbers and basic operators
        math_match = re.search(r"([0-9\.\+\-\*\/\(\)\s]+)", qty_str)
        if not math_match:
            # Fallback: just extract the first number, but ONLY if it looks like a simple number
            # If the string was complex enough to fail regex, be careful.
            match = re.search(r"^(\d+(\.\d+)?)", qty_str.strip())
            return float(match.group(1)) if match else 0.0
            
        clean_expr = math_match.group(1).strip()
        # Remove all whitespace for eval
        eval_expr = re.sub(r"\s+", "", clean_expr)
        
        if not eval_expr:
            return 0.0
            
        try:
            # Only allow numbers and basic operators
            if re.search(r"[^0-9\.\+\-\*\/\(\)]", eval_expr):
                raise ValueError("Unsafe characters in expression")
                
            # Use a limited scope for eval
            return float(eval(eval_expr, {"__builtins__": None}, {}))
        except Exception as e:
            # If eval fails, do NOT fallback to extracting the first number
            # This avoids cases like "(29/35)*17/" -> 29
            return 0.0

    def parse_mmg_table(self, wikitext: str) -> Optional[Dict]:
        """Parse Mmgtable template from wikitext."""
        # Find {{Mmgtable (case insensitive, allowing variants like Mmgtable recurring)
        match = re.search(r"{{Mmgtable", wikitext, re.IGNORECASE)
        if not match:
            return None
        
        start_index = match.start()
        
        # Simple brace counting to find the end of the template
        brace_count = 0
        end_index = -1
        i = start_index
        while i < len(wikitext) - 1:
            if wikitext[i:i+2] == "{{":
                brace_count += 1
                i += 2
            elif wikitext[i:i+2] == "}}":
                brace_count -= 1
                i += 2
                if brace_count == 0:
                    end_index = i
                    break
            else:
                i += 1
        
        if end_index == -1:
            return None
        
        content = wikitext[start_index:end_index]
        
        # Parse parameters. We look for | key = value
        # We split by | but only if it's not inside [[ ]] or {{ }}
        params = {}
        current_key = None
        current_value = []
        
        # Find the first | to skip the template name
        first_pipe = wikitext.find("|", start_index, end_index)
        if first_pipe == -1:
            return None
            
        params = {}
        current_key = None
        current_value = []
        
        # Start from the first pipe
        i = first_pipe
        brace_level = 0
        bracket_level = 0
        
        while i < end_index - 2:
            char = wikitext[i]
            
            # Look for new parameter start at pipe if we're not inside nested structures
            if char == "|" and brace_level == 0 and bracket_level == 0:
                # Save previous param if any
                if current_key:
                    params[current_key.strip().lower()] = "".join(current_value).strip()
                
                # Try to find the next key (between | and =)
                next_eq = wikitext.find("=", i + 1, end_index)
                next_pipe = wikitext.find("|", i + 1, end_index)
                
                if next_eq != -1 and (next_pipe == -1 or next_eq < next_pipe):
                    current_key = wikitext[i+1:next_eq]
                    current_value = []
                    i = next_eq + 1
                    continue
                else:
                    # Positional parameter or just a pipe - skip it
                    current_key = None
                    i += 1
                    continue

            # Standard char processing
            if wikitext[i:i+2] == "{{":
                brace_level += 1
                current_value.append("{{")
                i += 2
            elif wikitext[i:i+2] == "}}":
                brace_level -= 1
                current_value.append("}}")
                i += 2
            elif wikitext[i:i+2] == "[[":
                bracket_level += 1
                current_value.append("[[")
                i += 2
            elif wikitext[i:i+2] == "]]":
                bracket_level -= 1
                current_value.append("]]")
                i += 2
            else:
                if current_key:
                    current_value.append(char)
                i += 1
        
        # Save last param
        if current_key:
            params[current_key.strip().lower()] = "".join(current_value).strip()

        # logger.info(f"Parsed params for {params.get('activity')}: {list(params.keys())}")

        # Extract skill and level before cleaning templates
        raw_skill = params.get('skill', '')
        skill_name = None
        level_req = 1
        
        # 1. Handle {{SCP|Skill|Level}}
        scp_match = re.search(r"{{SCP\|([^|}]*)\|(\d+)}}", raw_skill, re.IGNORECASE)
        if scp_match:
            skill_name = scp_match.group(1)
            level_req = int(scp_match.group(2))
        else:
            # 2. Check for explicit level param
            if 'level' in params:
                try:
                    level_req = int(re.sub(r"[^0-9]", "", params['level']))
                except:
                    pass
            
            # 3. Try to extract from raw_skill after a simple clean
            temp_skill = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", raw_skill)
            # Find level in (55) or just 55
            level_match = re.search(r"(\d+)", temp_skill)
            if level_match and level_req == 1:
                level_req = int(level_match.group(1))
            
            # Find skill name (first word that isn't a number)
            skill_match = re.search(r"([a-zA-Z]+)", temp_skill)
            if skill_match:
                skill_name = skill_match.group(1)

        # Clean up values
        def clean_value(val: str) -> str:
            val = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", val) # Remove wiki links
            val = re.sub(r"{{[^}]*}}", "", val) # Remove other templates
            return val.strip()

        mapping = self.get_item_mapping()
        
        result = {
            "name": clean_value(params.get("activity", "")),
            "wiki_name": None, # Will be set by caller
            "kph": params.get("kph"),
            "skill_required": skill_name,
            "level_required": level_req,
            "members": params.get("members", "Yes").lower() == "yes",
            "category": params.get("category", "Processing"),
            "inputs": [],
            "outputs": []
        }

        if not result["name"]:
            return None

        # Parse kph properly
        kph_raw = str(result["kph"])
        # If kph is like "720", or "2400 bows/hr", extract the number
        kph_match = re.search(r"(\d+(\.\d+)?)", kph_raw)
        if kph_match:
            result["kph"] = float(kph_match.group(1))
        else:
            result["kph"] = 0.0
        def parse_items(prefix: str):
            items = []
            # Check for single 'Input' or 'Output'
            single_name = params.get(prefix.lower())
            if single_name:
                item_data = self._resolve_item(single_name, params.get(f"{prefix.lower()}num", "1"))
                if item_data:
                    items.append(item_data)
            
            # Check for numbered ones
            for i in range(1, 11):
                item_name = params.get(f"{prefix.lower()}{i}")
                if not item_name:
                    continue
                
                item_data = self._resolve_item(item_name, params.get(f"{prefix.lower()}{i}num", "1"))
                if item_data:
                    items.append(item_data)
            return items

        result["inputs"] = parse_items("Input")
        result["outputs"] = parse_items("Output")

        if not result["outputs"]:
            logger.warning(f"Skipping {result['name']}: no outputs found")
            return None

        return result

    def _resolve_item(self, raw_name: str, raw_qty: str) -> Optional[Dict]:
        """Helper to resolve item name and quantity."""
        # 1. Handle complex templates like {{MaxPrice|...}} or {{#switch:...}}
        if "{{" in raw_name:
            # Try to find the first likely item name in the template
            # For {{MaxPrice|...|Diamond ring|...}}, we want "Diamond ring"
            # We look for strings between | and | or | and }
            inner_matches = re.findall(r"\|([^|=\[\]{}#]+)", raw_name)
            mapping = self.get_item_mapping()
            for candidate in inner_matches:
                candidate = candidate.strip()
                if not candidate or candidate.lower() in ["item", "format", "link", "n", "y", "var"]:
                    continue
                res = self._resolve_item(candidate, raw_qty)
                if res: return res

        # 2. Clean up: remove links, templates, and extra whitespace
        clean_name = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", raw_name)
        clean_name = re.sub(r"{{[^}]*}}", "", clean_name).strip()
        
        mapping = self.get_item_mapping()
        
        def try_match(name: str) -> Optional[int]:
            name = name.lower().strip()
            # Try exact
            if name in mapping: return mapping[name]
            # Try without 's
            name_no_s = name.replace("'s", "").replace("s'", "")
            if name_no_s in mapping: return mapping[name_no_s]
            # Try without trailing s (plural)
            if name.endswith("s") and name[:-1] in mapping: return mapping[name[:-1]]
            # Try adding s
            if name + "s" in mapping: return mapping[name + "s"]
            return None

        # 2. Try various normalizations
        item_id = try_match(clean_name)
        
        # 3. Try removing parenthetical notes
        if not item_id and "(" in clean_name:
            base_name = re.sub(r"\s*\(.*?\)", "", clean_name).strip()
            item_id = try_match(base_name)
            if item_id:
                clean_name = base_name

        # 4. Try the "split by pipe" method for raw name
        if not item_id:
            clean_name_alt = re.sub(r"\[\[|\]\]", "", raw_name).split("|")[-1].strip()
            item_id = try_match(clean_name_alt)
            if not item_id and "(" in clean_name_alt:
                base_name_alt = re.sub(r"\s*\(.*?\)", "", clean_name_alt).strip()
                item_id = try_match(base_name_alt)
                if item_id:
                    clean_name = base_name_alt
            elif item_id:
                clean_name = clean_name_alt

        # 5. Special case for Coins
        if not item_id and "coins" in raw_name.lower():
            item_id = -100
            clean_name = "Coins"

        if item_id:
            qty = self._parse_quantity(raw_qty)
            return {"id": item_id, "name": clean_name, "quantity": qty}
        return None

    def scrape_processing_methods(self) -> List[Dict]:
        """Scrape all processing methods from OSRS Wiki."""
        categories = ["MMG/Processing", "MMG/Skilling"]
        all_titles = []
        for cat in categories:
            all_titles.extend(self.get_category_members(cat))
        
        # Deduplicate titles
        titles = sorted(list(set(all_titles)))
        
        methods = []
        for title in titles:
            # Skip only internal/meta pages
            if ":" in title and not title.startswith("Money making guide/"):
                continue
            if title.lower() == "money making guide/processing" or title.lower() == "money making guide/skilling":
                continue
            if "sandbox" in title.lower():
                continue
            
            # Exclude specific methods known to have issues (e.g., untradeable inputs not handled)
            if title.replace("Money making guide/", "") in [
                "Crafting sunfire runes",
                "Crafting aether runes using scarred extract"
            ]:
                continue
            
            logger.info(f"Scraping {title}...")
            wikitext = self.fetch_wikitext(title)
            if wikitext:
                method = self.parse_mmg_table(wikitext)
                if method:
                    method["wiki_name"] = title.replace("Money making guide/", "")
                    method["wiki_url"] = f"https://oldschool.runescape.wiki/w/{title.replace(' ', '_')}"
                    methods.append(method)
        
        return methods

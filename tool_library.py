import json
import random
from datetime import datetime
from typing import Dict, List, Any

class ToolLibrary:
    """
    Production-ready tool library for AI agents
    
    Each tool:
    1. Has a clear purpose
    2. Returns structured data
    3. Handles errors gracefully
    4. Is documented for both humans and AI
    """
    
    def __init__(self):
        """Initialize tool library with mock data"""
        
        # Mock ServiceNow data (UPDATED: More realistic revenue)
        self.servicenow_data = {
            "features": {
                "personalization_engine": {
                    "status": "production",
                    "adoption_rate": 0.65,
                    "users": 12500,
                    "incidents": 23
                },
                "ai_search": {
                    "status": "beta",
                    "adoption_rate": 0.32,
                    "users": 4200,
                    "incidents": 8
                }
            },
            "metrics": {
                "conversion_rate": 0.032,
                "revenue": 5000000,  # CHANGED: $5M (was $50M) - more realistic for mid-market
                "platform_uptime": 0.997
            }
        }
    
    # =====================================================
    # TOOL 1: CALCULATOR
    # =====================================================
    
    def calculate(self, expression: str) -> Dict[str, Any]:
        """
        Evaluate mathematical expressions safely
        
        Args:
            expression: Math expression (e.g., "15 * 2.3 + 100")
            
        Returns:
            Dict with result and metadata
        """
        try:
            # Safe eval - only allow math operations
            allowed_chars = set("0123456789+-*/().% ")
            if not all(c in allowed_chars for c in expression):
                return {
                    "success": False,
                    "error": "Invalid characters in expression",
                    "expression": expression
                }
            
            # Evaluate
            result = eval(expression)
            
            return {
                "success": True,
                "result": result,
                "expression": expression,
                "formatted": f"{result:,.2f}" if isinstance(result, (int, float)) else str(result)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "expression": expression
            }
    
    def get_calculate_schema(self) -> Dict:
        """Return tool schema for calculate"""
        return {
            "name": "calculate",
            "description": "Evaluate mathematical expressions. Use for any calculation including percentages, ROI, conversions, etc.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression to evaluate (e.g., '0.15 * 2300000' or '(100 + 50) / 2')"
                    }
                },
                "required": ["expression"]
            }
        }
    
    # =====================================================
    # TOOL 2: SERVICENOW LOOKUP
    # =====================================================
    
    def servicenow_lookup(self, entity_type: str, entity_id: str = None) -> Dict[str, Any]:
        """
        Look up ServiceNow data (mock implementation)
        
        Args:
            entity_type: Type of entity ("feature", "metric", "user")
            entity_id: Specific entity ID (optional)
            
        Returns:
            Dict with entity data
        """
        try:
            if entity_type == "feature":
                if entity_id:
                    data = self.servicenow_data["features"].get(entity_id)
                    if not data:
                        return {
                            "success": False,
                            "error": f"Feature '{entity_id}' not found"
                        }
                    return {
                        "success": True,
                        "entity_type": "feature",
                        "entity_id": entity_id,
                        "data": data
                    }
                else:
                    return {
                        "success": True,
                        "entity_type": "feature",
                        "data": self.servicenow_data["features"]
                    }
            
            elif entity_type == "metric":
                if entity_id:
                    value = self.servicenow_data["metrics"].get(entity_id)
                    if value is None:
                        return {
                            "success": False,
                            "error": f"Metric '{entity_id}' not found"
                        }
                    return {
                        "success": True,
                        "entity_type": "metric",
                        "entity_id": entity_id,
                        "value": value
                    }
                else:
                    return {
                        "success": True,
                        "entity_type": "metric",
                        "data": self.servicenow_data["metrics"]
                    }
            
            else:
                return {
                    "success": False,
                    "error": f"Unknown entity type: {entity_type}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_servicenow_lookup_schema(self) -> Dict:
        """Return tool schema for servicenow_lookup"""
        return {
            "name": "servicenow_lookup",
            "description": "Look up ServiceNow platform data including features, metrics, and user information. Use this to get current data about the ServiceNow platform.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "entity_type": {
                        "type": "string",
                        "enum": ["feature", "metric", "user"],
                        "description": "Type of entity to look up"
                    },
                    "entity_id": {
                        "type": "string",
                        "description": "Specific entity ID (optional - omit to get all entities of this type)"
                    }
                },
                "required": ["entity_type"]
            }
        }
    
    # =====================================================
    # TOOL 3: WEB SEARCH (MOCK)
    # =====================================================
    
    def web_search(self, query: str, num_results: int = 3) -> Dict[str, Any]:
        """
        Mock web search for industry benchmarks and external data
        
        Args:
            query: Search query
            num_results: Number of results to return (1-5)
            
        Returns:
            Dict with search results
        """
        # Mock search results based on common queries
        mock_results = {
            "personalization conversion": [
                {
                    "title": "Industry Benchmark: E-commerce Personalization",
                    "url": "https://example.com/personalization-benchmarks",
                    "snippet": "Average conversion rate lift from personalization: 1.5-2.0%. Top performers see 3-5% lift."
                },
                {
                    "title": "2024 Personalization ROI Study",
                    "url": "https://example.com/roi-study",
                    "snippet": "Enterprises implementing AI personalization report average revenue increase of $2-4M annually."
                }
            ],
            "enterprise ai adoption": [
                {
                    "title": "Enterprise AI Adoption Rates 2024",
                    "url": "https://example.com/ai-adoption",
                    "snippet": "65% of enterprises have deployed AI in at least one function. Adoption rate growing 15% YoY."
                }
            ],
            "servicenow competitors": [
                {
                    "title": "ServiceNow Competitive Analysis",
                    "url": "https://example.com/competitors",
                    "snippet": "Main competitors: Salesforce (CRM), Adobe (Experience), Microsoft (Power Platform). ServiceNow leads in IT workflow automation."
                }
            ]
        }
        
        # Find best matching results
        query_lower = query.lower()
        results = []
        
        for key, search_results in mock_results.items():
            if any(word in query_lower for word in key.split()):
                results.extend(search_results[:num_results])
        
        if not results:
            # Generic fallback
            results = [{
                "title": f"Search results for: {query}",
                "url": "https://example.com/search",
                "snippet": f"Mock search result for '{query}'. In production, this would query a real search API."
            }]
        
        return {
            "success": True,
            "query": query,
            "results": results[:num_results],
            "num_results": len(results[:num_results])
        }
    
    def get_web_search_schema(self) -> Dict:
        """Return tool schema for web_search"""
        return {
            "name": "web_search",
            "description": "Search the web for industry benchmarks, competitor information, and external data. Use when you need current information not available in ServiceNow data.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (e.g., 'enterprise AI adoption rates 2024')"
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "Number of results to return (1-5)",
                        "default": 3
                    }
                },
                "required": ["query"]
            }
        }
    
    # =====================================================
    # TOOL REGISTRY
    # =====================================================
    
    def get_all_tools(self) -> List[Dict]:
        """Return list of all tool schemas for Claude API"""
        return [
            self.get_calculate_schema(),
            self.get_servicenow_lookup_schema(),
            self.get_web_search_schema()
        ]
    
    def execute_tool(self, tool_name: str, tool_input: Dict) -> Dict:
        """
        Execute a tool by name
        
        Args:
            tool_name: Name of tool to execute
            tool_input: Input parameters as dict
            
        Returns:
            Tool execution result
        """
        if tool_name == "calculate":
            return self.calculate(**tool_input)
        
        elif tool_name == "servicenow_lookup":
            return self.servicenow_lookup(**tool_input)
        
        elif tool_name == "web_search":
            return self.web_search(**tool_input)
        
        else:
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}"
            }
    
    def format_tool_result(self, result: Dict) -> str:
        """
        Format tool result for display to Claude
        
        Args:
            result: Tool execution result
            
        Returns:
            Formatted string
        """
        if not result.get("success", False):
            return f"Error: {result.get('error', 'Unknown error')}"
        
        # Pretty print the result
        return json.dumps(result, indent=2)


# DEMO: Test the tools
def demo_tools():
    """Demo the tool library"""
    
    print("\n" + "🔧 " * 20)
    print("TOOL LIBRARY DEMO")
    print("🔧 " * 20)
    
    tools = ToolLibrary()
    
    # Test 1: Calculator
    print("\n" + "="*70)
    print("TEST 1: Calculator")
    print("="*70)
    
    calc_result = tools.calculate("0.15 * 2300000")
    print(f"Expression: 0.15 * 2300000")
    print(f"Result: {json.dumps(calc_result, indent=2)}")
    
    # Test 2: ServiceNow Lookup
    print("\n" + "="*70)
    print("TEST 2: ServiceNow Lookup")
    print("="*70)
    
    lookup_result = tools.servicenow_lookup("metric", "conversion_rate")
    print(f"Lookup: metric/conversion_rate")
    print(f"Result: {json.dumps(lookup_result, indent=2)}")
    
    # Show updated revenue
    revenue_result = tools.servicenow_lookup("metric", "revenue")
    print(f"\nLookup: metric/revenue")
    print(f"Result: {json.dumps(revenue_result, indent=2)}")
    print(f"\n💡 Note: Revenue is now $5M (more realistic for mid-market)")
    
    # Test 3: Web Search
    print("\n" + "="*70)
    print("TEST 3: Web Search")
    print("="*70)
    
    search_result = tools.web_search("personalization conversion benchmarks")
    print(f"Query: personalization conversion benchmarks")
    print(f"Result: {json.dumps(search_result, indent=2)}")
    
    # Test 4: Tool Registry
    print("\n" + "="*70)
    print("TEST 4: Tool Registry")
    print("="*70)
    
    all_tools = tools.get_all_tools()
    print(f"Available tools: {len(all_tools)}")
    for tool in all_tools:
        print(f"  - {tool['name']}: {tool['description'][:60]}...")
    
    print("\n✅ Tool library ready!")


if __name__ == "__main__":
    demo_tools()